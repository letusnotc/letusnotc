#!/usr/bin/env python3
"""One-off: turn source-photo.png into portrait.txt, the ASCII art cards.py draws in the header.
Needs Pillow (pip install Pillow). Rerun only when the photo changes; the daily workflow just reads portrait.txt.
"""
import os
import sys

from PIL import Image, ImageOps

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
COLS, ROWS = 80, 40  # characters are about twice as tall as wide, so half the rows keeps the photo square
RAMP = " .:-=+*#%@"  # light to dark


def to_ascii(path, cols=COLS, rows=ROWS):
    img = ImageOps.autocontrast(Image.open(path).convert("L")).resize((cols, rows), Image.LANCZOS)
    px = img.load()
    return ["".join(RAMP[min(len(RAMP) - 1, (255 - px[x, y]) * len(RAMP) // 256)] for x in range(cols)).rstrip()
            for y in range(rows)]


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "source-photo.png")
    lines = to_ascii(src)
    assert len(lines) == ROWS and any(l.strip() for l in lines)
    with open(os.path.join(ROOT, "portrait.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))
