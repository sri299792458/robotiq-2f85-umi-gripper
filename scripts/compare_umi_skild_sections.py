"""Render measured mid-plane sections of the source UMI and current Skild finger.

This is a reference/diagnostic tool.  It does not modify any CAD model.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageFont


REFERENCE_DIR = Path(r"C:\Users\srini\Downloads\extracted\reference_umi")
UMI_STL = REFERENCE_DIR / "UMI-Soft-Gripper-Finger.stl"
SKILD_STL = Path(r"C:\Users\srini\Downloads\extracted\2F85_TPU95A_Finger_PRINT_2.stl")
OUTPUT_PNG = REFERENCE_DIR / "UMI_vs_current_Skild_side_sections.png"


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\arial.ttf"),
    )
    for candidate in candidates:
        if candidate.exists():
            return ImageFont.truetype(str(candidate), size=size)
    return ImageFont.load_default()


def section_segments(
    path: Path,
    plane_origin: tuple[float, float, float],
    plane_normal: tuple[float, float, float],
    horizontal_axis: int,
    vertical_axis: int,
    horizontal_sign: float = 1.0,
    vertical_sign: float = 1.0,
) -> tuple[np.ndarray, np.ndarray]:
    mesh = trimesh.load_mesh(path, process=False)
    lines = trimesh.intersections.mesh_plane(
        mesh,
        plane_normal=np.asarray(plane_normal, dtype=float),
        plane_origin=np.asarray(plane_origin, dtype=float),
    )
    points = np.empty((len(lines), 2, 2), dtype=float)
    points[:, :, 0] = lines[:, :, horizontal_axis] * horizontal_sign
    points[:, :, 1] = lines[:, :, vertical_axis] * vertical_sign
    return points, np.asarray(mesh.extents, dtype=float)


def draw_panel(
    canvas: Image.Image,
    box: tuple[int, int, int, int],
    title: str,
    subtitle: str,
    segments: np.ndarray,
    line_color: tuple[int, int, int],
    forced_height_per_length: float | None = None,
) -> None:
    draw = ImageDraw.Draw(canvas)
    left, top, right, bottom = box
    draw.rounded_rectangle(box, radius=18, fill=(250, 250, 250), outline=(210, 210, 210), width=2)
    draw.text((left + 24, top + 18), title, fill=(20, 20, 20), font=font(28))
    draw.text((left + 24, top + 55), subtitle, fill=(85, 85, 85), font=font(18))

    plot = (left + 28, top + 100, right - 28, bottom - 28)
    p_left, p_top, p_right, p_bottom = plot
    mins = segments.reshape(-1, 2).min(axis=0)
    maxs = segments.reshape(-1, 2).max(axis=0)
    span = np.maximum(maxs - mins, 1e-9)

    available_w = p_right - p_left
    available_h = p_bottom - p_top
    if forced_height_per_length is None:
        scale = min(available_w / span[0], available_h / span[1])
        sx = sy = scale
    else:
        sx = available_w / span[0]
        target_height = span[0] * forced_height_per_length
        sy = min(available_h / span[1], target_height / span[1] * sx)

    used_w = span[0] * sx
    used_h = span[1] * sy
    offset_x = p_left + (available_w - used_w) / 2
    offset_y = p_top + (available_h - used_h) / 2

    def screen(point: np.ndarray) -> tuple[float, float]:
        x = offset_x + (point[0] - mins[0]) * sx
        y = offset_y + used_h - (point[1] - mins[1]) * sy
        return float(x), float(y)

    for segment in segments:
        draw.line((screen(segment[0]), screen(segment[1])), fill=line_color, width=3)


def main() -> None:
    umi, umi_extents = section_segments(
        UMI_STL,
        plane_origin=(20.0, -12.9, -61.0),
        plane_normal=(0.0, 1.0, 0.0),
        horizontal_axis=2,
        vertical_axis=0,
        horizontal_sign=-1.0,
    )
    skild, skild_extents = section_segments(
        SKILD_STL,
        plane_origin=(0.0, 57.0, 18.0),
        plane_normal=(1.0, 0.0, 0.0),
        horizontal_axis=1,
        vertical_axis=2,
    )

    canvas = Image.new("RGB", (1600, 1000), (238, 240, 243))
    draw = ImageDraw.Draw(canvas)
    draw.text((48, 25), "Original UMI soft finger vs current Skild reconstruction", fill=(15, 18, 22), font=font(36))
    draw.text(
        (50, 72),
        "Mid-plane sections from the actual STL meshes; equal scale within each panel.",
        fill=(70, 74, 80),
        font=font(20),
    )

    draw_panel(
        canvas,
        (40, 120, 780, 950),
        "Original UMI source CAD",
        f"Length {umi_extents[2]:.2f} mm | side height {umi_extents[0]:.2f} mm | width {umi_extents[1]:.2f} mm",
        umi,
        (18, 18, 18),
    )
    draw_panel(
        canvas,
        (820, 120, 1560, 950),
        "Current video-derived reconstruction",
        f"Length {skild_extents[1]:.2f} mm | side height {skild_extents[2]:.2f} mm | width {skild_extents[0]:.2f} mm",
        skild,
        (18, 18, 18),
    )

    canvas.save(OUTPUT_PNG)
    print(OUTPUT_PNG)


if __name__ == "__main__":
    main()
