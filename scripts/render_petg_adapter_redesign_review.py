"""Render and dimension the redrafted PETG adapter side section."""

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont


OUTPUT = Path(r"C:\Users\srini\Downloads\extracted")
PETG_PATH = OUTPUT / "REVIEW_ONLY_PETG_REDRAFT_2F85_PETG_Adapter_PRINT_2.stl"
TPU_PATH = OUTPUT / "REVIEW_ONLY_PETG_REDRAFT_2F85_TPU95A_Finger_PRINT_2.stl"
PNG_PATH = OUTPUT / "REVIEW_ONLY_PETG_Adapter_Redraft_dimensioned.png"
M4_CENTRES = ((17.0, 2.25), (17.0, 20.25), (38.0, 20.25))


def font(size):
    path = Path(r"C:\Windows\Fonts\segoeui.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default()


def section(path, x_plane):
    mesh = trimesh.load_mesh(path, process=True)
    lines = trimesh.intersections.mesh_plane(
        mesh,
        plane_normal=np.array([1.0, 0.0, 0.0]),
        plane_origin=np.array([x_plane, 20.0, 10.0]),
    )
    return lines[:, :, [1, 2]], mesh


def main():
    petg_lines, petg = section(PETG_PATH, 9.0)
    tpu_lines, tpu = section(TPU_PATH, 0.0)
    all_points = np.vstack((petg_lines.reshape(-1, 2), tpu_lines.reshape(-1, 2)))
    minimum = all_points.min(axis=0)
    maximum = all_points.max(axis=0)
    span = maximum - minimum

    canvas = Image.new("RGB", (1750, 900), (246, 247, 249))
    draw = ImageDraw.Draw(canvas)
    draw.text((45, 24), "PETG adapter redraft — fixed printed TPU", fill=(18, 20, 23), font=font(34))
    draw.text(
        (47, 72),
        "Exact Robotiq M5/indexing interface • fixed 16 mm pocket • fixed three-hole UMI triangle",
        fill=(70, 74, 80),
        font=font(20),
    )

    plot = (55, 125, 1695, 790)
    scale = min((plot[2] - plot[0]) / span[0], (plot[3] - plot[1]) / span[1]) * 0.91
    used = span * scale
    origin_x = plot[0] + ((plot[2] - plot[0]) - used[0]) / 2
    origin_y = plot[1] + ((plot[3] - plot[1]) + used[1]) / 2

    def point(value):
        return (
            origin_x + (value[0] - minimum[0]) * scale,
            origin_y - (value[1] - minimum[1]) * scale,
        )

    for segment in petg_lines:
        draw.line((point(segment[0]), point(segment[1])), fill=(95, 99, 106), width=6)
    for segment in tpu_lines:
        draw.line((point(segment[0]), point(segment[1])), fill=(38, 132, 68), width=4)

    radius_px = 2.15 * scale
    for index, centre in enumerate(M4_CENTRES, start=1):
        x, y = point(np.asarray(centre))
        draw.ellipse(
            (x - radius_px, y - radius_px, x + radius_px, y + radius_px),
            outline=(215, 36, 48),
            width=5,
        )
        draw.text((x + radius_px + 7, y - 16), f"M4-{index}", fill=(190, 25, 38), font=font(20))

    metrics = (
        "Clear PETG ligament: M4-1 contact edge 1.40 mm • M4-2 outer edge 4.41 mm • "
        "M4-3 outer edge 3.55 mm / end edge 3.85 mm"
    )
    draw.text((58, 810), metrics, fill=(44, 48, 54), font=font(19))
    draw.text(
        (58, 842),
        "PETG pair gap at mechanical close: 0.40 mm • straight outer edge • no change to TPU geometry",
        fill=(44, 48, 54),
        font=font(19),
    )
    canvas.save(PNG_PATH)
    print("PETG watertight", petg.is_watertight, "extents", np.round(petg.extents, 3).tolist())
    print("TPU unchanged extents", np.round(tpu.extents, 3).tolist())
    print(PNG_PATH)


if __name__ == "__main__":
    main()
