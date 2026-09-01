"""Render a side section of the recovered UMI finger holder for design reference."""

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw


SOURCE = Path(
    r"C:\Users\srini\Downloads\extracted\reference_umi\UMI-LEFT-Finger-Holder.stl"
)
OUTPUT = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\umi_holder_midsection.png"
)


def main() -> None:
    mesh = trimesh.load_mesh(SOURCE, process=True)
    x_mid = float(mesh.bounds[:, 0].mean())
    lines = trimesh.intersections.mesh_plane(
        mesh,
        plane_normal=np.array([1.0, 0.0, 0.0]),
        plane_origin=np.array([x_mid, 0.0, 0.0]),
    )[:, :, [1, 2]]

    points = lines.reshape(-1, 2)
    low = points.min(axis=0)
    high = points.max(axis=0)
    span = high - low
    canvas = Image.new("RGB", (1000, 760), "white")
    draw = ImageDraw.Draw(canvas)
    scale = min(900.0 / span[0], 650.0 / span[1])

    def map_point(point):
        return (
            50.0 + (point[0] - low[0]) * scale,
            705.0 - (point[1] - low[1]) * scale,
        )

    for segment in lines:
        draw.line((map_point(segment[0]), map_point(segment[1])), fill="black", width=3)
    draw.text((50, 20), f"UMI holder mid-section at X={x_mid:.3f} mm", fill="black")
    draw.text((50, 42), f"YZ span {span[0]:.3f} x {span[1]:.3f} mm (unscaled)", fill="black")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(OUTPUT)
    print(OUTPUT)


if __name__ == "__main__":
    main()
