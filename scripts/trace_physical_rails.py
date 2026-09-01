"""Trace the two physical TPU rail silhouettes from the clear lab-cup frame.

This deliberately does not segment or alter any bay.  It refines two manually
seeded silhouette paths against the image gradient, fits each with a single
quadratic (one curvature sign), and writes a rail-only evidence overlay.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


SOURCE = Path(
    r"C:\Users\srini\AppData\Local\Temp\codex-clipboard-7d5aabff-6a83-43d6-88a9-5466351194d7.png"
)
OUTPUT = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\physical_rail_trace"
)

# The upper-left empty finger is the requested reference.  Its side face is
# cleaner and the two exterior rail silhouettes are visible from root to tip.
# Coordinates are in the 768 x 648 user-supplied crop.  These are broad seeds,
# not the delivered trace; the local gradient refinement below moves every
# sampled point onto the visible exterior edge.
CONTACT_SEEDS = np.asarray(
    [
        (121, 294),
        (158, 282),
        (200, 263),
        (245, 238),
        (290, 213),
        (330, 192),
    ],
    np.float64,
)
OUTER_SEEDS = np.asarray(
    [
        (120, 288),
        (133, 258),
        (148, 224),
        (168, 188),
        (194, 160),
        (218, 148),
    ],
    np.float64,
)


def gradient_magnitude(gray: np.ndarray) -> np.ndarray:
    blurred = cv2.GaussianBlur(gray, (0, 0), 0.8)
    dx = cv2.Sobel(blurred, cv2.CV_32F, 1, 0, ksize=3)
    dy = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)
    return cv2.magnitude(dx, dy)


def refine_path(
    gradient: np.ndarray,
    seeds: np.ndarray,
    search_radius: int = 7,
) -> tuple[np.ndarray, np.ndarray]:
    """Snap a seeded y(x) path to the strongest nearby image edge."""

    seed_fit = np.polyfit(seeds[:, 0], seeds[:, 1], 2)
    xs = np.arange(int(seeds[:, 0].min()), int(seeds[:, 0].max()) + 1)
    predicted = np.polyval(seed_fit, xs)
    refined = []
    height, width = gradient.shape
    for x_value, y_value in zip(xs, predicted):
        x_index = int(np.clip(x_value, 0, width - 1))
        y_center = int(round(y_value))
        low = max(0, y_center - search_radius)
        high = min(height - 1, y_center + search_radius)
        column = gradient[low : high + 1, x_index]
        refined.append((x_index, low + int(np.argmax(column))))
    refined_array = np.asarray(refined, np.float64)

    # Two robust passes reject texture speckle while preserving the true edge.
    keep = np.ones(len(refined_array), dtype=bool)
    fit = seed_fit
    for _ in range(2):
        fit = np.polyfit(refined_array[keep, 0], refined_array[keep, 1], 2)
        residual = refined_array[:, 1] - np.polyval(fit, refined_array[:, 0])
        median = np.median(residual)
        mad = np.median(np.abs(residual - median)) + 1e-6
        keep = np.abs(residual - median) <= max(2.5, 3.5 * mad)
    return refined_array[keep], fit


def sampled_curve(fit: np.ndarray, x_min: float, x_max: float) -> np.ndarray:
    xs = np.linspace(x_min, x_max, 500)
    ys = np.polyval(fit, xs)
    return np.rint(np.column_stack((xs, ys))).astype(np.int32)


def curvature_sign(fit: np.ndarray) -> int:
    second_derivative = 2.0 * fit[0]
    return int(np.sign(second_derivative))


def main() -> None:
    image = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(SOURCE)
    if image.shape[1] != 768 or image.shape[0] != 648:
        raise RuntimeError(f"Unexpected reference size: {image.shape[1]} x {image.shape[0]}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gradient = gradient_magnitude(gray)
    contact_points, contact_fit = refine_path(gradient, CONTACT_SEEDS)
    outer_points, outer_fit = refine_path(gradient, OUTER_SEEDS)

    contact_curve = sampled_curve(
        contact_fit, CONTACT_SEEDS[:, 0].min(), CONTACT_SEEDS[:, 0].max()
    )
    outer_curve = sampled_curve(
        outer_fit, OUTER_SEEDS[:, 0].min(), OUTER_SEEDS[:, 0].max()
    )

    # Rail-only evidence view: no bay outlines are drawn here.
    crop = image[75:325, 55:365]
    crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    crop_view = cv2.cvtColor(crop_gray, cv2.COLOR_GRAY2BGR)
    crop_view = cv2.resize(crop_view, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)

    def crop_curve(points: np.ndarray) -> np.ndarray:
        shifted = points.astype(np.float64) - np.asarray((55, 75), np.float64)
        return np.rint(shifted * 4.0).astype(np.int32)

    cv2.polylines(crop_view, [crop_curve(contact_curve)], False, (0, 255, 255), 5, cv2.LINE_AA)
    cv2.polylines(crop_view, [crop_curve(outer_curve)], False, (255, 0, 255), 5, cv2.LINE_AA)
    cv2.putText(
        crop_view,
        "CONTACT RAIL - DIRECT EXTERIOR TRACE",
        (18, 36),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        crop_view,
        "OUTER RAIL - DIRECT EXTERIOR TRACE",
        (18, 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (255, 0, 255),
        2,
        cv2.LINE_AA,
    )
    cv2.putText(
        crop_view,
        "BAYS UNCHANGED / NOT TRACED IN THIS VIEW",
        (18, crop_view.shape[0] - 24),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    overlay_path = OUTPUT / "lab_upper_finger_physical_rails_only.png"
    if not cv2.imwrite(str(overlay_path), crop_view):
        raise RuntimeError(f"Failed to write {overlay_path}")

    edge_view = cv2.normalize(gradient, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    cv2.imwrite(str(OUTPUT / "lab_reference_gradient.png"), edge_view)
    diagnostics = {
        "source": str(SOURCE),
        "source_size_px": [image.shape[1], image.shape[0]],
        "reference": "upper-left empty finger",
        "contact_rail": {
            "quadratic_y_of_x": contact_fit.tolist(),
            "x_range_px": [float(CONTACT_SEEDS[:, 0].min()), float(CONTACT_SEEDS[:, 0].max())],
            "refined_point_count": int(len(contact_points)),
            "curvature_sign": curvature_sign(contact_fit),
        },
        "outer_rail": {
            "quadratic_y_of_x": outer_fit.tolist(),
            "x_range_px": [float(OUTER_SEEDS[:, 0].min()), float(OUTER_SEEDS[:, 0].max())],
            "refined_point_count": int(len(outer_points)),
            "curvature_sign": curvature_sign(outer_fit),
        },
        "bays_changed": False,
    }
    (OUTPUT / "physical_rail_trace.json").write_text(
        json.dumps(diagnostics, indent=2), encoding="utf-8"
    )
    print(overlay_path)
    print(json.dumps(diagnostics, indent=2))


if __name__ == "__main__":
    main()
