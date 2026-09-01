"""Extract close-pose Skild frames for pairwise inner-rail measurement.

The open-profile trace is not sufficient to determine how the two installed
fingers relate at closure.  This script samples the flakes-macro interval where
both jaws surround the sandwich, labels each full-resolution crop, and writes a
contact sheet plus the sharpest individual frame for manual/curve inspection.
"""

from pathlib import Path

import cv2
import numpy as np


VIDEO = Path(r"C:\Users\srini\Downloads\extracted\flakes-macro.mp4")
EMPTY_CLOSED_VIDEO = Path(r"C:\Users\srini\Downloads\extracted\lab-cup.mp4")
OUTPUT = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\closed_pair"
)
FRAME_IDS = tuple(range(108, 139, 3))


def sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def crop_pair(frame):
    height, width = frame.shape[:2]
    # The gripping pair occupies the upper-centre/right area in this interval.
    return frame[
        int(0.00 * height) : int(0.78 * height),
        int(0.32 * width) : int(0.99 * width),
    ]


def label(image, frame_id, fps):
    result = image.copy()
    cv2.rectangle(result, (0, 0), (result.shape[1], 54), (0, 0, 0), -1)
    cv2.putText(
        result,
        f"f{frame_id}  {frame_id / fps:.3f}s  sharp={sharpness(image):.1f}",
        (14, 38),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
        cv2.LINE_AA,
    )
    return result


def enhance_pair(image):
    """Tight, geometry-preserving views of the central Robotiq finger pair."""

    # Coordinates are in crop_pair output.  This retains both three-screw
    # adapters, both ribbed fingers, and their loaded sandwich contact.
    tight = image[15:600, 20:700]
    enlarged = cv2.resize(tight, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4)
    lab = cv2.cvtColor(enlarged, cv2.COLOR_BGR2LAB)
    lightness, a_channel, b_channel = cv2.split(lab)
    lightness = cv2.createCLAHE(clipLimit=2.2, tileGridSize=(12, 12)).apply(lightness)
    enhanced = cv2.cvtColor(
        cv2.merge((lightness, a_channel, b_channel)), cv2.COLOR_LAB2BGR
    )
    gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 45, 130)
    return tight, enhanced, edges


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(VIDEO))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    crops = []
    scores = []
    for frame_id in FRAME_IDS:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not read frame {frame_id}")
        crop = crop_pair(frame)
        score = sharpness(crop)
        crops.append((frame_id, crop))
        scores.append((score, frame_id, crop))
        cv2.imwrite(str(OUTPUT / f"closed_pair_f{frame_id:03d}.png"), crop)
        if frame_id in (108, 111, 114):
            tight, enhanced, edges = enhance_pair(crop)
            cv2.imwrite(str(OUTPUT / f"closed_pair_f{frame_id:03d}_tight.png"), tight)
            cv2.imwrite(
                str(OUTPUT / f"closed_pair_f{frame_id:03d}_enhanced_3x.png"),
                enhanced,
            )
            cv2.imwrite(
                str(OUTPUT / f"closed_pair_f{frame_id:03d}_edges_3x.png"), edges
            )
    capture.release()

    tile_width, tile_height = 640, 420
    tiles = []
    for frame_id, crop in crops:
        tile = cv2.resize(crop, (tile_width, tile_height), interpolation=cv2.INTER_AREA)
        tiles.append(label(tile, frame_id, fps))
    blank = np.zeros((tile_height, tile_width, 3), np.uint8)
    while len(tiles) % 3:
        tiles.append(blank)
    rows = [np.hstack(tiles[index : index + 3]) for index in range(0, len(tiles), 3)]
    cv2.imwrite(str(OUTPUT / "closed_pair_contact_sheet.png"), np.vstack(rows))

    score, frame_id, crop = max(scores)
    cv2.imwrite(str(OUTPUT / "closed_pair_sharpest.png"), crop)
    print(f"fps={fps:.3f} sampled={FRAME_IDS}")
    print(f"sharpest=f{frame_id} score={score:.3f}")

    # The centre gripper is empty and fully closed at the beginning of the
    # lab-cup clip.  Unlike the sandwich interval above, these frames provide
    # the unloaded pair relationship needed for the CAD assembly check.
    capture = cv2.VideoCapture(str(EMPTY_CLOSED_VIDEO))
    empty_fps = float(capture.get(cv2.CAP_PROP_FPS))
    empty_ids = tuple(range(0, 31, 3))
    empty_tiles = []
    empty_scores = []
    for empty_id in empty_ids:
        capture.set(cv2.CAP_PROP_POS_FRAMES, empty_id)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not read empty-closed frame {empty_id}")
        height, width = frame.shape[:2]
        crop = frame[0 : int(0.67 * height), int(0.35 * width) : int(0.66 * width)]
        score = sharpness(crop)
        empty_scores.append((score, empty_id, crop))
        cv2.imwrite(str(OUTPUT / f"empty_closed_f{empty_id:03d}.png"), crop)
        tile = cv2.resize(crop, (480, 520), interpolation=cv2.INTER_AREA)
        empty_tiles.append(label(tile, empty_id, empty_fps))
    capture.release()
    blank = np.zeros((520, 480, 3), np.uint8)
    while len(empty_tiles) % 4:
        empty_tiles.append(blank)
    rows = [
        np.hstack(empty_tiles[index : index + 4])
        for index in range(0, len(empty_tiles), 4)
    ]
    cv2.imwrite(str(OUTPUT / "empty_closed_contact_sheet.png"), np.vstack(rows))
    empty_score, empty_id, empty_crop = max(empty_scores)
    cv2.imwrite(str(OUTPUT / "empty_closed_sharpest.png"), empty_crop)
    tight, enhanced, edges = enhance_pair(empty_crop)
    cv2.imwrite(str(OUTPUT / "empty_closed_sharpest_enhanced_3x.png"), enhanced)
    cv2.imwrite(str(OUTPUT / "empty_closed_sharpest_edges_3x.png"), edges)
    print(
        f"empty_closed_fps={empty_fps:.3f} sampled={empty_ids} "
        f"sharpest=f{empty_id} score={empty_score:.3f}"
    )

    # A second gripper remains idle at the upper-right of the same clip.  Its
    # jaws are empty and substantially closer than the centre working gripper,
    # making it the primary unloaded-closure reference.
    capture = cv2.VideoCapture(str(EMPTY_CLOSED_VIDEO))
    idle_tiles = []
    idle_scores = []
    for empty_id in empty_ids:
        capture.set(cv2.CAP_PROP_POS_FRAMES, empty_id)
        ok, frame = capture.read()
        if not ok:
            raise RuntimeError(f"Could not read idle-closed frame {empty_id}")
        height, width = frame.shape[:2]
        crop = frame[0 : int(0.60 * height), int(0.60 * width) : width]
        score = sharpness(crop)
        idle_scores.append((score, empty_id, crop))
        cv2.imwrite(str(OUTPUT / f"idle_empty_closed_f{empty_id:03d}.png"), crop)
        tile = cv2.resize(crop, (560, 480), interpolation=cv2.INTER_AREA)
        idle_tiles.append(label(tile, empty_id, empty_fps))
    capture.release()
    blank = np.zeros((480, 560, 3), np.uint8)
    while len(idle_tiles) % 3:
        idle_tiles.append(blank)
    rows = [
        np.hstack(idle_tiles[index : index + 3])
        for index in range(0, len(idle_tiles), 3)
    ]
    cv2.imwrite(
        str(OUTPUT / "idle_empty_closed_contact_sheet.png"), np.vstack(rows)
    )
    idle_score, idle_id, idle_crop = max(idle_scores)
    cv2.imwrite(str(OUTPUT / "idle_empty_closed_sharpest.png"), idle_crop)
    enlarged = cv2.resize(
        idle_crop, None, fx=3, fy=3, interpolation=cv2.INTER_LANCZOS4
    )
    blur = cv2.GaussianBlur(enlarged, (0, 0), 1.0)
    enhanced = cv2.addWeighted(enlarged, 1.6, blur, -0.6, 0)
    cv2.imwrite(
        str(OUTPUT / "idle_empty_closed_sharpest_enhanced_3x.png"), enhanced
    )
    print(f"idle_empty_closed_sharpest=f{idle_id} score={idle_score:.3f}")


if __name__ == "__main__":
    main()
