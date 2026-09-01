"""Build two print-ready ArUco plates for the Robotiq 2F-85 linkages.

The official linkage CAD has a pair of M3 protector/accessory holes on each
outer linkage face at 9.0 mm centres.  Each plate uses that pair and carries a
single 4x4_50 marker clear of the screw heads.  The marker top is flush: black
cells fill 0.4 mm-deep pockets in a white PLA plate.

Hardware for this review is the user's M3 x 8 button-head screw:
  - 3.3 mm shank clearance
  - 6.2 mm button-head recess
  - 0.6 mm printed clamping land below the head

The two parts have the same mechanical outline but different marker IDs.
"""

import os

import adsk.core
import adsk.fusion


OUTPUT_DIR = r"C:\Users\srini\Downloads\extracted"
DESIGN_NAME = "REVIEW_Robotiq_2F85_Linkage_Aruco_M3x8_Button"

PLATE_WIDTH_MM = 23.0
PLATE_HEIGHT_MM = 16.0
PLATE_THICKNESS_MM = 2.0
CORNER_RADIUS_MM = 1.5

MOUNT_STRIP_MM = 7.0
HOLE_X_MM = 3.5
HOLE_Y_MM = (3.5, 12.5)
HOLE_SPACING_MM = 9.0
M3_CLEARANCE_MM = 3.3
BUTTON_HEAD_RECESS_MM = 6.2
CLAMPING_LAND_MM = 0.6

MARKER_FIELD_MM = 16.0
MARKER_SIZE_MM = 12.0
MARKER_CELL_MM = 2.0
MARKER_INSET_MM = 2.0
MARKER_RELIEF_MM = 0.4

# OpenCV DICT_4X4_50 marker images, including their mandatory one-cell black
# border.  1 = black.  These are IDs 0 and 1 from aprilcube's dictionary.
MARKERS = {
    0: (
        (1, 1, 1, 1, 1, 1),
        (1, 0, 1, 0, 0, 1),
        (1, 1, 0, 1, 0, 1),
        (1, 1, 1, 0, 0, 1),
        (1, 1, 1, 0, 1, 1),
        (1, 1, 1, 1, 1, 1),
    ),
    1: (
        (1, 1, 1, 1, 1, 1),
        (1, 1, 1, 1, 1, 1),
        (1, 0, 0, 0, 0, 1),
        (1, 0, 1, 1, 0, 1),
        (1, 0, 1, 0, 1, 1),
        (1, 1, 1, 1, 1, 1),
    ),
    2: (
        (1, 1, 1, 1, 1, 1),
        (1, 1, 1, 0, 0, 1),
        (1, 1, 1, 0, 0, 1),
        (1, 1, 1, 0, 1, 1),
        (1, 0, 0, 1, 0, 1),
        (1, 1, 1, 1, 1, 1),
    ),
    3: (
        (1, 1, 1, 1, 1, 1),
        (1, 0, 1, 1, 0, 1),
        (1, 0, 1, 1, 0, 1),
        (1, 1, 0, 1, 1, 1),
        (1, 1, 0, 0, 1, 1),
        (1, 1, 1, 1, 1, 1),
    ),
}


def mm(value):
    return value / 10.0


def make_box(temporary, x0, y0, z0, dx, dy, dz):
    oriented = adsk.core.OrientedBoundingBox3D.create(
        adsk.core.Point3D.create(mm(x0 + dx / 2.0), mm(y0 + dy / 2.0), mm(z0 + dz / 2.0)),
        adsk.core.Vector3D.create(1.0, 0.0, 0.0),
        adsk.core.Vector3D.create(0.0, 1.0, 0.0),
        mm(dx),
        mm(dy),
        mm(dz),
    )
    return temporary.createBox(oriented)


def make_cylinder(temporary, x, y, z0, z1, diameter):
    return temporary.createCylinderOrCone(
        adsk.core.Point3D.create(mm(x), mm(y), mm(z0)),
        mm(diameter / 2.0),
        adsk.core.Point3D.create(mm(x), mm(y), mm(z1)),
        mm(diameter / 2.0),
    )


def require_boolean(temporary, target, tool, operation, message):
    if not temporary.booleanOperation(target, tool, operation):
        raise RuntimeError(message)


def rounded_plate(temporary):
    radius = CORNER_RADIUS_MM
    body = make_box(
        temporary,
        radius,
        0.0,
        0.0,
        PLATE_WIDTH_MM - 2.0 * radius,
        PLATE_HEIGHT_MM,
        PLATE_THICKNESS_MM,
    )
    across = make_box(
        temporary,
        0.0,
        radius,
        0.0,
        PLATE_WIDTH_MM,
        PLATE_HEIGHT_MM - 2.0 * radius,
        PLATE_THICKNESS_MM,
    )
    require_boolean(
        temporary,
        body,
        across,
        adsk.fusion.BooleanTypes.UnionBooleanType,
        "Could not unite rounded plate cross",
    )
    for x in (radius, PLATE_WIDTH_MM - radius):
        for y in (radius, PLATE_HEIGHT_MM - radius):
            corner = make_cylinder(
                temporary, x, y, 0.0, PLATE_THICKNESS_MM, 2.0 * radius
            )
            require_boolean(
                temporary,
                body,
                corner,
                adsk.fusion.BooleanTypes.UnionBooleanType,
                "Could not unite rounded plate corner",
            )
    return body


def persist_body(component, temporary_body, name):
    body_index = component.bRepBodies.count
    feature = component.features.baseFeatures.add()
    feature.name = name
    feature.startEdit()
    component.bRepBodies.add(temporary_body, feature)
    feature.finishEdit()
    # The proxy returned while a base feature is being edited is invalidated
    # when finishEdit commits it.  Resolve the committed design body again so
    # naming and per-body appearance assignments persist into 3MF export.
    body = component.bRepBodies.item(body_index)
    body.name = name
    return body


def build_plate(component, marker_id):
    temporary = adsk.fusion.TemporaryBRepManager.get()
    white = rounded_plate(temporary)

    # Both screws sit on the 7 mm mounting strip; neither head overlaps the
    # fiducial's white quiet zone or encoded cells.
    for y_mm in HOLE_Y_MM:
        through = make_cylinder(
            temporary,
            HOLE_X_MM,
            y_mm,
            -0.5,
            PLATE_THICKNESS_MM + 0.5,
            M3_CLEARANCE_MM,
        )
        require_boolean(
            temporary,
            white,
            through,
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not cut M3 clearance hole",
        )
        head_relief = make_cylinder(
            temporary,
            HOLE_X_MM,
            y_mm,
            CLAMPING_LAND_MM,
            PLATE_THICKNESS_MM + 0.5,
            BUTTON_HEAD_RECESS_MM,
        )
        require_boolean(
            temporary,
            white,
            head_relief,
            adsk.fusion.BooleanTypes.DifferenceBooleanType,
            "Could not cut button-head relief",
        )

    black_transients = []
    marker_x0 = MOUNT_STRIP_MM + MARKER_INSET_MM
    marker_y0 = MARKER_INSET_MM
    pattern = MARKERS[marker_id]
    for row, row_values in enumerate(pattern):
        for column, is_black in enumerate(row_values):
            if not is_black:
                continue
            x0 = marker_x0 + column * MARKER_CELL_MM
            y0 = marker_y0 + (5 - row) * MARKER_CELL_MM
            pocket = make_box(
                temporary,
                x0,
                y0,
                PLATE_THICKNESS_MM - MARKER_RELIEF_MM,
                MARKER_CELL_MM,
                MARKER_CELL_MM,
                MARKER_RELIEF_MM + 0.1,
            )
            require_boolean(
                temporary,
                white,
                pocket,
                adsk.fusion.BooleanTypes.DifferenceBooleanType,
                "Could not cut a marker cell pocket",
            )
            insert = make_box(
                temporary,
                x0,
                y0,
                PLATE_THICKNESS_MM - MARKER_RELIEF_MM,
                MARKER_CELL_MM,
                MARKER_CELL_MM,
                MARKER_RELIEF_MM,
            )
            black_transients.append(insert)

    white_body = persist_body(component, white, f"ID{marker_id} WHITE plate")
    black_bodies = []
    for index, transient in enumerate(black_transients):
        black_bodies.append(
            persist_body(component, transient, f"ID{marker_id} BLACK cell {index + 1:02d}")
        )
    return white_body, black_bodies


def add_appearances(app, design, white_bodies, black_bodies):
    library = app.materialLibraries.itemByName("Fusion Appearance Library")
    white_source = library.appearances.itemByName("Plastic - Matte (White)")
    black_source = library.appearances.itemByName("Plastic - Matte (Black)")
    white = design.appearances.addByCopy(white_source, "Printed PLA - White")
    black = design.appearances.addByCopy(black_source, "Printed PLA - Black")
    for body in white_bodies:
        body.appearance = white
    for body in black_bodies:
        body.appearance = black


def export_3mf(manager, geometry, filename):
    path = os.path.join(OUTPUT_DIR, filename)
    options = manager.createC3MFExportOptions(geometry, path)
    options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
    options.isOneFilePerBody = False
    if not manager.execute(options):
        raise RuntimeError(f"Could not export {path}")
    return path


def run(_context: str):
    app = adsk.core.Application.get()
    document = app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    white_bodies = []
    black_bodies = []
    occurrences = []
    for index, marker_id in enumerate((0, 1)):
        transform = adsk.core.Matrix3D.create()
        transform.translation = adsk.core.Vector3D.create(mm(index * 28.0), 0.0, 0.0)
        occurrence = root.occurrences.addNewComponent(transform)
        occurrence.component.name = f"Robotiq linkage plate - ArUco ID {marker_id}"
        white, black = build_plate(occurrence.component, marker_id)
        white_bodies.append(white)
        black_bodies.extend(black)
        occurrences.append(occurrence)

    add_appearances(app, design, white_bodies, black_bodies)
    manager = design.exportManager

    exports = []
    exports.append(
        export_3mf(
            manager,
            root,
            f"{DESIGN_NAME}_BOTH.3mf",
        )
    )
    for marker_id, occurrence in zip((0, 1), occurrences):
        exports.append(
            export_3mf(
                manager,
                occurrence,
                f"{DESIGN_NAME}_ID{marker_id}.3mf",
            )
        )

    f3d = os.path.join(OUTPUT_DIR, f"{DESIGN_NAME}.f3d")
    step = os.path.join(OUTPUT_DIR, f"{DESIGN_NAME}.step")
    manager.execute(manager.createFusionArchiveExportOptions(f3d, root))
    manager.execute(manager.createSTEPExportOptions(step, root))
    exports.extend((f3d, step))

    app.activeViewport.fit()
    app.activeViewport.refresh()
    preview = os.path.join(OUTPUT_DIR, f"{DESIGN_NAME}_preview.png")
    app.activeViewport.saveAsImageFile(preview, 1600, 1000)
    exports.append(preview)

    print("Robotiq linkage marker review created")
    print("Hole pattern: M3 clearance, 9.0 mm centres")
    print("Hardware: M3 x 8 button head; 6.2 mm head recess; 0.6 mm clamping land")
    print("Marker: DICT_4X4_50 IDs 0 and 1; 12 mm code; 16 mm field")
    for path in exports:
        print(path)
