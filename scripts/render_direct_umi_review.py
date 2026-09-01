"""Render a labeled side section of the direct 0.600 UMI review."""

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont


OUTPUT = Path(r"C:\Users\srini\Downloads\extracted")
TPU_PATH = OUTPUT / "REVIEW_ONLY_DIRECT_UMI_060_2F85_TPU95A_Finger_PRINT_2.stl"
PETG_PATH = OUTPUT / "REVIEW_ONLY_DIRECT_UMI_060_2F85_PETG_Adapter_PRINT_2.stl"
PNG_PATH = OUTPUT / "REVIEW_ONLY_Direct_UMI_060_SixBay_labeled_side.png"
M4_CENTRES = ((17.0, 2.25), (17.0, 20.25), (38.0, 20.25))


def font(size):
    path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def section(path, x_plane):
    mesh = trimesh.load_mesh(path, process=True)
    lines = trimesh.intersections.mesh_plane(
        mesh,
        plane_normal=np.array([1.0, 0.0, 0.0]),
        plane_origin=np.array([x_plane, 45.0, 10.0]),
    )
    return lines[:, :, [1, 2]], mesh


def main():
    tpu_lines, tpu = section(TPU_PATH, 0.0)
    petg_lines, petg = section(PETG_PATH, 9.0)
    bounds = tpu_lines.reshape(-1, 2)
    minimum = bounds.min(axis=0)
    maximum = bounds.max(axis=0)
    span = maximum - minimum

    canvas = Image.new("RGB", (1700, 760), (246, 247, 249))
    draw = ImageDraw.Draw(canvas)
    draw.text((44, 24), "Direct 0.600-scale UMI reconstruction", fill=(18, 20, 23), font=font(34))
    draw.text(
        (46, 70),
        "Actual UMI exterior section • 16 original cells merged into six • holes restored to Ø4.3 mm",
        fill=(70, 74, 80),
        font=font(20),
    )

    plot = (55, 125, 1645, 705)
    width = plot[2] - plot[0]
    height = plot[3] - plot[1]
    scale = min(width / span[0], height / span[1]) * 0.91
    used = span * scale
    origin_x = plot[0] + (width - used[0]) / 2
    origin_y = plot[1] + (height + used[1]) / 2

    def point(value):
        return (
            origin_x + (value[0] - minimum[0]) * scale,
            origin_y - (value[1] - minimum[1]) * scale,
        )

    # Show the PETG cheek only as a subdued reference, then the complete TPU
    # mid-plane on top so every screw and bay remains readable.
    for segment in petg_lines:
        draw.line((point(segment[0]), point(segment[1])), fill=(170, 174, 180), width=4)
    for segment in tpu_lines:
        draw.line((point(segment[0]), point(segment[1])), fill=(38, 132, 68), width=6)

    radius_px = 3.3 * scale
    for index, centre in enumerate(M4_CENTRES, start=1):
        x, y = point(np.asarray(centre))
        draw.ellipse(
            (x - radius_px, y - radius_px, x + radius_px, y + radius_px),
            outline=(215, 36, 48),
            width=4,
        )
        draw.text((x + radius_px + 7, y - 15), f"M4-{index}", fill=(190, 25, 38), font=font(20))

    draw.text(
        (58, 714),
        "TPU: 74.019 × 23.990 × 15.480 mm  |  Robotiq interface-to-tip: 88.019 mm  |  closed TPU gap: 1.5 mm",
        fill=(55, 59, 65),
        font=font(19),
    )
    canvas.save(PNG_PATH)
    print("PETG watertight", petg.is_watertight, "extents", np.round(petg.extents, 3).tolist())
    print("TPU watertight", tpu.is_watertight, "extents", np.round(tpu.extents, 3).tolist())
    print(PNG_PATH)


if __name__ == "__main__":
    main()

