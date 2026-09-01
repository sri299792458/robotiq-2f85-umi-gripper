"""Register the manually clicked lab-frame rail traces to the accepted CAD bays.

The registration uses the three visible PETG-to-TPU screw centres plus the
already accepted fingertip meeting point.  Accepted bay coordinates are read
from the existing evidence JSON and are never modified by this script.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


SOURCE = Path(
    r"C:\Users\srini\AppData\Local\Temp\codex-clipboard-7d5aabff-6a83-43d6-88a9-5466351194d7.png"
)
BAY_JSON = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\multiframe\cad_trace_geometry.json"
)
OUTPUT = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\physical_rail_trace"
)

# Hough-refined screw-head centres in the 768 x 648 lab reference.
# Correspondence is root/outer, root/inner, distal/outer.
SCREWS_SOURCE_PX = np.asarray(
    [(276.5, 104.5), (290.5, 133.5), (233.5, 132.5)], np.float32
)
SCREWS_CAD_YZ = np.asarray([(10.0, 3.0), (10.0, 21.0), (31.0, 3.0)], np.float32)

# The payload says root-to-tip, but the clicked coordinates visibly run from
# the shared fingertip back toward the PETG root.  Keep the source data exact
# and reverse it only when generating root-to-tip CAD arrays.
OUTER_SOURCE_PX_TIP_TO_ROOT = np.asarray(
    [
        (121.5, 288.7),
        (128.0, 272.8),
        (136.1, 258.2),
        (147.6, 239.2),
        (156.5, 225.5),
        (164.3, 214.0),
        (182.9, 186.7),
        (198.5, 172.1),
        (212.0, 159.6),
        (225.3, 149.9),
    ],
    np.float32,
)
CONTACT_SOURCE_PX_TIP_TO_ROOT = np.asarray(
    [
        (121.5, 288.1),
        (155.4, 259.9),
        (174.1, 243.3),
        (200.2, 217.7),
        (231.0, 197.2),
        (268.0, 169.6),
        (291.4, 155.0),
    ],
    np.float32,
)

# The already accepted nose meeting point in the source-frame CAD convention.
TIP_SOURCE_PX = np.asarray((121.5, 288.4), np.float32)
TIP_CAD_YZ = np.asarray((100.5, 34.27), np.float32)


def accepted_bays() -> list[np.ndarray]:
    payload = json.loads(BAY_JSON.read_text(encoding="utf-8"))
    bays = [np.asarray(points, np.float32) for points in payload["bay_corners_yz_mm"]]
    # Final user-corrected Bay 0 outer-top from [300,80] to [304,74].
    bays[0][0] = np.asarray((19.522, 8.919), np.float32)
    return bays


def perspective_registration() -> np.ndarray:
    source = np.vstack((SCREWS_SOURCE_PX, TIP_SOURCE_PX))
    target = np.vstack((SCREWS_CAD_YZ, TIP_CAD_YZ))
    return cv2.getPerspectiveTransform(source, target)


def transform_points(points: np.ndarray, transform: np.ndarray) -> np.ndarray:
    return cv2.perspectiveTransform(points.reshape(1, -1, 2), transform)[0]


def draw_polyline(image: np.ndarray, points: np.ndarray, color, width=3) -> None:
    cv2.polylines(
        image,
        [np.rint(points).astype(np.int32)],
        False,
        color,
        width,
        cv2.LINE_AA,
    )


def main() -> None:
    image = cv2.imread(str(SOURCE), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(SOURCE)
    OUTPUT.mkdir(parents=True, exist_ok=True)

    registration = perspective_registration()
    inverse = np.linalg.inv(registration)
    bays = accepted_bays()
    outer_cad = transform_points(OUTER_SOURCE_PX_TIP_TO_ROOT, registration)[::-1]
    contact_cad = transform_points(CONTACT_SOURCE_PX_TIP_TO_ROOT, registration)[::-1]

    overlay = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    overlay = cv2.cvtColor(overlay, cv2.COLOR_GRAY2BGR)
    for index, bay in enumerate(bays):
        projected = transform_points(bay, inverse)
        polygon = np.rint(projected).astype(np.int32)
        cv2.polylines(overlay, [polygon], True, (0, 0, 255), 2, cv2.LINE_AA)
        centre = tuple(np.rint(projected.mean(axis=0)).astype(int))
        cv2.putText(
            overlay,
            str(index),
            centre,
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
    draw_polyline(overlay, OUTER_SOURCE_PX_TIP_TO_ROOT, (255, 0, 255), 3)
    draw_polyline(overlay, CONTACT_SOURCE_PX_TIP_TO_ROOT, (0, 255, 255), 3)
    for centre in SCREWS_SOURCE_PX:
        cv2.circle(overlay, tuple(np.rint(centre).astype(int)), 10, (0, 255, 0), 2, cv2.LINE_AA)

    crop = overlay[75:325, 55:365]
    crop = cv2.resize(crop, None, fx=4, fy=4, interpolation=cv2.INTER_LANCZOS4)
    overlay_path = OUTPUT / "manual_rails_with_fixed_bays_registration.png"
    cv2.imwrite(str(overlay_path), crop)

    result = {
        "registration": "projective: three screw centres plus accepted nose",
        "source_to_cad_homography": registration.tolist(),
        "point_order": "PETG root to fingertip",
        "outer_rail_raw_yz_mm": np.round(outer_cad, 4).tolist(),
        "contact_rail_raw_yz_mm": np.round(contact_cad, 4).tolist(),
        "bays_changed": False,
        "overlay": str(overlay_path),
    }
    result_path = OUTPUT / "manual_rail_registration.json"
    result_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
