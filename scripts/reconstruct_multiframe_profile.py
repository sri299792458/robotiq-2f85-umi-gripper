"""Align a short flakes-macro burst to recover a cleaner finger side profile."""

import json
from pathlib import Path

import cv2
import numpy as np


VIDEO = Path(r"C:\Users\srini\Downloads\extracted\flakes-macro.mp4")
OUTPUT = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\multiframe"
)
ROI = (880, 80, 1080, 460)  # Full-frame left jaw, with alignment margin.
FRAME_IDS = range(0, 4)
REFERENCE_FRAME = 0

# Each seed is deliberately placed well inside one observed opening.  The
# rectangles are only guard bands: pixel connectivity determines the contour.
# They prevent the PETG shadow above bay 0 and the dark right-hand background
# beside the TPU rail from entering a bay component.
BAY_SEEDS = (
    {"index": 0, "seed": (590, 180), "guard": (470, 70, 680, 275)},
    {"index": 1, "seed": (470, 400), "guard": (225, 255, 675, 600)},
    {"index": 2, "seed": (440, 690), "guard": (225, 475, 655, 1035)},
    {"index": 3, "seed": (470, 1070), "guard": (275, 745, 630, 1435)},
    {"index": 4, "seed": (475, 1440), "guard": (340, 1110, 590, 1725)},
    {"index": 5, "seed": (485, 1760), "guard": (405, 1500, 550, 1925)},
)

# User-corrected hard constraints, in the 880 x 1960 distal image.  Order is
# outer top, inner top, inner bottom, outer bottom.  Bays 2-5 remain automatic
# traces and are not altered by these overrides.
MANUAL_TOP_BAYS = {
    0: [(304, 74), (677, 75), (655, 229), (266, 243)],
    1: [(260, 320), (654, 290), (640, 430), (246, 566)],
}

# Same-frame screw centres expressed in the distal crop coordinate system.
# The first two are above the crop, hence their negative Y values.  They map
# to the accepted 18 mm root pair and the distal outer screw 21 mm away.
CALIBRATION_SCREWS_PX = [(216, -168), (616, -72), (120, 296)]
CALIBRATION_SCREWS_YZ_MM = [(10.0, 3.0), (10.0, 21.0), (31.0, 3.0)]


def read_frames():
    capture = cv2.VideoCapture(str(VIDEO))
    frames = {}
    for frame_id in FRAME_IDS:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not read frame {frame_id}")
        x0, y0, x1, y1 = ROI
        frames[frame_id] = frame[y0:y1, x0:x1]
    capture.release()
    return frames


def sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def align(reference, moving):
    reference_gray = cv2.cvtColor(reference, cv2.COLOR_BGR2GRAY)
    moving_gray = cv2.cvtColor(moving, cv2.COLOR_BGR2GRAY)
    warp = np.eye(2, 3, dtype=np.float32)
    criteria = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT,
        150,
        1e-7,
    )
    cv2.findTransformECC(
        reference_gray,
        moving_gray,
        warp,
        cv2.MOTION_AFFINE,
        criteria,
        None,
        3,
    )
    return cv2.warpAffine(
        moving,
        warp,
        (reference.shape[1], reference.shape[0]),
        flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP,
        borderMode=cv2.BORDER_REFLECT,
    )


def enlarge(image, scale=4):
    return cv2.resize(
        image, None, fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4
    )


def prepare_distal(image):
    """Crop the same finger region and enhance it without moving any pixels."""

    distal = image[135:380, 55:165]
    distal = cv2.resize(
        distal, None, fx=8, fy=8, interpolation=cv2.INTER_LANCZOS4
    )
    blur = cv2.GaussianBlur(distal, (0, 0), 1.1)
    return cv2.addWeighted(distal, 1.5, blur, -0.5, 0)


def contact_sheet(frames, columns=4):
    tiles = []
    for frame_id, frame in frames.items():
        tile = cv2.resize(frame, (300, 570), interpolation=cv2.INTER_LANCZOS4)
        cv2.putText(
            tile,
            f"frame {frame_id}  sharp {sharpness(frame):.1f}",
            (8, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 255),
            2,
            cv2.LINE_AA,
        )
        tiles.append(tile)
    rows = []
    blank = np.zeros_like(tiles[0])
    for start in range(0, len(tiles), columns):
        row = tiles[start : start + columns]
        row.extend([blank] * (columns - len(row)))
        rows.append(np.hstack(row))
    return np.vstack(rows)


def kmeans_view(image, clusters=8):
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    samples = lab.reshape((-1, 3)).astype(np.float32)
    criteria = (
        cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_MAX_ITER,
        60,
        0.2,
    )
    _, labels, centres = cv2.kmeans(
        samples,
        clusters,
        None,
        criteria,
        10,
        cv2.KMEANS_PP_CENTERS,
    )
    quantized = centres[labels.ravel()].reshape(lab.shape).astype(np.uint8)
    return cv2.cvtColor(quantized, cv2.COLOR_LAB2BGR)


def nearest_foreground(mask, seed, radius=45):
    """Return the closest classified opening pixel to a seed."""

    seed_x, seed_y = seed
    y0 = max(0, seed_y - radius)
    y1 = min(mask.shape[0], seed_y + radius + 1)
    x0 = max(0, seed_x - radius)
    x1 = min(mask.shape[1], seed_x + radius + 1)
    ys, xs = np.nonzero(mask[y0:y1, x0:x1])
    if len(xs) == 0:
        raise RuntimeError(f"No dark opening pixels close to seed {seed}")
    xs = xs + x0
    ys = ys + y0
    distances = (xs - seed_x) ** 2 + (ys - seed_y) ** 2
    closest = int(np.argmin(distances))
    return int(xs[closest]), int(ys[closest])


def seeded_component(mask, seed, guard):
    """Select one connected opening component inside a broad guard rectangle."""

    x0, y0, x1, y1 = guard
    guarded = np.zeros_like(mask)
    guarded[y0:y1, x0:x1] = mask[y0:y1, x0:x1]
    component_seed = nearest_foreground(guarded, seed)
    count, labels, stats, _ = cv2.connectedComponentsWithStats(guarded, 8)
    label = int(labels[component_seed[1], component_seed[0]])
    if label == 0 or label >= count:
        raise RuntimeError(f"Seed {seed} did not select an opening component")
    component = np.where(labels == label, 255, 0).astype(np.uint8)
    area = int(stats[label, cv2.CC_STAT_AREA])
    bounds = tuple(int(value) for value in stats[label, :4])
    return component, area, bounds, component_seed


def infinite_line_intersection(first_start, first_end, second_start, second_end):
    """Intersect two fitted infinite lines, returning floating-point pixels."""

    first_start = np.asarray(first_start, np.float64)
    first_delta = np.asarray(first_end, np.float64) - first_start
    second_start = np.asarray(second_start, np.float64)
    second_delta = np.asarray(second_end, np.float64) - second_start
    system = np.column_stack((first_delta, -second_delta))
    parameters = np.linalg.solve(system, second_start - first_start)
    return first_start + parameters[0] * first_delta


def complete_bay_two_corner(polygons):
    """Recover bay 2's tan lower-left area from its two structural edges.

    The bench visible through this part of the bay is too light/warm for the
    dark-pixel classifier.  Its boundary is nevertheless determined by the
    outer rail and the pale diagonal rib, both of which are visible.  The
    approximate contour supplies two points on the rib, while bay 3 supplies a
    second point on the outer rail.
    """

    bay_two = np.asarray(polygons[2], np.float64)
    bay_three = np.asarray(polygons[3], np.float64)
    if len(bay_two) != 5:
        return polygons, None

    top_right = bay_two[0]
    top_left = bay_two[1]
    rib_midpoint = bay_two[3]
    bottom_right = bay_two[4]
    bay_three_outer = bay_three[np.argmin(bay_three[:, 0])]
    corner = infinite_line_intersection(
        top_left, bay_three_outer, bottom_right, rib_midpoint
    )
    corrected = np.rint(
        np.asarray([top_right, top_left, corner, bottom_right])
    ).astype(np.int32)
    updated = list(polygons)
    updated[2] = corrected.tolist()
    return updated, corrected[2].tolist()


def pchip_slopes(independent, values):
    """Return shape-preserving cubic Hermite slopes for x=f(y)."""

    independent = np.asarray(independent, np.float64)
    values = np.asarray(values, np.float64)
    spacing = np.diff(independent)
    secants = np.diff(values) / spacing
    slopes = np.zeros_like(values)
    for index in range(1, len(values) - 1):
        before = secants[index - 1]
        after = secants[index]
        if before == 0.0 or after == 0.0 or before * after < 0.0:
            slopes[index] = 0.0
        else:
            weight_one = 2.0 * spacing[index] + spacing[index - 1]
            weight_two = spacing[index] + 2.0 * spacing[index - 1]
            slopes[index] = (weight_one + weight_two) / (
                weight_one / before + weight_two / after
            )

    def endpoint_slope(here, neighbour, first_secant, second_secant):
        slope = (
            (2.0 * here + neighbour) * first_secant
            - here * second_secant
        ) / (here + neighbour)
        if slope * first_secant <= 0.0:
            return 0.0
        if first_secant * second_secant < 0.0 and abs(slope) > 3.0 * abs(
            first_secant
        ):
            return 3.0 * first_secant
        return slope

    slopes[0] = endpoint_slope(
        spacing[0], spacing[1], secants[0], secants[1]
    )
    slopes[-1] = endpoint_slope(
        spacing[-1], spacing[-2], secants[-1], secants[-2]
    )
    return slopes


def evaluate_pchip(independent, values, slopes, samples):
    independent = np.asarray(independent, np.float64)
    values = np.asarray(values, np.float64)
    slopes = np.asarray(slopes, np.float64)
    samples = np.asarray(samples, np.float64)
    result = np.empty_like(samples)
    for output_index, sample in enumerate(samples):
        interval = int(np.searchsorted(independent, sample, side="right") - 1)
        interval = max(0, min(interval, len(independent) - 2))
        width = independent[interval + 1] - independent[interval]
        local = (sample - independent[interval]) / width
        h00 = 2.0 * local**3 - 3.0 * local**2 + 1.0
        h10 = local**3 - 2.0 * local**2 + local
        h01 = -2.0 * local**3 + 3.0 * local**2
        h11 = local**3 - local**2
        result[output_index] = (
            h00 * values[interval]
            + h10 * width * slopes[interval]
            + h01 * values[interval + 1]
            + h11 * width * slopes[interval + 1]
        )
    return result


def sample_pchip_rail(anchors, start, end, count=18):
    anchors = np.asarray(sorted(anchors, key=lambda point: point[1]), np.float64)
    rail_y = anchors[:, 1]
    rail_x = anchors[:, 0]
    slopes = pchip_slopes(rail_y, rail_x)
    samples_y = np.linspace(start[1], end[1], count)
    samples_x = evaluate_pchip(rail_y, rail_x, slopes, samples_y)
    points = np.column_stack((samples_x, samples_y))
    points[0] = start
    points[-1] = end
    return points


def bay_from_sampled_sides(outer_side, inner_side):
    """Close two ordered rail segments with straight top and bottom ribs."""

    return np.rint(
        np.vstack(
            (
                outer_side[0],
                inner_side,
                outer_side[-1],
                outer_side[-2:0:-1],
            )
        )
    ).astype(np.int32)


def complete_occluded_top_bays(polygons):
    """Apply manual bays 0-1 and interpolate the two rails through all bays."""

    manual_zero = np.asarray(MANUAL_TOP_BAYS[0], np.float64)
    manual_one = np.asarray(MANUAL_TOP_BAYS[1], np.float64)
    outer_anchors = [manual_zero[0], manual_zero[3], manual_one[0], manual_one[3]]
    inner_anchors = [manual_zero[1], manual_zero[2], manual_one[1], manual_one[2]]
    for bay_points in polygons[2:]:
        bay = np.asarray(bay_points, np.float64)
        outer_anchors.extend((bay[1], bay[2]))
        inner_anchors.extend((bay[0], bay[3]))

    completed = []
    for manual in (manual_zero, manual_one):
        outer_side = sample_pchip_rail(
            outer_anchors, manual[0], manual[3], count=18
        )
        inner_side = sample_pchip_rail(
            inner_anchors, manual[1], manual[2], count=18
        )
        completed.append(bay_from_sampled_sides(outer_side, inner_side))

    updated = list(polygons)
    updated[0] = completed[0].tolist()
    updated[1] = completed[1].tolist()
    return updated, {
        "bay_0_manual_corners_px": MANUAL_TOP_BAYS[0],
        "bay_1_manual_corners_px": MANUAL_TOP_BAYS[1],
        "rail_interpolation": "shape-preserving cubic Hermite through hard anchors",
        "outer_rail_anchors_px": np.rint(outer_anchors).astype(int).tolist(),
        "inner_rail_anchors_px": np.rint(inner_anchors).astype(int).tolist(),
    }


def segment_bay_contours(image):
    """Trace six dark openings using colour classification and connectivity."""

    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    # The TPU rails are pale (L roughly 175-205 here); the openings are dark.
    # A-channel limits remove some warm bench/background leakage while retaining
    # the green-black interiors.  No polygon vertices are placed by hand.
    lightness, channel_a, _ = cv2.split(lab)
    mask = np.where((lightness <= 118) & (channel_a <= 133), 255, 0).astype(
        np.uint8
    )
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    accepted_pixel_mask = np.zeros_like(mask)
    polygons = []
    diagnostics = []
    for spec in BAY_SEEDS:
        index = spec["index"]
        component, area, bounds, component_seed = seeded_component(
            mask, spec["seed"], spec["guard"]
        )
        contours, _ = cv2.findContours(
            component, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        contour = max(contours, key=cv2.contourArea)
        perimeter = cv2.arcLength(contour, True)
        polygon = cv2.approxPolyDP(contour, 0.012 * perimeter, True)
        polygons.append(polygon[:, 0, :].tolist())
        accepted_pixel_mask = cv2.bitwise_or(accepted_pixel_mask, component)
        diagnostic = {
            "index": index,
            "seed": spec["seed"],
            "component_seed": component_seed,
            "guard": spec["guard"],
            "area_px": area,
            "bounds": bounds,
            "polygon_px": polygons[-1],
        }
        diagnostics.append(diagnostic)
        print(
            "bay",
            index,
            "area",
            area,
            "bounds",
            bounds,
            "vertices",
            len(polygons[-1]),
        )

    polygons, bay_two_corner = complete_bay_two_corner(polygons)
    if bay_two_corner is not None:
        diagnostics[2]["rail_rib_intersection_px"] = bay_two_corner
        diagnostics[2]["polygon_px"] = polygons[2]

    polygons, top_bay_extrapolation = complete_occluded_top_bays(polygons)
    for key, value in top_bay_extrapolation.items():
        if key.startswith("bay_0"):
            diagnostics[0][key] = value
        elif key.startswith("bay_1"):
            diagnostics[1][key] = value
        else:
            diagnostics[0].setdefault("global_rail_fit", {})[key] = value
    for diagnostic_index in (0, 1):
        diagnostics[diagnostic_index]["occluded_geometry_extrapolated"] = True
        diagnostics[diagnostic_index]["polygon_px"] = polygons[diagnostic_index]

    overlay = image.copy()
    geometric_mask = accepted_pixel_mask.copy()
    for diagnostic, polygon_points in zip(diagnostics, polygons):
        index = diagnostic["index"]
        polygon = np.asarray(polygon_points, np.int32).reshape((-1, 1, 2))
        if index in (0, 1, 2):
            cv2.fillPoly(geometric_mask, [polygon], 255)
        cv2.drawContours(overlay, [polygon], -1, (0, 0, 255), 5)
        component_seed = tuple(diagnostic["component_seed"])
        cv2.putText(
            overlay,
            str(index),
            component_seed,
            cv2.FONT_HERSHEY_SIMPLEX,
            1.3,
            (0, 0, 255),
            4,
            cv2.LINE_AA,
        )
    rail_fit = diagnostics[0].get("global_rail_fit", {})
    if rail_fit:
        outer_anchors = np.asarray(
            rail_fit["outer_rail_anchors_px"], np.float64
        )
        inner_anchors = np.asarray(
            rail_fit["inner_rail_anchors_px"], np.float64
        )
        outer_points = np.rint(
            sample_pchip_rail(
                outer_anchors,
                outer_anchors[np.argmin(outer_anchors[:, 1])],
                outer_anchors[np.argmax(outer_anchors[:, 1])],
                count=240,
            )
        ).astype(np.int32)
        inner_points = np.rint(
            sample_pchip_rail(
                inner_anchors,
                inner_anchors[np.argmin(inner_anchors[:, 1])],
                inner_anchors[np.argmax(inner_anchors[:, 1])],
                count=240,
            )
        ).astype(np.int32)
        cv2.polylines(overlay, [outer_points], False, (255, 0, 255), 3)
        cv2.polylines(overlay, [inner_points], False, (0, 255, 255), 3)
    return geometric_mask, accepted_pixel_mask, overlay, polygons, diagnostics


def mask_iou(first, second):
    intersection = np.count_nonzero((first > 0) & (second > 0))
    union = np.count_nonzero((first > 0) | (second > 0))
    return float(intersection / union) if union else 0.0


def cad_trace_geometry(diagnostics):
    """Transform the accepted rail endpoints into the Fusion YZ frame."""

    transform = cv2.getAffineTransform(
        np.asarray(CALIBRATION_SCREWS_PX, np.float32),
        np.asarray(CALIBRATION_SCREWS_YZ_MM, np.float32),
    )

    def mapped(points):
        source = np.asarray([points], np.float32)
        result = cv2.transform(source, transform)[0]
        return [
            [round(float(y_value), 3), round(float(z_value), 3)]
            for y_value, z_value in result
        ]

    rail_fit = diagnostics[0]["global_rail_fit"]
    outer_px = rail_fit["outer_rail_anchors_px"]
    inner_px = rail_fit["inner_rail_anchors_px"]
    bay_corners_px = []
    for index in range(6):
        bay_corners_px.append(
            [
                outer_px[2 * index],
                inner_px[2 * index],
                inner_px[2 * index + 1],
                outer_px[2 * index + 1],
            ]
        )
    return {
        "source_size_px": [880, 1960],
        "point_order": [
            "outer top",
            "inner top",
            "inner bottom",
            "outer bottom",
        ],
        "calibration_screws_px": CALIBRATION_SCREWS_PX,
        "calibration_screws_yz_mm": CALIBRATION_SCREWS_YZ_MM,
        "pixel_to_yz_affine": transform.tolist(),
        "outer_opening_rail_yz_mm": mapped(outer_px),
        "inner_opening_rail_yz_mm": mapped(inner_px),
        "bay_corners_yz_mm": [mapped(corners) for corners in bay_corners_px],
    }


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    frames = read_frames()
    cv2.imwrite(str(OUTPUT / "burst_contact_sheet.png"), contact_sheet(frames))

    reference = frames[REFERENCE_FRAME]
    aligned = []
    aligned_by_frame = {}
    for frame_id, frame in frames.items():
        registered = reference if frame_id == REFERENCE_FRAME else align(reference, frame)
        aligned.append(registered.astype(np.float32))
        aligned_by_frame[frame_id] = registered
    stack = np.stack(aligned)
    median = np.median(stack, axis=0).astype(np.uint8)
    mean = np.mean(stack, axis=0).astype(np.uint8)
    sharpest_id = max(frames, key=lambda item: sharpness(frames[item]))

    cv2.imwrite(str(OUTPUT / "aligned_median_4x.png"), enlarge(median))
    cv2.imwrite(str(OUTPUT / "aligned_mean_4x.png"), enlarge(mean))
    cv2.imwrite(
        str(OUTPUT / f"sharpest_frame_{sharpest_id}_4x.png"),
        enlarge(frames[sharpest_id]),
    )
    distal = prepare_distal(aligned_by_frame[sharpest_id])
    cv2.imwrite(str(OUTPUT / "distal_ribs_sharpest_8x.png"), distal)
    cv2.imwrite(str(OUTPUT / "distal_ribs_kmeans.png"), kmeans_view(distal))
    bay_mask, bay_pixel_mask, bay_overlay, _, diagnostics = segment_bay_contours(
        distal
    )
    cv2.imwrite(str(OUTPUT / "distal_bay_mask.png"), bay_mask)
    cv2.imwrite(str(OUTPUT / "distal_bay_pixel_mask.png"), bay_pixel_mask)
    cv2.imwrite(str(OUTPUT / "distal_bay_contours.png"), bay_overlay)
    top_bays_zoom = bay_overlay[45:690, 145:725]
    top_bays_zoom = cv2.resize(
        top_bays_zoom, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_LANCZOS4
    )
    cv2.imwrite(str(OUTPUT / "top_bays_0_1_2_zoom.png"), top_bays_zoom)
    (OUTPUT / "distal_bay_contours.json").write_text(
        json.dumps(diagnostics, indent=2), encoding="utf-8"
    )
    (OUTPUT / "cad_trace_geometry.json").write_text(
        json.dumps(cad_trace_geometry(diagnostics), indent=2), encoding="utf-8"
    )

    frame_masks = {}
    frame_diagnostics = {}
    for frame_id, registered in aligned_by_frame.items():
        frame_distal = prepare_distal(registered)
        frame_mask, _, _, _, frame_info = segment_bay_contours(frame_distal)
        frame_masks[frame_id] = frame_mask
        frame_diagnostics[frame_id] = frame_info
        cv2.imwrite(str(OUTPUT / f"bay_mask_frame_{frame_id}.png"), frame_mask)

    reference_mask = frame_masks[sharpest_id]
    validation = {
        "reference_frame": sharpest_id,
        "frame_iou": {
            str(frame_id): mask_iou(reference_mask, frame_mask)
            for frame_id, frame_mask in frame_masks.items()
        },
        "frames": frame_diagnostics,
    }
    (OUTPUT / "burst_contour_validation.json").write_text(
        json.dumps(validation, indent=2), encoding="utf-8"
    )
    mask_tiles = []
    for frame_id, frame_mask in frame_masks.items():
        tile = cv2.resize(frame_mask, (220, 490), interpolation=cv2.INTER_NEAREST)
        tile = cv2.cvtColor(tile, cv2.COLOR_GRAY2BGR)
        cv2.putText(
            tile,
            f"frame {frame_id}  IoU {validation['frame_iou'][str(frame_id)]:.3f}",
            (6, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.48,
            (0, 0, 255),
            1,
            cv2.LINE_AA,
        )
        mask_tiles.append(tile)
    cv2.imwrite(str(OUTPUT / "burst_bay_mask_comparison.png"), np.hstack(mask_tiles))
    print("sharpest_frame", sharpest_id, sharpness(frames[sharpest_id]))


if __name__ == "__main__":
    main()
