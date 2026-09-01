"""Build the accepted TPU with a mechanically redrafted PETG adapter.

This is review-only.  It cannot overwrite the accepted production STL/F3D.
"""


BUILDER = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_direct_umi_060_review.py"
)


def run(_context: str):
    namespace = {
        "__file__": BUILDER,
        "__name__": "petg_adapter_redesign_review_builder",
    }
    with open(BUILDER, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), BUILDER, "exec"), namespace)

    # The three M4 axes and the TPU are already fixed by the part now being
    # printed.  This fresh four-edge cheek maximizes the available material
    # around those axes while preserving the exact Robotiq mating interface.
    # Local Z cannot extend below -1.5 mm without the opposed PETG adapters
    # colliding at the 2F-85 mechanical closed position.  Z=-1.3 leaves a
    # deliberate 0.4 mm pair clearance.
    namespace["PETG_SIDE_PROFILE_OVERRIDE"] = [
        (0.0, -1.3),
        (44.0, -1.3),
        (44.0, 25.7),
        (0.0, 27.5),
    ]
    namespace["REVIEW_DESIGN_NAME"] = "REVIEW_ONLY_PETG_Adapter_Redraft"
    namespace["REVIEW_STL_PREFIX"] = "REVIEW_ONLY_PETG_REDRAFT_"
    namespace["run"](_context)
