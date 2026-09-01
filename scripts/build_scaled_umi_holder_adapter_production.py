"""Promote the verified scaled-UMI M3 holder and Robotiq root build."""

REVIEW_BUILDER = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_scaled_umi_holder_adapter_review.py"
)


def run(_context: str):
    namespace = {
        "__file__": REVIEW_BUILDER,
        "__name__": "scaled_umi_holder_adapter_production_builder",
    }
    with open(REVIEW_BUILDER, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), REVIEW_BUILDER, "exec"), namespace)
    namespace["EXPORT_MODE"] = "production"
    namespace["run"](_context)
