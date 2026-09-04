"""Check V2 against the imported official closed Robotiq reference."""

import json
from pathlib import Path
import adsk.core
import adsk.fusion

OUTPUT = Path(__file__).resolve().parents[1] / "artifacts" / "review_v2_20260904"


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    refs = [o for o in root.occurrences if o.component.name == "REFERENCE Robotiq closed mechanism"]
    if len(refs) != 1:
        raise RuntimeError("Import exactly one official closed Robotiq reference first")
    # Verified from the imported STEP: these four removable fingertip/pad
    # bodies span Y=124.82..162.82 and are replaced by the new finger assembly.
    excluded = {"Body6", "Body7", "Body10", "Body11"}
    stock = []
    for b in refs[0].bRepBodies:
        if b.name in excluded:
            if abs(b.boundingBox.minPoint.y*10-124.82) > 0.02 or abs(b.boundingBox.maxPoint.y*10-162.82) > 0.02:
                raise RuntimeError("Reference body identities changed; inspect before excluding")
            b.isVisible = False
        else:
            stock.append(b)
    if len(stock) != 11:
        raise RuntimeError(f"Unexpected reference body count: {len(stock)}")
    new_bodies = []
    for occ in root.allOccurrences:
        if "V2 handed finger" in occ.fullPathName:
            new_bodies.extend(list(occ.bRepBodies))
    collection = adsk.core.ObjectCollection.create()
    for b in new_bodies + stock:
        collection.add(b)
    inp = design.createInterferenceInput(collection)
    inp.areCoincidentFacesIncluded = False
    results = design.analyzeInterference(inp)
    if results is None:
        raise RuntimeError("Fusion interference analysis failed")
    collisions = []
    for result in results:
        one, two = result.entityOne, result.entityTwo
        if one.name.startswith("Body") and two.name.startswith("Body"):
            continue
        bounds = result.interferenceBody.boundingBox
        collisions.append({"one": one.name, "two": two.name,
                           "volume_mm3": round(result.interferenceBody.volume*1000, 6),
                           "min_mm": [round(v*10, 4) for v in bounds.minPoint.asArray()],
                           "max_mm": [round(v*10, 4) for v in bounds.maxPoint.asArray()]})
    hardware = [b for b in new_bodies if b.name.startswith(("M3x30", "M3 washer", "M3 nut"))]
    distances = []
    for body in hardware:
        nearest = min((app.measureManager.measureMinimumDistance(body, other).value*10, other.name)
                      for other in stock)
        distances.append({"hardware": body.name, "nearest_stock_body": nearest[1],
                          "clearance_mm": round(nearest[0], 4)})
    report = {"configuration": "official closed STEP", "excluded_stock_fingertips": sorted(excluded),
              "new_part_interferences": collisions, "hardware_clearances": distances,
              "minimum_hardware_to_robotiq_clearance_mm": min(d["clearance_mm"] for d in distances)}
    (OUTPUT / "robotiq_fitcheck.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    for collision in collisions:
        names = {collision["one"], collision["two"]}
        expected_pair = names in ({"PETG Adapter LEFT", "Body2"}, {"PETG Adapter RIGHT", "Body1"})
        at_mount = collision["min_mm"][1] >= 124.819 and collision["max_mm"][1] <= 128.821
        if not (expected_pair and at_mount and abs(collision["volume_mm3"]-0.03682) < 0.0001):
            raise RuntimeError("New interference beyond the previously recorded OEM mounting contact")
    manager = design.exportManager
    manager.execute(manager.createFusionArchiveExportOptions(str(OUTPUT / "REVIEW_V2_Robotiq_FITCHECK.f3d"), root))
    app.activeViewport.fit()
    app.activeViewport.refresh()
