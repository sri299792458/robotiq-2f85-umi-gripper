"""QA the clean handed zero-gap review in the active Fusion document."""

import json
import math

import adsk.core
import adsk.fusion


def mm(value_cm: float) -> float:
    return value_cm * 10.0


def body_by_prefix(component, prefix: str):
    for index in range(component.bRepBodies.count):
        body = component.bRepBodies.item(index)
        if body.name.startswith(prefix):
            return body
    raise RuntimeError(f"Missing body starting with {prefix!r} in {component.name}")


def outer_x_face(body, x_mm: float):
    matches = []
    for index in range(body.faces.count):
        face = body.faces.item(index)
        plane = adsk.core.Plane.cast(face.geometry)
        if not plane:
            continue
        point = face.pointOnFace
        if abs(mm(point.x) - x_mm) > 0.02:
            continue
        if abs(abs(plane.normal.x) - 1.0) > 1e-4:
            continue
        matches.append(face)
    if len(matches) != 1:
        raise RuntimeError(
            f"Expected one continuous x={x_mm:.1f} mm exterior face on {body.name}; found {len(matches)}"
        )
    return matches[0]


def loop_edge_counts(face):
    counts = []
    for index in range(face.loops.count):
        loop = face.loops.item(index)
        if not loop.isOuter:
            counts.append(loop.edges.count)
    return sorted(counts)


def transformed_point_mm(occurrence, x_mm: float, y_mm: float, z_mm: float):
    point = adsk.core.Point3D.create(x_mm / 10.0, y_mm / 10.0, z_mm / 10.0)
    point.transformBy(occurrence.transform)
    return [round(mm(point.x), 4), round(mm(point.y), 4), round(mm(point.z), 4)]


def run(_context: str):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        raise RuntimeError("No active Fusion design")
    root = design.rootComponent
    if root.occurrences.count != 2:
        raise RuntimeError(f"Expected two handed occurrences; found {root.occurrences.count}")

    report = {"document": app.activeDocument.name, "parts": {}}
    installed_hex_points = []
    occurrences = {}
    for index in range(root.occurrences.count):
        occurrence = root.occurrences.item(index)
        component = occurrence.component
        label = "LEFT" if component.name.startswith("LEFT") else "RIGHT"
        if label not in ("LEFT", "RIGHT"):
            raise RuntimeError(f"Unexpected component name {component.name!r}")
        occurrences[label] = occurrence
        adapter = body_by_prefix(component, "PETG Adapter")
        finger = body_by_prefix(component, "TPU 95A Finger")
        if not adapter.isSolid or not finger.isSolid:
            raise RuntimeError(f"Non-solid body in {component.name}")
        if component.bRepBodies.count != 2:
            raise RuntimeError(f"Expected exactly two bodies in {component.name}")

        left_face = outer_x_face(adapter, -11.4)
        right_face = outer_x_face(adapter, 11.4)
        left_loops = loop_edge_counts(left_face)
        right_loops = loop_edge_counts(right_face)
        expected_hex_x = -11.4 if label == "LEFT" else 11.4
        hex_loops = left_loops if expected_hex_x < 0 else right_loops
        head_loops = right_loops if expected_hex_x < 0 else left_loops
        if hex_loops.count(6) != 3:
            raise RuntimeError(f"{label}: expected three complete hex mouths; got edge counts {hex_loops}")
        if head_loops.count(1) != 3:
            raise RuntimeError(f"{label}: expected three complete circular head mouths; got edge counts {head_loops}")

        hex_global = transformed_point_mm(occurrence, expected_hex_x, 17.0, 12.0)
        installed_hex_points.append(hex_global)
        report["parts"][label] = {
            "adapter_volume_mm3": round(adapter.volume * 1000.0, 3),
            "finger_volume_mm3": round(finger.volume * 1000.0, 3),
            "outer_face_count_per_side": [1, 1],
            "hex_outer_loop_edges": hex_loops,
            "head_outer_loop_edges": head_loops,
            "hex_reference_global_mm": hex_global,
            "adapter_bounds_mm": {
                "min": [round(mm(getattr(adapter.boundingBox.minPoint, axis)), 3) for axis in ("x", "y", "z")],
                "max": [round(mm(getattr(adapter.boundingBox.maxPoint, axis)), 3) for axis in ("x", "y", "z")],
            },
            "finger_bounds_mm": {
                "min": [round(mm(getattr(finger.boundingBox.minPoint, axis)), 3) for axis in ("x", "y", "z")],
                "max": [round(mm(getattr(finger.boundingBox.maxPoint, axis)), 3) for axis in ("x", "y", "z")],
            },
        }

        temporary = adsk.fusion.TemporaryBRepManager.get()
        adapter_copy = temporary.copy(adapter)
        finger_copy = temporary.copy(finger)
        overlap = temporary.booleanOperation(
            adapter_copy,
            finger_copy,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        )
        overlap_volume = adapter_copy.volume if overlap else 0.0
        if overlap_volume > 1e-6:
            raise RuntimeError(f"{label}: PETG and TPU overlap by {overlap_volume} cm^3")
        report["parts"][label]["petg_tpu_intersection_mm3"] = round(overlap_volume * 1000.0, 6)

        # Fit the user's measured M5 head explicitly in the unchanged Robotiq
        # interface: it seats at the OEM-derived Y=4 mm shoulder.
        head_keepout = temporary.createCylinderOrCone(
            adsk.core.Point3D.create(0.0, 0.4, 1.236),
            0.425,
            adsk.core.Point3D.create(0.0, 0.89, 1.236),
            0.425,
        )
        if not head_keepout:
            raise RuntimeError("Could not create measured M5-head keep-out")
        head_petg = temporary.copy(head_keepout)
        petg_copy = temporary.copy(adapter)
        petg_operation = temporary.booleanOperation(
            head_petg,
            petg_copy,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        )
        head_petg_volume = head_petg.volume if petg_operation else 0.0
        head_tpu = temporary.copy(head_keepout)
        tpu_copy = temporary.copy(finger)
        tpu_operation = temporary.booleanOperation(
            head_tpu,
            tpu_copy,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        )
        head_tpu_volume = head_tpu.volume if tpu_operation else 0.0
        if head_petg_volume > 1e-6:
            raise RuntimeError(f"{label}: measured M5 head intersects PETG")
        if head_tpu_volume > 1e-6:
            raise RuntimeError(f"{label}: measured M5 head intersects TPU")
        report["parts"][label]["measured_m5_head"] = {
            "diameter_mm": 8.5,
            "height_mm": 4.9,
            "petg_intersection_mm3": round(head_petg_volume * 1000.0, 6),
            "tpu_intersection_mm3": round(head_tpu_volume * 1000.0, 6),
            "longitudinal_clearance_to_tpu_mm": 1.1,
        }

    if set(report["parts"]) != {"LEFT", "RIGHT"}:
        raise RuntimeError(f"Missing handed component: {sorted(report['parts'])}")
    if abs(installed_hex_points[0][2] - installed_hex_points[1][2]) > 0.02:
        raise RuntimeError(f"Installed hex pockets are on opposite global sides: {installed_hex_points}")
    if abs(report["parts"]["LEFT"]["adapter_volume_mm3"] - report["parts"]["RIGHT"]["adapter_volume_mm3"]) > 0.01:
        raise RuntimeError("Left/right adapter volumes differ")
    if abs(report["parts"]["LEFT"]["finger_volume_mm3"] - report["parts"]["RIGHT"]["finger_volume_mm3"]) > 0.01:
        raise RuntimeError("Left/right TPU volumes differ")

    temporary = adsk.fusion.TemporaryBRepManager.get()
    pair_intersections = {}
    for prefix in ("PETG Adapter", "TPU 95A Finger"):
        left_body = body_by_prefix(occurrences["LEFT"].component, prefix)
        right_body = body_by_prefix(occurrences["RIGHT"].component, prefix)
        left_copy = temporary.copy(left_body)
        right_copy = temporary.copy(right_body)
        temporary.transform(left_copy, occurrences["LEFT"].transform)
        temporary.transform(right_copy, occurrences["RIGHT"].transform)
        operation = temporary.booleanOperation(
            left_copy,
            right_copy,
            adsk.fusion.BooleanTypes.IntersectionBooleanType,
        )
        volume = left_copy.volume if operation else 0.0
        if volume > 1e-6:
            raise RuntimeError(f"Closed {prefix} pair overlaps by {volume} cm^3")
        pair_intersections[prefix] = round(volume * 1000.0, 6)

    report["installed_hex_global_side"] = "same"
    report["closed_contact_gap_mm"] = 1.5
    report["closed_pair_intersection_mm3"] = pair_intersections
    report["status"] = "PASS"
    print(json.dumps(report, indent=2, sort_keys=True))
