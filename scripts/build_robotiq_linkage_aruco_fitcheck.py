"""Place the two-hole ArUco review plates on the official closed 2F-85 CAD."""

import math
import os

import adsk.core
import adsk.fusion


PLATE_BUILDER = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_robotiq_linkage_aruco_plates_review.py"
)
ROBOTIQ_CLOSED_STEP = r"C:\Users\srini\Downloads\extracted\2F-85_Closed.step"
OUTPUT_DIR = r"C:\Users\srini\Downloads\extracted"
FITCHECK_NAME = "REVIEW_Robotiq_2F85_Linkage_Aruco_M3x8_Button_FITCHECK"


def placement_matrix(root_hole, tip_hole, outward_sign):
    """Map local plate XY to a linkage face and local +Z outward."""

    dx = tip_hole[0] - root_hole[0]
    dy = tip_hole[1] - root_hole[1]
    length = math.hypot(dx, dy)
    vy = (dx / length, dy / length, 0.0)  # local +Y along the hole pair

    # The plate's +X side carries the marker.  Point it away from the gripper
    # centre while retaining a right-handed local frame whose +Z is outward.
    if outward_sign < 0:
        vx = (-vy[1], vy[0], 0.0)
        vz = (0.0, 0.0, -1.0)
    else:
        vx = (vy[1], -vy[0], 0.0)
        vz = (0.0, 0.0, 1.0)

    # Plate hole 1 is at local (3.5, 3.5, 0) mm.
    tx = root_hole[0] - 3.5 * vx[0] - 3.5 * vy[0]
    ty = root_hole[1] - 3.5 * vx[1] - 3.5 * vy[1]
    tz = root_hole[2]

    matrix = adsk.core.Matrix3D.create()
    axes = (vx, vy, vz)
    for column, axis in enumerate(axes):
        for row, value in enumerate(axis):
            matrix.setCell(row, column, value)
    matrix.translation = adsk.core.Vector3D.create(tx / 10.0, ty / 10.0, tz / 10.0)
    return matrix


def run(_context: str):
    namespace = {"__file__": PLATE_BUILDER, "__name__": "aruco_plate_builder"}
    with open(PLATE_BUILDER, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), PLATE_BUILDER, "exec"), namespace)

    app = adsk.core.Application.get()
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    options = app.importManager.createSTEPImportOptions(ROBOTIQ_CLOSED_STEP)
    app.importManager.importToTarget2(options, root)

    placements = (
        (
            0,
            (-11.004, 79.491, -17.5),
            (-10.163, 88.451, -17.5),
            -1,
        ),
        (
            1,
            (11.004, 79.491, 17.5),
            (10.163, 88.451, 17.5),
            1,
        ),
    )

    white_bodies = []
    black_bodies = []
    for marker_id, root_hole, tip_hole, outward_sign in placements:
        transform = placement_matrix(root_hole, tip_hole, outward_sign)
        occurrence = root.occurrences.addNewComponent(transform)
        occurrence.component.name = f"Fitted ArUco ID {marker_id} linkage plate"
        white, black = namespace["build_plate"](occurrence.component, marker_id)
        white_bodies.append(white)
        black_bodies.extend(black)

    namespace["add_appearances"](app, design, white_bodies, black_bodies)
    manager = design.exportManager
    f3d = os.path.join(OUTPUT_DIR, FITCHECK_NAME + ".f3d")
    step = os.path.join(OUTPUT_DIR, FITCHECK_NAME + ".step")
    manager.execute(manager.createFusionArchiveExportOptions(f3d, root))
    manager.execute(manager.createSTEPExportOptions(step, root))

    app.activeViewport.fit()
    app.activeViewport.refresh()
    preview = os.path.join(OUTPUT_DIR, FITCHECK_NAME + "_preview.png")
    app.activeViewport.saveAsImageFile(preview, 1600, 1200)

    print("Mounted two-hole marker fit-check on official closed 2F-85 CAD")
    print("M3 centres: 9.0 mm; marker faces point outward")
    print(f3d)
    print(step)
    print(preview)

