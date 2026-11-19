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
    "crop-board-b-magnetics.jpg": ("photo-board-b-top.jpg", (704, 560, 1700, 1520)),
    "crop-board-a-regulator.jpg": ("photo-u4-wide.jpg", (1877, 1687, 2980, 4080)),
    "crop-board-a-power-input.jpg": ("photo-u4-wide.jpg", (1768, 163, 3072, 1768)),
    "crop-board-a-led-esd.jpg": ("photo-u4-wide.jpg", (0, 0, 680, 1150)),
    "crop-bottom-eeprom-flash.jpg": ("photo-bottom-under-u4.jpg", (266, 573, 1884, 2020)),
    "crop-poe-module.jpg": ("photo-poe-module.jpg", (616, 112, 2240, 1475)),
    "crop-u4-right-edge.jpg": ("photo-u4-macro.jpg", (2200, 1400, 3072, 2760)),
}


def main():
    for name, (source, box) in CROPS.items():
        crop = Image.open(HERE / source).convert("RGB").crop(box)
        crop.save(HERE / name, quality=90)
        print(name, crop.size)


if __name__ == "__main__":
    main()
