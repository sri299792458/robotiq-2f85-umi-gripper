"""Render the shortened PETG root while proving the accepted triangle remains."""

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont


OUTPUT = Path(r"C:\Users\srini\Downloads\extracted")
PETG = OUTPUT / "REVIEW_ONLY_2F85_PETG_Adapter_LEFT_M3_PRINT_1.stl"
TPU = OUTPUT / "REVIEW_ONLY_2F85_TPU95A_Finger_M3_PRINT_2.stl"
PREVIEW = OUTPUT / "REVIEW_ONLY_PETG_distal_trim_review.png"


def font(size: int):
    path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def section(path: Path, x_mm: float):
    mesh = trimesh.load_mesh(path, process=True)
    segments = trimesh.intersections.mesh_plane(
        mesh,
        plane_normal=np.array([1.0, 0.0, 0.0]),
        plane_origin=np.array([x_mm, 20.0, 10.0]),
    )
    return segments[:, :, [1, 2]]


def main() -> None:
    petg = section(PETG, 9.0)
    tpu = section(TPU, 0.0)
    points = np.vstack((petg.reshape(-1, 2), tpu.reshape(-1, 2)))
    minimum = points.min(axis=0)
    maximum = points.max(axis=0)
    span = maximum - minimum

    image = Image.new("RGB", (1700, 950), (247, 248, 250))
    draw = ImageDraw.Draw(image)
    draw.text((45, 28), "PETG distal edge moved inward — review", fill=(20, 23, 28), font=font(36))
    draw.text(
        (47, 80),
        "Gray: PETG trimmed to Y=40.5 mm  |  Green: unchanged TPU  |  all fastener axes fixed",
        fill=(68, 73, 80),
        font=font(22),
    )

    plot = (60, 145, 1640, 865)
    scale = min((plot[2] - plot[0]) / span[0], (plot[3] - plot[1]) / span[1]) * 0.92
    used = span * scale
    origin_x = plot[0] + ((plot[2] - plot[0]) - used[0]) / 2
    origin_y = plot[1] + ((plot[3] - plot[1]) + used[1]) / 2

    def point(value):
        return (
            origin_x + (value[0] - minimum[0]) * scale,
            origin_y - (value[1] - minimum[1]) * scale,
        )

    for segment in petg:
        draw.line((point(segment[0]), point(segment[1])), fill=(88, 93, 101), width=7)
    for segment in tpu:
        draw.line((point(segment[0]), point(segment[1])), fill=(38, 132, 68), width=5)

    # Mark the full-width-root termination; the accepted exterior triangle is
    # untouched to its right.
    root_bottom = point(np.array([10.0, -1.5]))
    root_top = point(np.array([10.0, 25.7]))
    draw.line((root_bottom, root_top), fill=(220, 62, 45), width=3)
    draw.text((root_top[0] + 10, root_top[1] - 5), "TPU seats here: Y=10", fill=(190, 45, 32), font=font(20))

    image.save(PREVIEW)
    print(PREVIEW)


if __name__ == "__main__":
    main()
