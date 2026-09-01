"""Read-only geometric QA for the active two-part finger design in Fusion."""

import math

import adsk.core
import adsk.fusion


def mm(value_cm):
    return round(value_cm * 10.0, 3)


def extent_mm(body):
    box = body.boundingBox
    return tuple(
        round((high - low) * 10.0, 3)
        for low, high in zip(box.minPoint.asArray(), box.maxPoint.asArray())
    )


def cylinder_rows(body):
    rows = []
    for face in body.faces:
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if not cylinder:
            continue
        axis = cylinder.axis
        origin = cylinder.origin
        rows.append(
            (
                mm(cylinder.radius),
                tuple(round(value, 3) for value in axis.asArray()),
                tuple(mm(value) for value in origin.asArray()),
            )
        )
    return sorted(set(rows))


def y_cylinder_rows(body):
    rows = []
    for face in body.faces:
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if not cylinder or abs(abs(cylinder.axis.y) - 1.0) > 0.001:
            continue
        box = face.boundingBox
        rows.append(
            {
                "radius": mm(cylinder.radius),
                "x": mm(cylinder.origin.x),
                "z": mm(cylinder.origin.z),
                "y_min": mm(box.minPoint.y),
                "y_max": mm(box.maxPoint.y),
                "area": round(face.area * 100.0, 4),
            }
        )
    return rows


def require_y_cylinder(rows, radius, x, z, y_min, y_max, label):
    for row in rows:
        if (
            abs(row["radius"] - radius) <= 0.02
            and abs(row["x"] - x) <= 0.02
            and abs(row["z"] - z) <= 0.02
            and abs(row["y_min"] - y_min) <= 0.05
            and abs(row["y_max"] - y_max) <= 0.05
        ):
            expected_area = 2.0 * math.pi * radius * (y_max - y_min)
            if abs(row["area"] - expected_area) > 0.1:
                raise RuntimeError(label + " is not a complete circular cylinder")
            return row
    raise RuntimeError(label + " was not found at the required size and position")


def require_open_y_cylinder(rows, radius, x, z, y_min, minimum_y_max, label):
    for row in rows:
        if (
            abs(row["radius"] - radius) <= 0.02
            and abs(row["x"] - x) <= 0.02
            and abs(row["z"] - z) <= 0.02
            and abs(row["y_min"] - y_min) <= 0.05
            and row["y_max"] >= minimum_y_max
        ):
            return row
    raise RuntimeError(label + " does not provide the required open clearance")


def enclosed_recess_centres(body, outer_x_mm, expected_edge_count):
    """Return centres of closed inner loops on one transverse outer face."""
    centres = set()
    for face in body.faces:
        plane = adsk.core.Plane.cast(face.geometry)
        if (
            not plane
            or abs(abs(plane.normal.x) - 1.0) > 0.001
            or abs(mm(plane.origin.x) - outer_x_mm) > 0.02
        ):
            continue
        for loop in face.loops:
            if loop.isOuter or loop.edges.count != expected_edge_count:
                continue
            y_values = []
            z_values = []
            for edge in loop.edges:
                bounds = edge.boundingBox
                y_values.extend((mm(bounds.minPoint.y), mm(bounds.maxPoint.y)))
                z_values.extend((mm(bounds.minPoint.z), mm(bounds.maxPoint.z)))
            centres.add(
                (
                    round((min(y_values) + max(y_values)) / 2.0, 2),
                    round((min(z_values) + max(z_values)) / 2.0, 2),
                )
            )
    return centres


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent
    if root.occurrences.count != 2:
        raise RuntimeError(
            "Expected two opposed occurrences; got " + str(root.occurrences.count)
        )

    component = root.occurrences.item(0).component
    if component.bRepBodies.count != 2:
        raise RuntimeError(
            "Expected exactly two master bodies; got "
            + str(component.bRepBodies.count)
        )

    print("Occurrences", root.occurrences.count)
    print("Master component", component.name)
    for body in component.bRepBodies:
        print(
            "BODY",
            body.name,
            "extent_mm",
            extent_mm(body),
            "volume_cm3",
            round(body.volume, 4),
        )
        for radius, axis, origin in cylinder_rows(body):
            print("  CYL radius_mm", radius, "axis", axis, "origin_mm", origin)

    window_sketch = component.sketches.itemByName(
        "Six bays merged directly from consecutive UMI cells"
    )
    if not window_sketch:
        raise RuntimeError("Six-bay sketch was not found")
    print("Bay profiles", window_sketch.profiles.count)

    expected_joint_centres = {
        (17.0, 2.25),
        (17.0, 20.25),
        (38.0, 20.25),
    }
    observed_joint_centres = set()
    for radius, axis, origin in cylinder_rows(
        component.bRepBodies.itemByName("TPU 95A Finger - PRINT 2")
    ):
        if abs(radius - 2.0) <= 0.01 and abs(abs(axis[0]) - 1.0) <= 0.001:
            observed_joint_centres.add((origin[1], origin[2]))
    print("M3 joint centres YZ mm", sorted(observed_joint_centres))
    if observed_joint_centres != expected_joint_centres:
        raise RuntimeError(
            "M3 joint centres do not match the 0.600x UMI triangle"
        )

    petg_body = component.bRepBodies.itemByName("PETG Adapter - PRINT 2")
    petg_y_cylinders = y_cylinder_rows(petg_body)
    print("PETG axial fastening cylinders", petg_y_cylinders)
    require_y_cylinder(
        petg_y_cylinders,
        2.65,
        0.0,
        12.36,
        0.0,
        4.0,
        "OEM M5 shank clearance",
    )
    require_open_y_cylinder(
        petg_y_cylinders,
        4.6,
        0.0,
        12.36,
        4.0,
        9.0,
        "OEM M5 head counterbore",
    )
    for pin_x in (-4.5, 4.5):
        require_y_cylinder(
            petg_y_cylinders,
            1.0,
            pin_x,
            12.36,
            0.0,
            2.5,
            "OEM 2 mm indexing socket at X=" + str(pin_x),
        )

    # The authoritative UMI soft-finger STEP uses Ø4.0 mm TPU clearance for
    # its M3 screws.  Require three complete 15.48 mm-long cylinders.
    tpu_body = component.bRepBodies.itemByName("TPU 95A Finger - PRINT 2")
    expected_m3_area_mm2 = 2.0 * math.pi * 2.0 * 15.48
    tpu_m3_areas = []
    for face in tpu_body.faces:
        cylinder = adsk.core.Cylinder.cast(face.geometry)
        if not cylinder:
            continue
        if (
            abs(mm(cylinder.radius) - 2.0) <= 0.01
            and abs(abs(cylinder.axis.x) - 1.0) <= 0.001
        ):
            tpu_m3_areas.append(round(face.area * 100.0, 6))
    print("TPU full M3 cylinder areas mm2", sorted(tpu_m3_areas))
    if len(tpu_m3_areas) != 3 or any(
        abs(area - expected_m3_area_mm2) > 0.05 for area in tpu_m3_areas
    ):
        raise RuntimeError("At least one TPU M3 clearance is not a complete circle")

    sketch_expectations = (
        ("Original UMI M3 clearance restored to 3.6 mm", math.pi * 1.8**2),
        ("Original UMI TPU M3 clearance - 4.0 mm", math.pi * 2.0**2),
        ("Three original UMI M3 SHCS head pockets - 6.5 mm", math.pi * 3.25**2),
        (
            "Three original UMI M3 captive-nut pockets - 6.3 mm AF",
            math.sqrt(3.0) * 6.3**2 / 2.0,
        ),
    )
    for sketch_name, expected_area_mm2 in sketch_expectations:
        sketch = component.sketches.itemByName(sketch_name)
        if sketch is None or sketch.profiles.count != 3:
            raise RuntimeError(sketch_name + " does not contain three profiles")
        areas = sorted(
            round(sketch.profiles.item(index).areaProperties().area * 100.0, 6)
            for index in range(sketch.profiles.count)
        )
        print(sketch_name, "profile areas mm2", areas)
        if any(abs(area - expected_area_mm2) > 0.05 for area in areas):
            raise RuntimeError(sketch_name + " has the wrong physical size")

    # A correctly sized sketch can still cut through the holder's outer edge.
    # Require all three recess mouths to be closed inner loops on the actual
    # finished PETG body; this fails if any circle or hex is chopped open.
    enclosed_heads = enclosed_recess_centres(petg_body, 11.4, 1)
    enclosed_nuts = enclosed_recess_centres(petg_body, -11.4, 6)
    print("Enclosed M3 head recess centres YZ mm", sorted(enclosed_heads))
    print("Enclosed M3 hex recess centres YZ mm", sorted(enclosed_nuts))
    if enclosed_heads != expected_joint_centres:
        raise RuntimeError("At least one M3 head recess breaks through the PETG edge")
    if enclosed_nuts != expected_joint_centres:
        raise RuntimeError("At least one M3 hex recess breaks through the PETG edge")

    tpu_y_cylinders = y_cylinder_rows(tpu_body)
    print("TPU axial cylinders", tpu_y_cylinders)
    if tpu_y_cylinders:
        raise RuntimeError("TPU must not contain an axial M5 relief or groove")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    tpu_keepout_copy = temporary.copy(tpu_body)
    oem_head_keepout = temporary.createCylinderOrCone(
        adsk.core.Point3D.create(0.0, 0.4, 1.236),
        0.45,
        adsk.core.Point3D.create(0.0, 1.3384, 1.236),
        0.45,
    )
    keepout_operation = temporary.booleanOperation(
        tpu_keepout_copy,
        oem_head_keepout,
        adsk.fusion.BooleanTypes.IntersectionBooleanType,
    )
    keepout_volume = tpu_keepout_copy.volume if keepout_operation else 0.0
    print("TPU-OEM counterbore keepout intersection volume_cm3", keepout_volume)
    if keepout_volume > 1e-6:
        raise RuntimeError("TPU intrudes into the OEM M5 counterbore keepout")

    # In the supplied closed-gripper STEP, local OEM Z=-1.5 mm maps to the
    # X=0 contact plane on both jaws.  Symmetric installed bodies therefore
    # have a closed-position gap of 2 * (minimum local Z + 1.5 mm).
    closed_gaps = {}
    for body in component.bRepBodies:
        minimum_z = mm(body.boundingBox.minPoint.z)
        closed_gaps[body.name] = round(2.0 * (minimum_z + 1.5), 3)
    print("Closed-jaw structural gaps mm", closed_gaps)
    if closed_gaps["PETG Adapter - PRINT 2"] < -0.01:
        raise RuntimeError("PETG adapters overlap at mechanical zero")
    tpu_gap = closed_gaps["TPU 95A Finger - PRINT 2"]
    if not 1.3 <= tpu_gap <= 1.6:
        raise RuntimeError("TPU closed gap does not preserve the safety clearance")
    stock_open_contact_gap = 84.976
    print(
        "Full-open TPU structural gap mm",
        round(tpu_gap + stock_open_contact_gap, 3),
    )

    petg_copy = temporary.copy(petg_body)
    tpu_copy = temporary.copy(tpu_body)
    overlap = temporary.booleanOperation(
        petg_copy,
        tpu_copy,
        adsk.fusion.BooleanTypes.IntersectionBooleanType,
    )
    print("PETG-TPU intersection operation", overlap)
    print("PETG-TPU intersection volume_cm3", round(petg_copy.volume, 6))
    if petg_copy.volume > 1e-6:
        raise RuntimeError("PETG and TPU master bodies overlap")

    for body_name in ("PETG Adapter - PRINT 2", "TPU 95A Finger - PRINT 2"):
        source = component.bRepBodies.itemByName(body_name)
        left_copy = temporary.copy(source)
        right_copy = temporary.copy(source)
        temporary.transform(left_copy, root.occurrences.item(0).transform)
        temporary.transform(right_copy, root.occurrences.item(1).transform)
        pair_operation = temporary.booleanOperation(
            left_copy,
            right_copy,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        )
        pair_volume = left_copy.volume if pair_operation else 0.0
        print(
            "Closed pair intersection",
            body_name,
            "operation",
            pair_operation,
            "volume_cm3",
            round(pair_volume, 6),
        )
        if pair_volume > 1e-6:
            raise RuntimeError(body_name + " pair overlaps at mechanical zero")
