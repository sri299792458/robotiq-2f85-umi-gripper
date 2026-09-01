"""Copy the actual UMI holder at 0.600 scale and add the Robotiq root.

The triangular UMI cheek geometry is not redrawn.  The source BRep is scaled
and rigidly registered from its three fastener axes to the already-printed
TPU's three axes.  Only the obsolete UMI robot-side mount is trimmed away.
"""

import os


BUILDER = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_direct_umi_060_review.py"
)
UMI_HOLDER_STEP = (
    r"C:\Users\srini\Downloads\extracted\reference_umi"
    r"\UMI-LEFT-Finger-Holder.step"
)
EXPORT_MODE = "review"


def adapter_builder_factory(base):
    adsk = base["adsk"]
    xz_point = base["xz_point"]
    add_polygon = base["add_polygon"]
    largest_profile = base["largest_profile"]
    profiles_collection = base["profiles_collection"]
    symmetric_extrude = base["symmetric_extrude"]
    one_side_extrude = base["one_side_extrude"]
    positive_y_direction = base["positive_y_direction"]

    def bounds_mm(body):
        bounds = body.boundingBox
        return (
            tuple(round(value * 10.0, 3) for value in bounds.minPoint.asArray()),
            tuple(round(value * 10.0, 3) for value in bounds.maxPoint.asArray()),
        )

    def box(temporary, x_mm, y_mm, z_mm, dx_mm, dy_mm, dz_mm):
        oriented = adsk.core.OrientedBoundingBox3D.create(
            adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0),
            adsk.core.Vector3D.create(1.0, 0.0, 0.0),
            adsk.core.Vector3D.create(0.0, 1.0, 0.0),
            dx_mm / 10.0,
            dy_mm / 10.0,
            dz_mm / 10.0,
        )
        return temporary.createBox(oriented)

    def require_boolean(temporary, target, tool, operation, label):
        if not temporary.booleanOperation(target, tool, operation):
            raise RuntimeError(label)

    def build_adapter(component):
        app = adsk.core.Application.get()
        root = component.parentDesign.rootComponent
        source_oem = component.bRepBodies.item(0)
        temporary = adsk.fusion.TemporaryBRepManager.get()
        adapter = temporary.copy(source_oem)

        # Retain the source Robotiq body only through the mounting/root zone.
        # This is an intersection with Y=0..14 mm, not a redrawn base.
        require_boolean(
            temporary,
            adapter,
            box(temporary, 0.0, 7.0, 5.0, 40.0, 14.0, 110.0),
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
            "Could not retain the exact OEM Robotiq root",
        )
        print("OEM root retained bounds mm", bounds_mm(adapter))

        before = root.occurrences.count
        options = app.importManager.createSTEPImportOptions(UMI_HOLDER_STEP)
        app.importManager.importToTarget2(options, root)
        imported = root.occurrences.item(before)
        source_body = imported.component.bRepBodies.item(0)

        holder = temporary.copy(source_body)

        # Exact 0.600 similarity registration from the three actual UMI
        # holder-hole centers to target YZ=(17,2.25),(17,20.25),(38,20.25).
        # Source thickness Z maps to target X and is centered at X=0.
        matrix = adsk.core.Matrix3D.create()
        values = (
            (0.0, 0.0, 0.6, 0.144),
            (0.00975609990, 0.599920674, 0.0, -3.20544311),
            (-0.599920674, 0.00975610275, 0.0, -2.55513088),
        )
        for row, row_values in enumerate(values):
            for column, value in enumerate(row_values):
                matrix.setCell(row, column, value)
        temporary.transform(holder, matrix)
        imported.deleteMe()
        print("Scaled UMI holder bounds mm", bounds_mm(holder))

        # Remove only the UMI robot-side mounting end.  Everything from the
        # triangular three-screw holder onward remains source UMI geometry.
        require_boolean(
            temporary,
            holder,
            box(temporary, 0.0, 46.5, 5.0, 40.0, 67.0, 110.0),
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
            "Could not trim the obsolete UMI robot mount",
        )
        print("Trimmed UMI holder bounds mm", bounds_mm(holder))

        require_boolean(
            temporary,
            adapter,
            holder,
            adsk.fusion.BooleanTypes.UnionBooleanType,
            "The exact OEM root and scaled UMI holder did not unite",
        )
        print("United OEM plus UMI bounds mm", bounds_mm(adapter))

        # The source UMI holder pocket is 26.2 mm for a 25.8 mm TPU tongue:
        # 0.40 mm total, or 0.20 mm clearance per side.  Preserve that physical
        # print clearance around the 15.48 mm scaled TPU instead of scaling the
        # clearance itself, giving a 15.88 mm pocket.
        require_boolean(
            temporary,
            adapter,
            box(temporary, 0.0, 51.75, 5.0, 15.88, 76.5, 110.0),
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not set the copied UMI pocket to 15.88 mm",
        )
        print("Pocket-widened adapter bounds mm", bounds_mm(adapter))

        # Preserve the OEM 4 mm shoulder and expand the stock Ø9.0 head
        # pocket to Ø9.2 for the nominal Ø8.5 x 5 mm M5 SHCS head.
        head_pocket = temporary.createCylinderOrCone(
            adsk.core.Point3D.create(0.0, 0.4, 1.236),
            0.460,
            adsk.core.Point3D.create(0.0, 1.4, 1.236),
            0.460,
        )
        require_boolean(
            temporary,
            adapter,
            head_pocket,
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not expand the M5 SHCS head pocket",
        )

        # The stock fingertip contributes the correct functional mounting
        # geometry but its exterior includes rounded lobes that do not belong
        # on the new adapter.  Enclose that source body in one clean root
        # envelope, then recut only the functional M5 and locating features.
        # The front stays within the OEM 22 mm width and 17.66 mm height; its
        # top blends linearly into the continuous cheek at Y=4 mm.
        clean_root_sketch = component.sketches.add(component.yZConstructionPlane)
        clean_root_sketch.name = "Clean Robotiq functional root envelope"
        add_polygon(
            clean_root_sketch,
            [(0.0, -1.5), (0.0, 17.66), (4.0, 20.5), (4.0, -1.5)],
        )
        clean_root_feature = symmetric_extrude(
            component,
            largest_profile(clean_root_sketch),
            "22 mm",
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
        clean_root_tool = temporary.copy(clean_root_feature.bodies.item(0))
        clean_root_feature.deleteMe()
        require_boolean(
            temporary,
            adapter,
            clean_root_tool,
            adsk.fusion.BooleanTypes.UnionBooleanType,
            "Could not replace the stock curved shell with the clean root",
        )

        # The OEM fingertip exterior leaves only about 0.7 mm above its M5
        # head pocket.  Fill the conversion region with one continuous convex
        # triangular cheek envelope rather than joining a rectangular root to
        # the scaled holder through a visible neck.  Y=0..4 retains the exact
        # OEM functional axes inside the clean envelope; the reinforcement
        # begins behind that shoulder.
        # Keep every full-size M3 recess enclosed after the holder is scaled.
        # The source UMI outline has generous material around its hardware,
        # but a literal 0.600 exterior scale combined with restored full-size
        # M3 pockets lets the recesses break through the contour.  The flat
        # top and extended nose give the two upper pockets at least 1.4 mm of
        # PETG; the lower closing datum remains exactly Z=-1.5 mm and extends
        # past the lower pocket, enclosing it without changing jaw closure.
        cheek_outline = [
            (4.0, -1.5),
            (4.0, 20.5),
            (13.0, 24.9),
            (38.0, 24.9),
            (42.9, 23.0),
            (42.9, 17.5),
            (40.620, 16.559),
            (20.366, -0.389),
            (19.5, -1.5),
            (14.0, -1.5),
        ]
        cheek_sketch = component.sketches.add(component.yZConstructionPlane)
        cheek_sketch.name = "Continuous convex UMI-to-Robotiq triangular cheek"
        add_polygon(cheek_sketch, cheek_outline)
        cheek_feature = symmetric_extrude(
            component,
            largest_profile(cheek_sketch),
            "22.8 mm",
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
        cheek_body = cheek_feature.bodies.item(0)
        cheek_tool = temporary.copy(cheek_body)
        cheek_feature.deleteMe()
        require_boolean(
            temporary,
            adapter,
            cheek_tool,
            adsk.fusion.BooleanTypes.UnionBooleanType,
            "Could not unite the continuous triangular reinforcement",
        )

        # Reopen the 15.88 mm TPU pocket after the full-width convex cheek union.
        require_boolean(
            temporary,
            adapter,
            box(temporary, 0.0, 51.75, 5.0, 15.88, 76.5, 110.0),
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not reopen the 15.88 mm TPU pocket through the reinforcement",
        )

        # The reinforcement begins at the OEM Y=4 shoulder, so restore the
        # open Ø9.2 M5 head/tool pocket through Y=4..14 after the union.
        reinforced_head_pocket = temporary.createCylinderOrCone(
            adsk.core.Point3D.create(0.0, 0.4, 1.236),
            0.460,
            adsk.core.Point3D.create(0.0, 1.4, 1.236),
            0.460,
        )
        require_boolean(
            temporary,
            adapter,
            reinforced_head_pocket,
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not restore the M5 head pocket through the reinforcement",
        )

        # The clean envelope filled the OEM mounting cuts.  Restore the exact
        # functional axes and depths on its flat mating face.
        m5_shank = temporary.createCylinderOrCone(
            adsk.core.Point3D.create(0.0, 0.0, 1.236),
            0.265,
            adsk.core.Point3D.create(0.0, 0.4, 1.236),
            0.265,
        )
        require_boolean(
            temporary,
            adapter,
            m5_shank,
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not restore the clean-root M5 shank clearance",
        )
        for pin_x_mm in (-4.5, 4.5):
            locating_socket = temporary.createCylinderOrCone(
                adsk.core.Point3D.create(pin_x_mm / 10.0, 0.0, 1.236),
                0.100,
                adsk.core.Point3D.create(pin_x_mm / 10.0, 0.25, 1.236),
                0.100,
            )
            require_boolean(
                temporary,
                adapter,
                locating_socket,
                adsk.fusion.BooleanTypes.DifferenceBooleanType,
                "Could not restore a clean-root locating socket",
            )

        source_oem.deleteMe()
        source_feature = component.features.baseFeatures.add()
        source_feature.name = "Continuous scaled-UMI cheek plus clean Robotiq root"
        source_feature.startEdit()
        persisted = component.bRepBodies.add(adapter, source_feature)
        source_feature.finishEdit()
        persisted.name = "Continuous triangular UMI holder with Robotiq OEM root"
        return persisted

    return build_adapter


def joint_cutter_factory(base):
    import math

    adsk = base["adsk"]
    yz_point = base["yz_point"]
    add_polygon = base["add_polygon"]
    profiles_collection = base["profiles_collection"]
    symmetric_extrude = base["symmetric_extrude"]
    one_side_extrude = base["one_side_extrude"]

    def cut_three_joint_bolts(component):
        centres = base["JOINT_BOLT_CENTRES"]
        adapter = component.bRepBodies.itemByName(
            "Continuous triangular UMI holder with Robotiq OEM root"
        )
        finger = component.bRepBodies.itemByName("TPU 95A direct 0.600 UMI six-bay finger")
        bodies = [component.bRepBodies.item(index) for index in range(component.bRepBodies.count)]
        print("Bodies before fastener cuts:", [(body.name, body.isValid) for body in bodies])
        if adapter is None:
            adapter = bodies[0]
        if finger is None:
            finger = bodies[1]
        if adapter is None or finger is None:
            raise RuntimeError("Could not resolve the PETG and TPU bodies before fastener cuts")

        adapter_holes = component.sketches.add(component.yZConstructionPlane)
        adapter_holes.name = "Original UMI M3 clearance restored to 3.6 mm"
        circles = adapter_holes.sketchCurves.sketchCircles
        for y_mm, z_mm in centres:
            circles.addByCenterRadius(yz_point(y_mm, z_mm), 0.180)
        symmetric_extrude(
            component,
            profiles_collection(adapter_holes),
            "30 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        # Restore the source UMI's standard-hardware features at physical M3
        # size after the 0.600 body scale: Ø6.5 x 2.4 mm SHCS head pockets on
        # +X and 6.3 mm-AF x 2.5 mm captive-nut pockets on -X.
        planes = component.constructionPlanes
        head_plane_input = planes.createInput()
        head_plane_input.setByOffset(
            component.yZConstructionPlane,
            adsk.core.ValueInput.createByString("11.4 mm"),
        )
        head_plane = planes.add(head_plane_input)
        head_plane.name = "M3 SHCS head seating plane"
        head_pockets = component.sketches.add(head_plane)
        head_pockets.name = "Three original UMI M3 SHCS head pockets - 6.5 mm"
        circles = head_pockets.sketchCurves.sketchCircles
        for y_mm, z_mm in centres:
            circles.addByCenterRadius(yz_point(y_mm, z_mm), 0.325)
        head_direction = (
            adsk.fusion.ExtentDirections.NegativeExtentDirection
            if head_plane.geometry.normal.x > 0
            else adsk.fusion.ExtentDirections.PositiveExtentDirection
        )
        one_side_extrude(
            component,
            profiles_collection(head_pockets),
            "2.4 mm",
            head_direction,
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        nut_plane_input = planes.createInput()
        nut_plane_input.setByOffset(
            component.yZConstructionPlane,
            adsk.core.ValueInput.createByString("-11.4 mm"),
        )
        nut_plane = planes.add(nut_plane_input)
        nut_plane.name = "M3 captive-nut seating plane"
        nut_pockets = component.sketches.add(nut_plane)
        nut_pockets.name = "Three original UMI M3 captive-nut pockets - 6.3 mm AF"
        hex_radius = 6.3 / math.sqrt(3.0)
        for y_mm, z_mm in centres:
            points = []
            for index in range(6):
                angle = math.radians(index * 60.0)
                points.append(
                    (
                        y_mm + hex_radius * math.cos(angle),
                        z_mm + hex_radius * math.sin(angle),
                    )
                )
            add_polygon(nut_pockets, points)
        nut_direction = (
            adsk.fusion.ExtentDirections.PositiveExtentDirection
            if nut_plane.geometry.normal.x > 0
            else adsk.fusion.ExtentDirections.NegativeExtentDirection
        )
        one_side_extrude(
            component,
            profiles_collection(nut_pockets),
            "2.5 mm",
            nut_direction,
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(adapter,),
        )

        # The authoritative UMI soft-finger STEP uses Ø4.0 mm clearance around
        # its M3 screws.  Restore that diameter instead of the rejected M4 cut.
        tpu_holes = component.sketches.add(component.yZConstructionPlane)
        tpu_holes.name = "Original UMI TPU M3 clearance - 4.0 mm"
        circles = tpu_holes.sketchCurves.sketchCircles
        for y_mm, z_mm in centres:
            circles.addByCenterRadius(yz_point(y_mm, z_mm), 0.200)
        symmetric_extrude(
            component,
            profiles_collection(tpu_holes),
            "30 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(finger,),
        )
        return centres

    return cut_three_joint_bolts


def run(_context: str):
    namespace = {
        "__file__": BUILDER,
        "__name__": "scaled_umi_holder_adapter_review_builder",
    }
    with open(BUILDER, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), BUILDER, "exec"), namespace)
    namespace["EXPORT_MODE"] = EXPORT_MODE
    namespace["ADAPTER_BUILDER_FACTORY"] = adapter_builder_factory
    namespace["JOINT_CUTTER_FACTORY"] = joint_cutter_factory
    if EXPORT_MODE != "production":
        namespace["REVIEW_DESIGN_NAME"] = "REVIEW_ONLY_Scaled_UMI_Holder_Robotiq_Root_M3"
        namespace["REVIEW_STL_PREFIX"] = "REVIEW_ONLY_UMI_M3_"
    namespace["run"](_context)
