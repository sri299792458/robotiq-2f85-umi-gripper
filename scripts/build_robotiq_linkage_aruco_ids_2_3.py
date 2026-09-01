"""Build the second Robotiq linkage marker pair using ArUco IDs 2 and 3."""

import os

import adsk.core
import adsk.fusion


BASE_BUILDER = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_robotiq_linkage_aruco_plates_review.py"
)
OUTPUT_DIR = r"C:\Users\srini\Downloads\extracted"
DESIGN_NAME = "REVIEW_Robotiq_2F85_Linkage_Aruco_M3x8_Button_IDS_2_3"
MARKER_IDS = (2, 3)


def run(_context: str):
    namespace = {"__file__": BASE_BUILDER, "__name__": "aruco_plate_builder"}
    with open(BASE_BUILDER, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), BASE_BUILDER, "exec"), namespace)

    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    white_bodies = []
    black_bodies = []
    occurrences = []
    for index, marker_id in enumerate(MARKER_IDS):
        transform = adsk.core.Matrix3D.create()
        transform.translation = adsk.core.Vector3D.create(index * 2.8, 0.0, 0.0)
        occurrence = root.occurrences.addNewComponent(transform)
        occurrence.component.name = f"Robotiq linkage plate - ArUco ID {marker_id}"
        white, black = namespace["build_plate"](occurrence.component, marker_id)
        white_bodies.append(white)
        black_bodies.extend(black)
        occurrences.append(occurrence)

    namespace["add_appearances"](app, design, white_bodies, black_bodies)
    manager = design.exportManager
    exports = [
        namespace["export_3mf"](manager, root, DESIGN_NAME + "_BOTH_RAW.3mf")
    ]
    for marker_id, occurrence in zip(MARKER_IDS, occurrences):
        exports.append(
            namespace["export_3mf"](
                manager,
                occurrence,
                DESIGN_NAME + f"_ID{marker_id}.3mf",
            )
        )

    f3d = os.path.join(OUTPUT_DIR, DESIGN_NAME + ".f3d")
    step = os.path.join(OUTPUT_DIR, DESIGN_NAME + ".step")
    manager.execute(manager.createFusionArchiveExportOptions(f3d, root))
    manager.execute(manager.createSTEPExportOptions(step, root))
    exports.extend((f3d, step))

    app.activeViewport.fit()
    app.activeViewport.refresh()
    preview = os.path.join(OUTPUT_DIR, DESIGN_NAME + "_preview.png")
    app.activeViewport.saveAsImageFile(preview, 1600, 1000)
    exports.append(preview)

    print("Additional Robotiq linkage markers created")
    print("ArUco DICT_4X4_50 IDs: 2 and 3")
    for path in exports:
        print(path)

