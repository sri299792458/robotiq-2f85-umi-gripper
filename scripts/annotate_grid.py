from __future__ import annotations

import argparse
from pathlib import Path

import cv2


def main() -> None:
    parser = argparse.ArgumentParser(description="Overlay a pixel-coordinate grid on an image.")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--spacing", type=int, default=50)
    args = parser.parse_args()

    image = cv2.imread(str(args.input), cv2.IMREAD_COLOR)
    if image is None:
        raise FileNotFoundError(args.input)

    height, width = image.shape[:2]
    color = (0, 220, 255)
    for x in range(0, width, args.spacing):
        cv2.line(image, (x, 0), (x, height - 1), color, 1, cv2.LINE_AA)
        cv2.putText(image, str(x), (x + 3, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)
    for y in range(0, height, args.spacing):
        cv2.line(image, (0, y), (width - 1, y), color, 1, cv2.LINE_AA)
        cv2.putText(image, str(y), (3, y + 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45, color, 1, cv2.LINE_AA)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(args.output), image):
        raise RuntimeError(f"Failed to write {args.output}")


if __name__ == "__main__":
    main()
