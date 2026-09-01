"""Production entry point for the accepted direct 0.600-scale UMI model."""


BUILDER = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_direct_umi_060_review.py"
)


def run(_context: str):
    namespace = {
        "__file__": BUILDER,
        "__name__": "direct_umi_060_production_builder",
    }
    with open(BUILDER, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), BUILDER, "exec"), namespace)
    namespace["EXPORT_MODE"] = "production"
    namespace["run"](_context)

