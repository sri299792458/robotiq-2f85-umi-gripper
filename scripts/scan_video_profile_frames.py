"""Create sharpness-labelled contact sheets across the full flakes-macro clip."""

from pathlib import Path

import cv2
import numpy as np


VIDEO = Path(r"C:\Users\srini\Downloads\extracted\flakes-macro.mp4")
OUTPUT = Path(
    r"C:\Users\srini\Downloads\extracted\analysis_frames\opencv_geometry\full_scan"
)
SAMPLE_STEP = 15
TILE_SIZE = (384, 216)
GRID = (5, 4)


def sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def labelled_tile(frame, frame_id, fps):
    tile = cv2.resize(frame, TILE_SIZE, interpolation=cv2.INTER_AREA)
    cv2.rectangle(tile, (0, 0), (383, 31), (0, 0, 0), -1)
    cv2.putText(
        tile,
        f"f{frame_id:03d}  {frame_id / fps:4.2f}s  sharp {sharpness(frame):.0f}",
        (7, 22),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return tile


def write_pages(tiles):
    columns, rows = GRID
    page_size = columns * rows
    blank = np.zeros((TILE_SIZE[1], TILE_SIZE[0], 3), np.uint8)
    for page_index, start in enumerate(range(0, len(tiles), page_size)):
        page_tiles = tiles[start : start + page_size]
        page_tiles.extend([blank] * (page_size - len(page_tiles)))
        page_rows = []
        for row in range(rows):
            row_tiles = page_tiles[row * columns : (row + 1) * columns]
            page_rows.append(np.hstack(row_tiles))
        cv2.imwrite(str(OUTPUT / f"full_scan_page_{page_index + 1}.png"), np.vstack(page_rows))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(VIDEO))
    frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = float(capture.get(cv2.CAP_PROP_FPS))
    sample_ids = list(range(0, frame_count, SAMPLE_STEP))
    if sample_ids[-1] != frame_count - 1:
        sample_ids.append(frame_count - 1)
    tiles = []
    for frame_id in sample_ids:
        capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
        ok, frame = capture.read()
        if not ok:
            continue
        tiles.append(labelled_tile(frame, frame_id, fps))
    capture.release()
    write_pages(tiles)
    print("sampled", len(tiles), "frames", sample_ids)


if __name__ == "__main__":
    main()
