"""Create OpenCV evidence views for the Skild custom 2F-85 fingers.

The ROIs are near-profile observations selected from the downloaded source
videos.  Each crop is enlarged without inventing geometry, locally contrast
enhanced, sharpened, and paired with an edge/line view.  These images are for
tracing the real silhouette and rib topology before the next Fusion rebuild.
"""

from pathlib import Path
import json

import cv2
import numpy as np


FRAME_DIR = Path(r"C:\Users\srini\Downloads\extracted\analysis_frames")
OUTPUT_DIR = FRAME_DIR / "opencv_geometry"

# Coordinates are x0, y0, x1, y1 in the original source image.
ROIS = {
    "flakes_left_profile": (
        FRAME_DIR / "calibration-flakes-center-crop.png",
        (125, 125, 270, 415),
    ),
    "flakes_right_profile": (
        FRAME_DIR / "calibration-flakes-center-crop.png",
        (335, 115, 525, 435),
    ),
    "lab_right_profile": (
        FRAME_DIR / "lab-cup-closeup-0.20s.png",
        (1210, 80, 1580, 500),
    ),
    "lab_center_pair": (
        FRAME_DIR / "lab-cup-closeup-0.20s.png",
        (790, 245, 1130, 625),
    ),
    "syringe_outer_shell": (
        FRAME_DIR / "syringe-hold-closeup-2.40s.png",
        (610, 250, 1110, 650),
    ),
}

# Traced in original pixels from the sharp flakes-left profile.  The trace is
# repeated against the second jaw and the lab side view before being accepted.
TRACE_OUTER = [
    (47, 15),
    (46, 50),
    (43, 75),
    (42, 105),
    (44, 135),
    (48, 165),
    (53, 195),
    (61, 230),
    (70, 260),
    (72, 268),
]
TRACE_INNER = [
    (109, 15),
    (108, 42),
    (104, 65),
    (99, 95),
    (94, 125),
    (88, 155),
    (82, 185),
    (77, 220),
    (73, 250),
    (72, 268),
]
TRACE_BAYS = [
    # Bay 0 repeats bay 1 but is mostly occluded by the PETG adapter.  Its full
    # inferred outline is retained here; only a small fragment is image-visible.
    [(50, 20), (104, 18), (102, 36), (49, 38)],
    [(50, 48), (104, 40), (102, 57), (49, 65)],
    [(48, 69), (99, 61), (94, 82), (47, 103)],
    [(47, 108), (92, 87), (86, 119), (50, 145)],
    [(51, 150), (84, 125), (79, 159), (59, 193)],
    [(61, 197), (78, 164), (74, 206), (68, 232)],
]

# PETG side-cheek landmarks from the flakes-right near-profile view, in the
# original (pre-upscale) crop pixels.  This is the clearest frame in which all
# three fastener heads and the full cheek perimeter are visible.  The affine
# reference below uses the root inner/outer screws and the distal outer screw;
# it removes the in-plane camera rotation without pretending to recover hidden
# back-side geometry.
ADAPTER_OUTLINE = [
    (70, 10),
    (145, 23),
    (122, 127),
    (105, 130),
    (55, 55),
]
ADAPTER_SCREWS = [(75, 39), (125, 50), (113, 105)]
ADAPTER_CAD_SCREWS_YZ_MM = [(10.0, 21.0), (10.0, 3.0), (31.0, 3.0)]


def enhance(crop: np.ndarray, scale: int = 4) -> np.ndarray:
    enlarged = cv2.resize(
        crop,
        None,
        fx=scale,
        fy=scale,
        interpolation=cv2.INTER_LANCZOS4,
    )
    lab = cv2.cvtColor(enlarged, cv2.COLOR_BGR2LAB)
    lightness, channel_a, channel_b = cv2.split(lab)
    lightness = cv2.createCLAHE(clipLimit=1.6, tileGridSize=(8, 8)).apply(
        lightness
    )
    enhanced = cv2.cvtColor(
        cv2.merge((lightness, channel_a, channel_b)), cv2.COLOR_LAB2BGR
    )
    blur = cv2.GaussianBlur(enhanced, (0, 0), 1.2)
    return cv2.addWeighted(enhanced, 1.65, blur, -0.65, 0)


def edge_overlay(image: np.ndarray) -> np.ndarray:
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 115, apertureSize=3, L2gradient=True)
    edges = cv2.morphologyEx(
        edges, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8)
    )
    overlay = image.copy()
    overlay[edges > 0] = (0, 0, 255)

    lines = cv2.HoughLinesP(
        edges,
        1,
        np.pi / 1800,
        threshold=90,
        minLineLength=90,
        maxLineGap=22,
    )
    if lines is not None:
        for x0, y0, x1, y1 in lines[:, 0]:
            cv2.line(overlay, (x0, y0), (x1, y1), (255, 0, 255), 2)
    return overlay


def kmeans_view(image: np.ndarray, clusters: int = 8) -> np.ndarray:
    small = cv2.resize(image, None, fx=0.5, fy=0.5, interpolation=cv2.INTER_AREA)
    lab = cv2.cvtColor(small, cv2.COLOR_BGR2LAB)
    samples = lab.reshape((-1, 3)).astype(np.float32)
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        50,
        0.2,
    )
    _, labels, centres = cv2.kmeans(
        samples,
        clusters,
        None,
        criteria,
        8,
        cv2.KMEANS_PP_CENTERS,
    )
    quantized = centres[labels.flatten()].reshape(lab.shape).astype(np.uint8)
    quantized = cv2.cvtColor(quantized, cv2.COLOR_LAB2BGR)
    return cv2.resize(
        quantized, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST
    )


def grid_view(image: np.ndarray, original_spacing: int = 10, scale: int = 4) -> np.ndarray:
    """Overlay coordinates expressed in original (pre-upscale) pixels."""

    result = image.copy()
    spacing = original_spacing * scale
    for x in range(0, image.shape[1], spacing):
        cv2.line(result, (x, 0), (x, image.shape[0] - 1), (0, 215, 255), 1)
        cv2.putText(
            result,
            str(x // scale),
            (x + 2, 16),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 215, 255),
            1,
            cv2.LINE_AA,
        )
    for y in range(0, image.shape[0], spacing):
        cv2.line(result, (0, y), (image.shape[1] - 1, y), (0, 215, 255), 1)
        cv2.putText(
            result,
            str(y // scale),
            (2, y + 15),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 215, 255),
            1,
            cv2.LINE_AA,
        )
    return result


def trace_view(image: np.ndarray, scale: int = 4) -> np.ndarray:
    """Draw the accepted five-bay trace over the enhanced source pixels."""

    result = image.copy()

    def scaled(points):
        return np.array([(x * scale, y * scale) for x, y in points], np.int32)

    cv2.polylines(result, [scaled(TRACE_OUTER)], False, (255, 0, 255), 5)
    cv2.polylines(result, [scaled(TRACE_INNER)], False, (0, 255, 255), 5)
    for index, bay in enumerate(TRACE_BAYS):
        polygon = scaled(bay)
        cv2.polylines(result, [polygon], True, (0, 0, 255), 4)
        centre = np.mean(polygon, axis=0).astype(int)
        cv2.putText(
            result,
            str(index),
            tuple(centre),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.1,
            (0, 0, 255),
            3,
            cv2.LINE_AA,
        )
    cv2.putText(
        result,
        "6 THROUGH-BAYS (0-5) - BAY 0 UNDER PETG",
        (12, image.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )
    return result


def adapter_affine():
    """Return the image-pixel to reconstructed PETG side-plane transform."""

    image_points = np.asarray(ADAPTER_SCREWS, dtype=np.float32)
    cad_points = np.asarray(ADAPTER_CAD_SCREWS_YZ_MM, dtype=np.float32)
    return cv2.getAffineTransform(image_points, cad_points)


def adapter_outline_yz_mm():
    points = np.asarray([ADAPTER_OUTLINE], dtype=np.float32)
    transformed = cv2.transform(points, adapter_affine())[0]
    # Snap the observed near-root edge to the known OEM mating plane.  Keep the
    # other values at trace precision so the Fusion generator remains legible.
    transformed[0, 0] = 0.0
    transformed[1, 0] = 0.0
    return [[round(float(y), 1), round(float(z), 1)] for y, z in transformed]


def adapter_trace_view(image: np.ndarray, scale: int = 4) -> np.ndarray:
    """Overlay the accepted PETG cheek and three screw-centre trace."""

    result = image.copy()
    outline = np.asarray(
        [(x * scale, y * scale) for x, y in ADAPTER_OUTLINE], np.int32
    )
    cv2.polylines(result, [outline], True, (255, 0, 255), 5)
    for index, (x, y) in enumerate(ADAPTER_SCREWS, start=1):
        centre = (x * scale, y * scale)
        cv2.circle(result, centre, 10, (0, 0, 255), 4)
        cv2.putText(
            result,
            str(index),
            (centre[0] + 12, centre[1] - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 0, 255),
            3,
            cv2.LINE_AA,
        )
    cv2.putText(
        result,
        "PETG CHEEK TRACE - SCREW 3 ON OUTER-RAIL SIDE",
        (12, image.shape[0] - 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 0, 255),
        2,
        cv2.LINE_AA,
    )
    return result


def normalized_trace():
    """Convert the accepted pixel trace into the CAD's video-derived YZ frame."""

    root_y_px = 50.0
    tip_y_px = 268.0
    root_y_mm = 18.5
    tip_y_mm = 108.0
    px_to_y_mm = (tip_y_mm - root_y_mm) / (tip_y_px - root_y_px)
    px_to_z_mm = 25.0 / (108.0 - 46.0)

    def convert(point):
        x_px, y_px = point
        return [
            round(root_y_mm + (y_px - root_y_px) * px_to_y_mm, 2),
            round((x_px - 46.0) * px_to_z_mm, 2),
        ]

    return {
        "source": "flakes_left_profile",
        "method": "OpenCV edge views plus cross-frame checked landmark trace",
        "outer_yz_mm": [convert(point) for point in TRACE_OUTER],
        "inner_yz_mm": [convert(point) for point in TRACE_INNER],
        "recessed_bays_yz_mm": [
            [convert(point) for point in bay] for bay in TRACE_BAYS
        ],
        "topology": {
            "bay_count": 6,
            "through_openings": True,
            "continuous_back_skin": False,
        },
        "petg_adapter": {
            "source": "flakes_right_profile",
            "method": "three-screw affine side-plane trace",
            "outline_yz_mm": adapter_outline_yz_mm(),
            "joint_screw_centres_yz_mm": [
                list(point) for point in ADAPTER_CAD_SCREWS_YZ_MM
            ],
            "third_screw_location": "distal and toward the outer rail",
        },
    }


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, (path, (x0, y0, x1, y1)) in ROIS.items():
        source = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if source is None:
            raise FileNotFoundError(path)
        crop = source[y0:y1, x0:x1]
        processed = enhance(crop)
        cv2.imwrite(str(OUTPUT_DIR / f"{name}_enhanced.png"), processed)
        cv2.imwrite(
            str(OUTPUT_DIR / f"{name}_edges.png"), edge_overlay(processed)
        )
        cv2.imwrite(
            str(OUTPUT_DIR / f"{name}_kmeans.png"), kmeans_view(processed)
        )
        cv2.imwrite(
            str(OUTPUT_DIR / f"{name}_grid.png"), grid_view(processed)
        )
        if name == "flakes_left_profile":
            cv2.imwrite(
                str(OUTPUT_DIR / "flakes_left_profile_trace.png"),
                trace_view(processed),
            )
        if name == "flakes_right_profile":
            cv2.imwrite(
                str(OUTPUT_DIR / "flakes_right_adapter_trace.png"),
                adapter_trace_view(processed),
            )
        print(name, "source", crop.shape[1], "x", crop.shape[0])
    (OUTPUT_DIR / "trace_geometry.json").write_text(
        json.dumps(normalized_trace(), indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
