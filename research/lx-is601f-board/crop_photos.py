#!/usr/bin/env python3
"""Cut the area crops out of the source photos in this folder.

Needs Pillow. Run as: python3 crop_photos.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).parent

# output file: (source photo, (left, top, right, bottom) in source pixels)
CROPS = {
    "crop-board-b-power-input.jpg": ("photo-board-b-top.jpg", (1440, 20, 2130, 680)),
    "crop-board-b-switch-ic.jpg": ("photo-board-b-top.jpg", (1360, 416, 1856, 1408)),
    "crop-board-b-magnetics.jpg": ("photo-board-b-top.jpg", (590, 560, 1700, 1520)),
    "crop-board-a-regulator.jpg": ("photo-u4-wide.jpg", (2192, 2060, 3072, 4010)),
    "crop-board-a-u4-right-edge.jpg": ("photo-u4-wide.jpg", (1690, 1620, 2270, 2620)),
    "crop-board-a-power-input.jpg": ("photo-u4-wide.jpg", (1768, 163, 3072, 1745)),
    "crop-board-a-led-esd.jpg": ("photo-u4-wide.jpg", (0, 0, 1020, 1150)),
    "crop-bottom-flash-footprint.jpg": ("photo-bottom-under-u4.jpg", (320, 1395, 1040, 2200)),
    "crop-bottom-strap-array.jpg": ("photo-bottom-under-u4.jpg", (835, 575, 1846, 1373)),
    "crop-poe-module.jpg": ("photo-poe-module.jpg", (616, 112, 2240, 1475)),
    "strap-resistors-source.jpg": ("photo-bottom-under-u4.jpg", (835, 858, 1300, 1382)),
}


def main():
    for name, (source, box) in CROPS.items():
        crop = Image.open(HERE / source).convert("RGB").crop(box)
        crop.save(HERE / name, quality=95)
        print(name, crop.size)


if __name__ == "__main__":
    main()
