"""Import and inspect the authoritative UMI holder and matching soft finger."""

import math
import os

import adsk.core
import adsk.fusion


REFERENCE = r"C:\Users\srini\Downloads\extracted\reference_umi"
FILES = (
    os.path.join(REFERENCE, "UMI-LEFT-Finger-Holder.step"),
    os.path.join(REFERENCE, "UMI-LEFT-Soft-Gripper-Finger.step"),
    r"C:\Users\srini\Downloads\extracted\2F-85_Flat_Overmolded_Fingertips.step",
)


def mm(value):
    return round(value * 10.0, 6)


def run(_context: str):
    app = adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design = adsk.fusion.Design.cast(app.activeProduct)
    root = design.rootComponent

    for path in FILES:
        before = root.occurrences.count
        options = app.importManager.createSTEPImportOptions(path)
        app.importManager.importToTarget2(options, root)
        occurrence = root.occurrences.item(before)
        occurrence.component.name = os.path.splitext(os.path.basename(path))[0]

    for occurrence_index in range(root.occurrences.count):
        occurrence = root.occurrences.item(occurrence_index)
        print("COMPONENT", occurrence.component.name)
        for body_index in range(occurrence.component.bRepBodies.count):
            body = occurrence.component.bRepBodies.item(body_index)
            bounds = body.boundingBox
            print(
                " BODY",
                body.name,
                "min_mm",
                (mm(bounds.minPoint.x), mm(bounds.minPoint.y), mm(bounds.minPoint.z)),
                "max_mm",
                (mm(bounds.maxPoint.x), mm(bounds.maxPoint.y), mm(bounds.maxPoint.z)),
            )
            for face in body.faces:
                cylinder = adsk.core.Cylinder.cast(face.geometry)
                if not cylinder:
                    continue
                print(
                    "  CYL radius_mm",
                    mm(cylinder.radius),
                    "axis",
                    (
                        round(cylinder.axis.x, 6),
                        round(cylinder.axis.y, 6),
                        round(cylinder.axis.z, 6),
                    ),
                    "origin_mm",
                    (
                        mm(cylinder.origin.x),
                        mm(cylinder.origin.y),
                        mm(cylinder.origin.z),
                    ),
                    "area_mm2",
                    round(face.area * 100.0, 6),
                )

    app.activeViewport.fit()
    preview = os.path.join(
        r"C:\Users\srini\Downloads\extracted\analysis_frames",
        "UMI_holder_and_finger_source.png",
    )
    app.activeViewport.saveAsImageFile(preview, 1800, 1200)
    print("PREVIEW", preview)
