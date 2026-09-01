"""Build the accepted handed fingers with the reduced, right-angle PETG root."""


SOURCE = (
    r"C:\Users\srini\OneDrive\Documents\ChatGPT\fusion\scripts"
    r"\build_handed_zero_gap_review.py"
)


def run(_context: str):
    namespace = {
        "__file__": SOURCE,
        "__name__": "handed_right_angle_production",
    }
    with open(SOURCE, "r", encoding="utf-8") as stream:
        exec(compile(stream.read(), SOURCE, "exec"), namespace)
    namespace["EXPORT_MODE"] = "production"
    namespace["run"](_context)
