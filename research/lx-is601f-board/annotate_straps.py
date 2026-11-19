#!/usr/bin/env python3
"""Draw strap-resistors-annotated.jpg from strap-resistors-source.jpg.

Needs Pillow and the DejaVu Sans fonts. Run as: python3 annotate_straps.py

Text sizes are chosen so that every label is at least 13 px tall when the
image is shown 850 px wide.
"""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).parent
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
SCALE = 3  # the source crop is enlarged by this factor
# x of each column in the source crop, in source pixels
COLUMN_X = [37, 80, 127, 175, 220, 267, 312, 360, 407]

# (pin, strap name, level, pull-down designator, pull-up designator)
COLUMNS = [
    (70, "DIS_SPIS", 1, "R49", "R50"),
    (71, "EEPROM_MOD", 0, "R51", "R52"),
    (74, "EN_PWRLIGHT", 1, "R65", "R66"),
    (75, "EN_SPIF", 0, "R53", "R54"),
    (76, "DIS_MCU", 1, "R55", "R56"),
    (77, "DISAUTOLOAD", 0, "R57", "R58"),
    (80, "MID29", 1, "R61", "R62"),
    (83, "EN_PHY", 1, "R63", "R64"),
    (85, "SMI_SEL", 1, "R59", "R60"),
]

BLACK = (0, 0, 0)
RED = (170, 0, 0)
GREY = (80, 80, 80)


def main():
    bold = ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 24)
    plain = ImageFont.truetype(str(FONT_DIR / "DejaVuSans.ttf"), 24)
    head = ImageFont.truetype(str(FONT_DIR / "DejaVuSans-Bold.ttf"), 26)

    photo = Image.open(HERE / "strap-resistors-source.jpg").convert("RGB")
    photo = photo.resize((photo.width * SCALE, photo.height * SCALE), Image.LANCZOS)

    line = 31
    y_head = 20
    y_pin = y_head + line + 16
    y_name = y_pin + line  # names sit on two lines, alternating by column
    y_level = y_name + 2 * line
    y_res = y_level + line + 10
    top = y_res + 2 * line + 16
    photo_bottom = top + photo.height
    y_bot = photo_bottom + 14
    y_foot = y_bot + 2 * line + 16
    out = Image.new("RGB", (photo.width, y_foot + line + 20), "white")
    out.paste(photo, (0, top))
    d = ImageDraw.Draw(out)

    d.text((12, y_head), "Upper row: odd designators, pull-down (inferred)", font=head, fill=BLACK)
    d.text((12, y_foot), "Lower row: even designators, pull-up (inferred)", font=head, fill=BLACK)

    for k, (pin, name, level, down, up) in enumerate(COLUMNS):
        x = COLUMN_X[k] * SCALE
        d.text((x, y_pin), f"Pin {pin}", font=bold, fill=BLACK, anchor="ma")
        d.text((x, y_name + (k % 2) * line), name, font=bold, fill=BLACK, anchor="ma")
        d.text((x, y_level), f"= {level}", font=bold, fill=BLACK, anchor="ma")
        for y, ref, fitted in ((y_res, down, level == 0), (y_bot, up, level == 1)):
            colour = RED if fitted else GREY
            d.text((x, y), ref, font=plain, fill=colour, anchor="ma")
            d.text((x, y + line), "fitted" if fitted else "empty", font=plain, fill=colour, anchor="ma")

    out.save(HERE / "strap-resistors-annotated.jpg", quality=90)
    print(out.size)


if __name__ == "__main__":
    main()
