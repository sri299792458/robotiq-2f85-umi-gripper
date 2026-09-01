"""Build the direct 0.600-scale UMI / Robotiq model in Fusion.

The default is review-only.  The small production entry point sets
``EXPORT_MODE`` to ``production`` before calling :func:`run`.
"""

import json
import os


BASE_SCRIPT = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_skild_inspired_fingers.py"
)
PROFILE_JSON = (
    r"C:\Users\srini\Downloads\extracted\reference_umi"
    r"\direct_umi_060_six_bay_profile.json"
)
EXPORT_MODE = "review"
PETG_SIDE_PROFILE_OVERRIDE = None
REVIEW_DESIGN_NAME = "REVIEW_ONLY_Direct_UMI_060_SixBay_2F85"
REVIEW_STL_PREFIX = "REVIEW_ONLY_DIRECT_UMI_060_"
ADAPTER_BUILDER_FACTORY = None
JOINT_CUTTER_FACTORY = None


def run(_context: str):
    with open(PROFILE_JSON, "r", encoding="utf-8") as stream:
        profile = json.load(stream)

    namespace = {
        "__file__": BASE_SCRIPT,
        "__name__": "direct_umi_060_base",
    }
    with open(BASE_SCRIPT, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), BASE_SCRIPT, "exec"), namespace)

    production = EXPORT_MODE == "production"
    namespace["DESIGN_NAME"] = (
        "Skild_Inspired_2F85_TwoPart_Finger_Set"
        if production
        else REVIEW_DESIGN_NAME
    )
    default_petg_profile = [
        (0.0, 0.0),
        (44.0, 0.0),
        (44.0, 22.0),
        (0.0, 25.0),
    ]
    namespace["PETG_SIDE_PROFILE"] = (
        PETG_SIDE_PROFILE_OVERRIDE or default_petg_profile
    )
    namespace["JOINT_BOLT_CENTRES"] = [
        tuple(point) for point in profile["m4_centres_yz_mm"]
    ]

    adsk = namespace["adsk"]
    yz_point = namespace["yz_point"]
    add_polygon = namespace["add_polygon"]
    largest_profile = namespace["largest_profile"]
    profiles_collection = namespace["profiles_collection"]
    symmetric_extrude = namespace["symmetric_extrude"]

    original_add_parameter = namespace["add_parameter"]

    def direct_add_parameter(design, name, expression, units, comment):
        if name == "adapterSlotWidth":
            expression = "15.88 mm"
            comment = (
                "15.48 mm TPU plus the source UMI clearance of 0.20 mm per side"
            )
        elif name == "tpuFingerThickness":
            expression = "15.48 mm"
            comment = "Exact 0.600 scale of the UMI 25.8 mm thickness"
        elif name == "jointBoltDiameter" and JOINT_CUTTER_FACTORY is not None:
            expression = "3.6 mm"
            comment = "Original UMI M3 holder clearance; TPU clearance is 4.0 mm"
        return original_add_parameter(
            design, name, expression, units, comment
        )

    namespace["add_parameter"] = direct_add_parameter

    def build_direct_tpu(component):
        silhouette = component.sketches.add(component.yZConstructionPlane)
        silhouette.name = "Exact 0.600 UMI exterior mid-plane section"
        add_polygon(
            silhouette,
            [tuple(point) for point in profile["outer_polygon_yz_mm"]],
        )
        feature = symmetric_extrude(
            component,
            largest_profile(silhouette),
            "tpuFingerThickness",
            adsk.fusion.FeatureOperations.NewBodyFeatureOperation,
        )
        finger = feature.bodies.item(0)
        finger.name = "TPU 95A direct 0.600 UMI six-bay finger"

        bays = component.sketches.add(component.yZConstructionPlane)
        bays.name = "Six bays merged directly from consecutive UMI cells"
        for polygon in profile["bay_polygons_yz_mm"]:
            add_polygon(bays, [tuple(point) for point in polygon])
        symmetric_extrude(
            component,
            profiles_collection(bays),
            "24 mm",
            adsk.fusion.FeatureOperations.CutFeatureOperation,
            participant_bodies=(finger,),
        )
        return finger

    namespace["build_tpu_finger"] = build_direct_tpu

    if ADAPTER_BUILDER_FACTORY is not None:
        namespace["build_petg_adapter"] = ADAPTER_BUILDER_FACTORY(namespace)
    if JOINT_CUTTER_FACTORY is not None:
        namespace["cut_three_joint_bolts"] = JOINT_CUTTER_FACTORY(namespace)

    original_export_stl = namespace["export_stl"]

    def review_export_stl(export_manager, body, filename):
        if production:
            return original_export_stl(export_manager, body, filename)
        return original_export_stl(
            export_manager,
            body,
            REVIEW_STL_PREFIX + filename,
        )

    namespace["export_stl"] = review_export_stl
    namespace["run"](_context)
