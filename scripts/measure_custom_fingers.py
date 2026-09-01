from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


REFERENCE_SPACING_MM = 18.0


@dataclass(frozen=True)
class FingerMeasurement:
    name: str
    hole_a: tuple[float, float]
    hole_b: tuple[float, float]
    tip: tuple[float, float]
    proximal: tuple[float, float]
    width_a: tuple[float, float]
    width_b: tuple[float, float]


# Coordinates are on calibration-flakes-center-crop.png. The two reference
# points are the centers of the OEM fingertip mounting-hole pair. Their 18 mm
# center spacing comes from 2F-85_Open.step / the stock fingertip geometry.
MEASUREMENTS = (
    FingerMeasurement(
        name="left jaw",
        hole_a=(177.5, 112.5),
        hole_b=(226.5, 125.5),
        tip=(206.5, 378.5),
        proximal=(191.0, 82.0),
        width_a=(158.0, 190.0),
        width_b=(226.0, 190.0),
    ),
    FingerMeasurement(
        name="right jaw",
        hole_a=(409.5, 160.5),
        hole_b=(459.5, 166.5),
        tip=(308.5, 412.5),
        proximal=(423.0, 126.0),
        width_a=(383.0, 235.0),
        width_b=(449.0, 235.0),
    ),
)


def vector(a: tuple[float, float], b: tuple[float, float]) -> np.ndarray:
    return np.asarray(b, dtype=float) - np.asarray(a, dtype=float)


def analyze(item: FingerMeasurement) -> dict[str, float]:
    reference = vector(item.hole_a, item.hole_b)
    reference_px = float(np.linalg.norm(reference))
    px_per_mm = reference_px / REFERENCE_SPACING_MM
    width_axis = reference / reference_px
    length_axis = np.asarray((-width_axis[1], width_axis[0]))

    midpoint = (np.asarray(item.hole_a) + np.asarray(item.hole_b)) / 2.0
    tip_delta = np.asarray(item.tip) - midpoint
    if float(np.dot(tip_delta, length_axis)) < 0:
        length_axis *= -1

    proximal_delta = np.asarray(item.tip) - np.asarray(item.proximal)
    width_delta = vector(item.width_a, item.width_b)
    return {
        "reference_px": reference_px,
        "px_per_mm": px_per_mm,
        "tip_longitudinal_mm": float(np.dot(tip_delta, length_axis) / px_per_mm),
        "tip_lateral_mm": float(np.dot(tip_delta, width_axis) / px_per_mm),
        "hole_midpoint_to_tip_mm": float(np.linalg.norm(tip_delta) / px_per_mm),
        "visible_proximal_to_tip_mm": float(np.linalg.norm(proximal_delta) / px_per_mm),
        "profile_width_mm": float(np.linalg.norm(width_delta) / px_per_mm),
    }


def point(value: tuple[float, float]) -> tuple[int, int]:
    return int(round(value[0])), int(round(value[1]))


def annotate(image: np.ndarray, output: Path, results: list[dict[str, float]]) -> None:
    colors = ((30, 220, 30), (30, 170, 255))
    for item, result, color in zip(MEASUREMENTS, results, colors, strict=True):
        a = point(item.hole_a)
        b = point(item.hole_b)
        tip = point(item.tip)
        proximal = point(item.proximal)
        width_a = point(item.width_a)
        width_b = point(item.width_b)
        midpoint = point(((item.hole_a[0] + item.hole_b[0]) / 2, (item.hole_a[1] + item.hole_b[1]) / 2))

        cv2.line(image, a, b, color, 2, cv2.LINE_AA)
        cv2.line(image, midpoint, tip, color, 2, cv2.LINE_AA)
        cv2.line(image, proximal, tip, color, 1, cv2.LINE_AA)
        cv2.line(image, width_a, width_b, color, 2, cv2.LINE_AA)
        for p in (a, b, tip, proximal, width_a, width_b):
            cv2.circle(image, p, 5, color, -1, cv2.LINE_AA)

        label = (
            f"{item.name}: holes-tip {result['hole_midpoint_to_tip_mm']:.1f} mm, "
            f"visible total {result['visible_proximal_to_tip_mm']:.1f} mm"
        )
        label_origin = (max(5, midpoint[0] - 120), max(18, midpoint[1] - 24))
        cv2.putText(image, label, label_origin, cv2.FONT_HERSHEY_SIMPLEX, 0.42, color, 1, cv2.LINE_AA)

    output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output), image):
        raise RuntimeError(f"Failed to write {output}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Scale Skild custom 2F-85 fingers from a known 18 mm mounting-hole pair.")
    parser.add_argument("input", type=Path)
    parser.add_argument("--annotated-output", type=Path)
    args = parser.parse_args()

    image = cv2.imread(str(args.input), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(args.input)

    results = [analyze(item) for item in MEASUREMENTS]
    for item, result in zip(MEASUREMENTS, results, strict=True):
        print(item.name)
        for key, value in result.items():
            print(f"  {key}: {value:.3f}")

    mean_span = sum(r["hole_midpoint_to_tip_mm"] for r in results) / len(results)
    mean_longitudinal = sum(r["tip_longitudinal_mm"] for r in results) / len(results)
    mean_lateral = sum(abs(r["tip_lateral_mm"]) for r in results) / len(results)
    mean_visible = sum(r["visible_proximal_to_tip_mm"] for r in results) / len(results)
    mean_width = sum(r["profile_width_mm"] for r in results) / len(results)
    print("summary")
    print(f"  mean_hole_midpoint_to_tip_mm: {mean_span:.3f}")
    print(f"  mean_longitudinal_mm: {mean_longitudinal:.3f}")
    print(f"  mean_abs_lateral_mm: {mean_lateral:.3f}")
    print(f"  mean_visible_proximal_to_tip_mm: {mean_visible:.3f}")
    print(f"  mean_profile_width_mm: {mean_width:.3f}")

    if args.annotated_output:
        annotate(image.copy(), args.annotated_output, results)


if __name__ == "__main__":
    main()
