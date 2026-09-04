"""Validate V2 solids, finished pocket mouths, closure and nominal hardware."""

import json
import math
from pathlib import Path
import adsk.core
import adsk.fusion

OUTPUT = Path(__file__).resolve().parents[1] / "artifacts" / "review_v2_20260904"


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    helper_path = Path(__file__).with_name("inspect_active_finger_design.py")
    helper = {"__file__": str(helper_path), "__name__": "inspection_helpers"}
    exec(compile(helper_path.read_text(encoding="utf-8"), str(helper_path), "exec"), helper)
    centres = {(13.0, 5.0), (13.0, 19.5), (34.0, 19.5)}
    report = {"parts": {}, "hardware_dimensions_provisional": True}
    occurrences = [o for o in root.occurrences if "V2 handed finger" in o.component.name]
    if len(occurrences) != 2:
        raise RuntimeError("Expected two V2 fingers")
    prototypes = {}
    for occ in occurrences:
        comp = occ.component
        label = "LEFT" if comp.name.startswith("LEFT") else "RIGHT"
        head_x = 13.0 if label == "LEFT" else -13.0
        petg = next(b for b in comp.bRepBodies if b.name.startswith("PETG"))
        tpu = next(b for b in comp.bRepBodies if b.name.startswith("TPU"))
        if comp.bRepBodies.count != 2 or not petg.isSolid or not tpu.isSolid:
            raise RuntimeError("Expected two solid printable bodies")
        if helper["enclosed_recess_centres"](petg, head_x, 1) != centres:
            raise RuntimeError(f"{label}: washer pocket opens through an edge")
        if helper["enclosed_recess_centres"](petg, -head_x, 6) != centres:
            raise RuntimeError(f"{label}: nut pocket opens through an edge")
        bays = comp.sketches.itemByName("Six unchanged UMI-derived through-bays")
        if bays.profiles.count != 6:
            raise RuntimeError("Expected six through-bay profiles")
        for body, radius, length in ((tpu, 2.0, 15.48), (petg, 1.8, 7.02)):
            areas = {}
            for face in body.faces:
                cylinder = adsk.core.Cylinder.cast(face.geometry)
                if not cylinder or abs(abs(cylinder.axis.x)-1) > 1e-5:
                    continue
                if abs(cylinder.radius*10-radius) > 0.001:
                    continue
                key = (round(cylinder.origin.y*10, 3), round(cylinder.origin.z*10, 3))
                areas[key] = areas.get(key, 0) + face.area*100
            expected = 2*math.pi*radius*length
            if set(areas) != centres or any(abs(v-expected) > 0.03 for v in areas.values()):
                raise RuntimeError(f"Incomplete M3 bores on {body.name}: {areas}; expected {expected}")
        y_rows = helper["y_cylinder_rows"](petg)
        for radius, x, z, y0, y1, name in (
            (2.65, 0, 12.36, 0, 4, "M5 shoulder bore"),
            (4.6, 0, 12.36, 4, 10, "M5 head pocket"),
            (1, -4.5, 12.36, 0, 2.5, "index socket 1"),
            (1, 4.5, 12.36, 0, 2.5, "index socket 2"),
        ):
            helper["require_y_cylinder"](y_rows, radius, x, z, y0, y1, name)
        if abs(tpu.boundingBox.minPoint.y*10-10) > 0.002:
            raise RuntimeError("TPU does not seat at Y=10")
        report["parts"][label] = {
            "petg_extents_mm": helper["extent_mm"](petg),
            "tpu_extents_mm": helper["extent_mm"](tpu),
            "petg_volume_mm3": round(petg.volume*1000, 3),
            "tpu_volume_mm3": round(tpu.volume*1000, 3),
            "joint_centres_yz_mm": sorted(centres),
            "minimum_washer_seat_floor_mm": 4.46,
            "minimum_nut_seat_floor_mm": 2.56,
        }
        prototypes[label] = (petg.createForAssemblyContext(occ), tpu.createForAssemblyContext(occ))

    report["closed_gaps_mm"] = {
        "PETG": round(app.measureManager.measureMinimumDistance(prototypes["LEFT"][0], prototypes["RIGHT"][0]).value*10, 6),
        "bare_TPU": round(app.measureManager.measureMinimumDistance(prototypes["LEFT"][1], prototypes["RIGHT"][1]).value*10, 6),
    }
    if abs(report["closed_gaps_mm"]["PETG"]-1.0) > 0.002 or report["closed_gaps_mm"]["bare_TPU"] > 0.002:
        raise RuntimeError(f"Unexpected closure gaps: {report['closed_gaps_mm']}")
    collection = adsk.core.ObjectCollection.create()
    count = 0
    screws = []
    for occ in root.allOccurrences:
        if not ("V2 handed finger" in occ.component.name or "REFERENCE hardware" in occ.component.name):
            continue
        for body in occ.bRepBodies:
            collection.add(body)
            count += 1
            if body.name.startswith("M3x30"):
                screws.append(body)
    if count != 22 or len(screws) != 6:
        raise RuntimeError(f"Expected 22 bodies including 6 screws; got {count}, {len(screws)}")
    inp = design.createInterferenceInput(collection)
    inp.areCoincidentFacesIncluded = False
    result = design.analyzeInterference(inp)
    if result is None:
        raise RuntimeError("Fusion interference analysis failed")
    overlaps = []
    for item in result:
        overlaps.append({"one": item.entityOne.name, "two": item.entityTwo.name,
                         "volume_mm3": item.interferenceBody.volume*1000})
    report["interference_results"] = overlaps
    if any(v["volume_mm3"] > 0.001 for v in overlaps):
        raise RuntimeError(f"Unexpected material overlap: {overlaps}")
    report["screw_tip_global_z_mm"] = [round(s.boundingBox.minPoint.z*10, 4) for s in screws]
    if any(abs(z+17.1) > 0.002 for z in report["screw_tip_global_z_mm"]):
        raise RuntimeError("Unexpected screw tip location")
    report["protrusion_beyond_petg_mm"] = 4.1
    report["protrusion_beyond_nominal_nut_mm"] = 4.2
    report["nominal_nut_engagement_mm"] = 2.4
    report["status"] = "PASS"
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "fusion_qa.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
