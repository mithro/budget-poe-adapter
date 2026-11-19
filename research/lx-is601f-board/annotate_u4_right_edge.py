#!/usr/bin/env python3
"""Draw u4-right-edge-annotated.jpg from photo-u4-macro.jpg.

Needs Pillow and the DejaVu Sans fonts. Run as: python3 annotate_u4_right_edge.py

The crop holds leads 33 to 55 of U4, which run up the right edge of the
package from lead 33 at the bottom corner, and the resistors beside them.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
BOX = (2250, 1780, 3072, 2750)  # left, top, right, bottom in the source photo
SCALE = 2
LEAD_33_Y = 2668  # centre of lead 33 in the source photo
PITCH = 38.5  # lead pitch in source pixels
LEAD_X = 2490  # package edge in the source photo
LABELS = {33: "33", 46: "46: no trace", 47: "47: no trace", 49: "49", 50: "50", 54: "54", 55: "55"}
YELLOW = (255, 230, 0)


def main():
    font = ImageFont.truetype(FONT, 34)
    photo = Image.open(HERE / "photo-u4-macro.jpg").convert("RGB").crop(BOX)
    photo = photo.resize((photo.width * SCALE, photo.height * SCALE), Image.LANCZOS)
    d = ImageDraw.Draw(photo)
    for lead, text in LABELS.items():
        y = (LEAD_33_Y - (lead - 33) * PITCH - BOX[1]) * SCALE
        x = (LEAD_X - BOX[0]) * SCALE
        d.line((x - 60, y, x, y), fill=YELLOW, width=4)
        d.text((x - 70, y), text, font=font, fill=YELLOW, anchor="rm", stroke_width=3, stroke_fill=(0, 0, 0))
    photo.save(HERE / "u4-right-edge-annotated.jpg", quality=90)
    print(photo.size)


if __name__ == "__main__":
    main()
