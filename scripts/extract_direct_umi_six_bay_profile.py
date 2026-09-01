"""Extract the exact UMI exterior section and merge its ribs into six bays."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import trimesh


SOURCE = Path(r"C:\Users\srini\Downloads\extracted\reference_umi\UMI-Soft-Gripper-Finger.stl")
OUTPUT = Path(r"C:\Users\srini\Downloads\extracted\reference_umi\direct_umi_060_six_bay_profile.json")
SCALE = 0.600
ROOT_Y = 14.0
CONTACT_Z = -0.75


def rdp(points: np.ndarray, tolerance: float) -> np.ndarray:
    if len(points) < 3:
        return points
    first = points[0]
    last = points[-1]
    vector = last - first
    length = np.linalg.norm(vector)
    if length <= 1e-12:
        distances = np.linalg.norm(points[1:-1] - first, axis=1)
    else:
        distances = np.abs(
            vector[0] * (first[1] - points[1:-1, 1])
            - vector[1] * (first[0] - points[1:-1, 0])
        ) / length
    index = int(np.argmax(distances))
    if distances[index] <= tolerance:
        return points[[0, -1]]
    split = index + 1
    return np.vstack(
        (rdp(points[: split + 1], tolerance)[:-1], rdp(points[split:], tolerance))
    )


def simplify_closed(points: np.ndarray, tolerance: float) -> np.ndarray:
    if np.linalg.norm(points[0] - points[-1]) < 1e-8:
        points = points[:-1]
    root_index = int(np.argmin(points[:, 0]))
    points = np.vstack((points[root_index:], points[:root_index]))
    tip_index = int(np.argmax(points[:, 0]))
    first_chain = rdp(points[: tip_index + 1], tolerance)
    second_chain = rdp(
        np.vstack((points[tip_index:], points[:1])), tolerance
    )
    return np.vstack((first_chain[:-1], second_chain[:-1]))


def target(source_point):
    longitudinal, height = source_point
    return [
        round(ROOT_Y + SCALE * longitudinal, 4),
        round(CONTACT_Z + SCALE * height, 4),
    ]


def main():
    mesh = trimesh.load_mesh(SOURCE, process=False)
    section = mesh.section(
        plane_origin=[20.0, -12.9, -61.0],
        plane_normal=[0.0, 1.0, 0.0],
    )
    loops = section.discrete
    exterior = max(
        loops,
        key=lambda loop: (loop[:, 0].max() - loop[:, 0].min())
        * (loop[:, 2].max() - loop[:, 2].min()),
    )
    source_exterior = np.column_stack((-exterior[:, 2], exterior[:, 0]))
    target_exterior = np.asarray([target(point) for point in source_exterior])
    simplified = simplify_closed(target_exterior, 0.035)

    # These are the boundary ribs obtained by merging consecutive openings in
    # the exact UMI mid-plane section in groups 3/3/3/3/2/2.  Every number is
    # a source-section vertex (longitudinal distance, height); only the dense
    # ribs between each group's first and last boundary have been removed.
    source_bays = [
        {
            "contact": (10.00, 20.94),
            "outer": [(10.00, 32.08), (10.00, 33.30), (13.00, 33.02), (15.00, 32.82), (19.24, 32.35), (21.23, 32.11), (25.43, 31.55)],
        },
        {
            "contact": (22.97, 33.69),
            "outer": [(27.41, 31.27), (31.61, 30.62), (33.59, 30.29), (37.82, 29.55), (39.80, 29.18), (44.10, 28.32)],
        },
        {
            "contact": (35.84, 48.94),
            "outer": [(46.08, 27.90), (50.48, 26.93), (52.48, 26.46), (57.03, 25.35), (59.04, 24.83), (63.76, 23.55)],
        },
        {
            "contact": (51.36, 69.38),
            "outer": [(65.79, 22.97), (70.75, 21.50), (72.80, 20.87), (78.03, 19.17), (79.27, 18.75), (85.14, 16.69)],
        },
        {
            "contact": (71.13, 88.07),
            "outer": [(86.40, 16.22), (92.58, 13.87), (93.85, 13.36), (100.37, 10.66)],
        },
        {
            "contact": (90.13, 119.20),
            "outer": [(101.65, 10.11), (108.55, 7.01), (109.85, 6.40)],
        },
    ]
    target_bays = []
    for bay in source_bays:
        contact_start, contact_end = bay["contact"]
        outer = bay["outer"]
        polygon = [
            target(outer[0]),
            target((contact_start, 1.80)),
            target((contact_end, 1.80)),
            target(outer[-1]),
        ]
        polygon.extend(target(point) for point in reversed(outer[1:-1]))
        target_bays.append(polygon)

    payload = {
        "source": str(SOURCE),
        "method": "exact UMI mid-plane exterior; consecutive UMI openings merged 3/3/3/3/2/2",
        "scale": SCALE,
        "root_y_mm": ROOT_Y,
        "contact_z_mm": CONTACT_Z,
        "source_envelope_mm": [123.36448669, 40.0, 25.8],
        "target_envelope_nominal_mm": [74.018692, 24.0, 15.48],
        "outer_polygon_yz_mm": np.round(simplified, 4).tolist(),
        "bay_polygons_yz_mm": target_bays,
        "m4_centres_yz_mm": [
            target((5.0, 5.0)),
            target((5.0, 35.0)),
            target((40.0, 35.0)),
        ],
    }
    OUTPUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("outer vertices", len(simplified))
    print("target tip Y", max(point[0] for point in simplified))
    print("M4 centres", payload["m4_centres_yz_mm"])
    print(OUTPUT)


if __name__ == "__main__":
    main()
