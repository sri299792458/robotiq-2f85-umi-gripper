"""Build the V2 review: zero bare-TPU gap, reinforced cheeks, uncut M3x30 hardware.

The accepted six-bay flexure is translated intact. Only the contact-side root
hole is relocated, so V2 requires new TPU prints. Hardware uses provisional
M3 flat washers (7 x 0.5 mm) and nominal thread-free fastener envelopes.
No production artifact is overwritten.
"""

import json
import math
import os
from pathlib import Path


WORKSPACE = Path(__file__).resolve().parents[1]
BASE_SCRIPT = str(WORKSPACE / "scripts" / "build_skild_inspired_fingers.py")
PROFILE_JSON = str(WORKSPACE / "artifacts" / "review_v2_20260904" / "source_profile.json")
OUTPUT_DIR = str(WORKSPACE / "artifacts" / "review_v2_20260904")
EXPORT_MODE = "review"



def run(_context: str):
    with open(PROFILE_JSON, "r", encoding="utf-8") as stream:
        profile = json.load(stream)

    namespace = {"__file__": BASE_SCRIPT, "__name__": "handed_zero_gap_base"}
    with open(BASE_SCRIPT, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), BASE_SCRIPT, "exec"), namespace)

    namespace["OUTPUT_DIR"] = OUTPUT_DIR
    adsk = namespace["adsk"]
    yz_point = namespace["yz_point"]
    xz_point = namespace["xz_point"]
    add_polygon = namespace["add_polygon"]
    largest_profile = namespace["largest_profile"]
    profiles_collection = namespace["profiles_collection"]
    symmetric_extrude = namespace["symmetric_extrude"]
    one_side_extrude = namespace["one_side_extrude"]
    positive_y_direction = namespace["positive_y_direction"]
    y_offset_plane = namespace["y_offset_plane"]
    apply_appearances = namespace["apply_appearances"]
    export_stl = namespace["export_stl"]
    save_flat_preview = namespace["save_flat_preview"]
    robotiq_closed_transform = namespace["robotiq_closed_transform"]
    add_parameter = namespace["add_parameter"]

    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    design.designType = adsk.fusion.DesignTypes.ParametricDesignType
    root = design.rootComponent

    add_parameter(design, "adapterOverallWidth", "26 mm", "mm", "V2 thicker PETG cheeks")
    add_parameter(design, "adapterSlotWidth", "15.88 mm", "mm", "15.48 mm TPU plus 0.20 mm clearance per side")
    add_parameter(design, "tpuFingerThickness", "15.48 mm", "mm", "Exact 0.600 scale of the UMI 25.8 mm thickness")
    add_parameter(design, "adapterM3Clearance", "3.6 mm", "mm", "UMI holder M3 clearance")
    add_parameter(design, "tpuM3Clearance", "4.0 mm", "mm", "UMI soft-finger M3 clearance")
    add_parameter(design, "closedClearancePerSide", "0 mm", "mm", "Bare TPU rails meet at mechanical closure")
    add_parameter(design, "m5ShoulderDepth", "4 mm", "mm", "Unchanged OEM fingertip shoulder")
    add_parameter(design, "m5HeadToolPocketDepth", "6 mm", "mm", "Reduced from 10 mm for the measured 4.9 mm M5 head")
    add_parameter(design, "adapterRootDepth", "10 mm", "mm", "Unchanged 4 mm shoulder plus 6 mm M5 head pocket")
    add_parameter(design, "tpuRootShift", "-4 mm", "mm", "Move TPU base from Y=14 mm to the Y=10 mm PETG split")
    add_parameter(design, "adapterDistalExtent", "40.5 mm", "mm", "Trimmed inward from 42.9 mm at the user's marked PETG edge")

    add_parameter(design, "washerSeatDiameter", "7.5 mm", "mm", "Provisional 7 mm washer plus radial clearance")
    add_parameter(design, "washerSeatDepth", "0.6 mm", "mm", "Shallow seat for provisional 0.5 mm washer")
    add_parameter(design, "washerThickness", "0.5 mm", "mm", "VIGRUE kit dimension not yet measured")
    add_parameter(design, "jointScrewLength", "30 mm", "mm", "Use full-length screws without cutting")
    add_parameter(design, "petgClosingClearancePerSide", "0.5 mm", "mm", "Rigid holders clear each other at TPU contact")

    silhouette_offset_y = -4.0
    silhouette_offset_z = -0.75
    # The contact-side root hole moves away from the gripping edge. The other
    # two axes retain their relation to the translated UMI flexure.
    joint_centres = [(13.0, 5.0), (13.0, 19.5), (34.0, 19.5)]

    def installed_point(point):
        return (
            float(point[0]) + silhouette_offset_y,
            float(point[1]) + silhouette_offset_z,
        )

    def add_xy_polygon(sketch, points):
        lines = sketch.sketchCurves.sketchLines
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            lines.addByTwoPoints(
                adsk.core.Point3D.create(start[0] / 10.0, start[1] / 10.0, 0.0),
                adsk.core.Point3D.create(end[0] / 10.0, end[1] / 10.0, 0.0),
            )

    def x_offset_plane(component, x_mm):
        normal = component.yZConstructionPlane.geometry.normal
        signed_x = x_mm if normal.x >= 0 else -x_mm
        plane_input = component.constructionPlanes.createInput()
        plane_input.setByOffset(
            component.yZConstructionPlane,
            adsk.core.ValueInput.createByString(str(signed_x) + " mm"),
        )
        return component.constructionPlanes.add(plane_input)

    def inward_x_direction(plane, x_mm):
        desired_x = -1.0 if x_mm > 0 else 1.0
        if plane.geometry.normal.x * desired_x >= 0:
            return adsk.fusion.ExtentDirections.PositiveExtentDirection
        return adsk.fusion.ExtentDirections.NegativeExtentDirection

    # Preserve the simple five-edge outline. PETG sits 0.5 mm behind the
    # bare TPU contact datum. The lower diagonal clears the larger washer seats.
    adapter_outline = [
        (0.0, -1.0), (0.0, 25.7), (40.5, 25.7),
        (40.5, 17.0), (17.0, -1.0),
    ]

    def build_adapter(component, hex_local_x):
        # One profile and one extrusion form the entire visible PETG body.
        # This removes the former coplanar seam between imported OEM/root and
        # cheek solids.
        envelope = component.sketches.add(component.yZConstructionPlane)
        envelope.name = "Single continuous Robotiq-to-UMI adapter envelope"
        add_polygon(envelope, adapter_outline)
        feature = symmetric_extrude(
            component,
            largest_profile(envelope),
            "adapterOverallWidth",
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
        adapter = feature.bodies.item(0)
        adapter.name = "PETG Adapter"

        # Open the 15.88 mm central TPU pocket at Y=10 mm: the unchanged 4 mm
        # Robotiq shoulder plus only 6 mm for the measured 4.9 mm M5 head.
        slot = component.sketches.add(component.xYConstructionPlane)
        slot.name = "Continuous TPU pocket - 0.20 mm clearance per side"
        add_xy_polygon(slot, [(-7.94, 10.0), (7.94, 10.0), (7.94, 100.0), (-7.94, 100.0)])
        symmetric_extrude(
            component,
            largest_profile(slot),
            "100 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        # Preserve the Robotiq removable-fingertip interface: the OEM-derived
        # 4 mm M5 shoulder and two 2 mm indexing sockets remain in place.  Only
        # excess tool-pocket depth beyond the measured head is shortened.
        interface = component.sketches.add(component.xZConstructionPlane)
        interface.name = "Exact Robotiq M5 and indexing interface"
        circles = interface.sketchCurves.sketchCircles
        circles.addByCenterRadius(xz_point(0.0, 12.36), 0.265)
        for pin_x in (-4.5, 4.5):
            circles.addByCenterRadius(xz_point(pin_x, 12.36), 0.100)
        profiles = []
        for index in range(interface.profiles.count):
            p = interface.profiles.item(index)
            profiles.append((p.areaProperties().area, p))
        profiles.sort(key=lambda row: row[0], reverse=True)
        one_side_extrude(
            component,
            profiles[0][1],
            "4 mm",
            positive_y_direction(component),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )
        indexing = adsk.core.ObjectCollection.create()
        indexing.add(profiles[1][1])
        indexing.add(profiles[2][1])
        one_side_extrude(
            component,
            indexing,
            "2.5 mm",
            positive_y_direction(component),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        head_plane = y_offset_plane(component, 4.0)
        head = component.sketches.add(head_plane)
        head.name = "Robotiq M5 SHCS head pocket - 9.2 mm"
        head.sketchCurves.sketchCircles.addByCenterRadius(xz_point(0.0, 12.36), 0.460)
        one_side_extrude(
            component,
            largest_profile(head),
            "6 mm",
            positive_y_direction(component),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        # Three complete M3 through-holes.
        through = component.sketches.add(component.yZConstructionPlane)
        through.name = "Three UMI M3 holder clearances - 3.6 mm"
        for y_mm, z_mm in joint_centres:
            through.sketchCurves.sketchCircles.addByCenterRadius(yz_point(y_mm, z_mm), 0.180)
        symmetric_extrude(
            component,
            profiles_collection(through),
            "30 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        head_local_x = -hex_local_x
        m3_head_plane = x_offset_plane(component, head_local_x)
        m3_head = component.sketches.add(m3_head_plane)
        m3_head.name = "Three shallow washer seats - 7.5 mm"
        for y_mm, z_mm in joint_centres:
            m3_head.sketchCurves.sketchCircles.addByCenterRadius(yz_point(y_mm, z_mm), 0.375)
        one_side_extrude(
            component,
            profiles_collection(m3_head),
            "washerSeatDepth",
            inward_x_direction(m3_head_plane, head_local_x),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        m3_hex_plane = x_offset_plane(component, hex_local_x)
        m3_hex = component.sketches.add(m3_hex_plane)
        m3_hex.name = "Three enclosed UMI M3 captive-nut pockets - 6.3 mm AF"
        radius = 6.3 / math.sqrt(3.0)
        for y_mm, z_mm in joint_centres:
            points = []
            for index in range(6):
                angle = math.radians(index * 60.0)
                points.append((y_mm + radius * math.cos(angle), z_mm + radius * math.sin(angle)))
            add_polygon(m3_hex, points)
        one_side_extrude(
            component,
            profiles_collection(m3_hex),
            "2.5 mm",
            inward_x_direction(m3_hex_plane, hex_local_x),
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )
        return adapter

    def build_tpu(component):
        silhouette = component.sketches.add(component.yZConstructionPlane)
        silhouette.name = "Exact 0.600 UMI exterior at zero-gap datum"
        add_polygon(silhouette, [installed_point(point) for point in profile["outer_polygon_yz_mm"]])
        feature = symmetric_extrude(
            component,
            largest_profile(silhouette),
            "15.48 mm",
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
        finger = feature.bodies.item(0)
        finger.name = "TPU 95A Finger"

        bays = component.sketches.add(component.yZConstructionPlane)
        bays.name = "Six unchanged UMI-derived through-bays"
        for polygon in profile["bay_polygons_yz_mm"]:
            add_polygon(bays, [installed_point(point) for point in polygon])
        symmetric_extrude(
            component,
            profiles_collection(bays),
            "24 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(finger,),
        )

        holes = component.sketches.add(component.yZConstructionPlane)
        holes.name = "Three UMI TPU M3 clearances - 4.0 mm"
        for y_mm, z_mm in joint_centres:
            holes.sketchCurves.sketchCircles.addByCenterRadius(yz_point(y_mm, z_mm), 0.200)
        symmetric_extrude(
            component,
            profiles_collection(holes),
            "24 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(finger,),
        )

        return finger

    parts = []
    for label, is_left, hex_local_x in (("LEFT", True, -13.0), ("RIGHT", False, 13.0)):
        # In a parametric design Fusion can ignore a transform assigned after
        # occurrence creation.  Create each handed occurrence directly in its
        # closed Robotiq jaw frame so the pair is never coincident/overlapped.
        occurrence = root.occurrences.addNewComponent(robotiq_closed_transform(is_left))
        component = occurrence.component
        component.name = label + " V2 handed finger"
        adapter = build_adapter(component, hex_local_x)
        adapter.name = "PETG Adapter " + label
        finger = build_tpu(component)
        finger.name = "TPU 95A Finger " + label
        parts.append((label, occurrence, adapter, finger))

    apply_appearances(app, design, parts[0][2], parts[0][3])
    gray = design.appearances.itemByName("Printed PETG - Light Gray")
    green = design.appearances.itemByName("Printed TPU 95A - Pale Green")
    parts[1][2].appearance = gray
    parts[1][3].appearance = green
    library = app.materialLibraries.itemByName("Fusion Appearance Library")
    yellow = design.appearances.addByCopy(library.appearances.itemByName("Plastic - Matte (Yellow)"),
                                          "V2 printed TPU - Yellow")
    for part in parts:
        part[3].appearance = yellow

    design.computeAll()
    hardware_script = WORKSPACE / "scripts" / "finger_v2_hardware.py"
    hardware_namespace = {"__file__": str(hardware_script), "__name__": "v2_hardware"}
    exec(compile(hardware_script.read_text(encoding="utf-8"), str(hardware_script), "exec"), hardware_namespace)
    for label, occurrence, adapter, finger in parts:
        hardware_namespace["build_hardware"](occurrence.component, label, joint_centres, namespace)

    design_name = "REVIEW_V2_ZeroGap_M3x30"
    prefix = "REVIEW_V2_"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    manager = design.exportManager
    exports = []
    f3d = os.path.join(OUTPUT_DIR, design_name + ".f3d")
    manager.execute(manager.createFusionArchiveExportOptions(f3d, root))
    exports.append(f3d)
    step = os.path.join(OUTPUT_DIR, design_name + ".step")
    manager.execute(manager.createSTEPExportOptions(step, root))
    exports.append(step)
    for label, _occurrence, adapter, _finger in parts:
        exports.append(export_stl(manager, adapter, prefix + "2F85_PETG_Adapter_" + label + "_M3_PRINT_1.stl"))
    exports.append(export_stl(manager, parts[0][3], prefix + "2F85_TPU95A_Finger_M3_PRINT_2.stl"))
    preview = os.path.join(OUTPUT_DIR, design_name + "_preview.png")
    save_flat_preview(app, preview)
    exports.append(preview)

    print("Created", design_name)
    print("Joint centres YZ mm", joint_centres)
    print("LEFT hex local X -13 mm; RIGHT hex local X +13 mm")
    print("Both installed hex faces map to the same global side")
    for path in exports:
        print("EXPORT", path)
