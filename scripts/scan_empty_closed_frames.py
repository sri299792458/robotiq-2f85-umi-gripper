"""Scan all seven Skild clips for empty, fully closed Robotiq finger pairs."""

from pathlib import Path

import cv2
import numpy as np


ROOT = Path(r"C:\Users\srini\Downloads\extracted")
OUTPUT = ROOT / "analysis_frames" / "opencv_geometry" / "closure_scan"
VIDEOS = tuple(sorted(ROOT.glob("*.mp4")))
STEP = 10  # 0.333 s at the observed 30 fps.
TILE = (384, 216)
GRID = (5, 4)


def sharpness(image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def labelled(frame, frame_id, fps):
    tile = cv2.resize(frame, TILE, interpolation=cv2.INTER_AREA)
    cv2.rectangle(tile, (0, 0), (TILE[0], 28), (0, 0, 0), -1)
    cv2.putText(
        tile,
        f"f{frame_id:03d} {frame_id / fps:4.2f}s S{sharpness(frame):.0f}",
        (6, 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1,
        cv2.LINE_AA,
    )
    return tile


def pages(tiles, stem):
    columns, rows = GRID
    page_size = columns * rows
    blank = np.zeros((TILE[1], TILE[0], 3), np.uint8)
    for page_number, start in enumerate(range(0, len(tiles), page_size), 1):
        page = tiles[start : start + page_size]
        page.extend([blank] * (page_size - len(page)))
        image_rows = [
            np.hstack(page[row * columns : (row + 1) * columns])
            for row in range(rows)
        ]
        cv2.imwrite(str(OUTPUT / f"{stem}_page_{page_number}.png"), np.vstack(image_rows))


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for video in VIDEOS:
        capture = cv2.VideoCapture(str(video))
        fps = float(capture.get(cv2.CAP_PROP_FPS))
        frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        ids = list(range(0, frame_count, STEP))
        if ids[-1] != frame_count - 1:
            ids.append(frame_count - 1)
        tiles = []
        for frame_id in ids:
            capture.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f"Could not read {video.name} frame {frame_id}")
            tiles.append(labelled(frame, frame_id, fps))
        capture.release()
        pages(tiles, video.stem)
        print(video.name, "frames", ids)


if __name__ == "__main__":
    main()
