#!/usr/bin/env python3
"""Build the web-size photos, thumbnails and annotated callouts for README.md.

Usage: python3 make_photos.py SRC_DIR
SRC_DIR holds the album originals named 01.jpg .. 34.jpg (album order).
Output is written next to this script. EXIF (including GPS) is stripped.
Needs Pillow.
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_R = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'

# Callouts: photo -> (title, [(targets, label, badge)]).
# Positions are percentages of the photo's width and height. Each target gets a small
# ring; a numbered badge sits at `badge` with a leader line to every target, so badges
# can be put on empty background instead of over markings.
CALLOUTS = {
    '04': ('Board A, top, heatsink removed', [
        ([(36, 56)], 'U4 YT9215SCH switch IC', (36, 92)),
        ([(96, 14)], 'Removed heatsink (thermal pad residue)', (86, 8)),
        ([(51, 29)], 'U12 SFP host connector, no cage', (51, 12)),
        ([(20, 30)], 'Single RJ45', (20, 12)),
        ([(81, 60)], 'RJ45 block', (95, 60)),
        ([(60, 40)], 'G2401PR magnetics (date 2632)', (68, 12)),
        ([(19, 52)], 'PU1 SCT2622 3.3 V buck', (5, 50)),
        ([(23, 66)], 'L2 "701" input inductor', (5, 66)),
        ([(20, 78)], 'J2 POWER2 input connector', (8, 90)),
        ([(33, 76)], 'Blue disc capacitors (x3)', (26, 92)),
        ([(71, 68)], 'PoE module header, empty', (75, 92)),
    ]),
    '08': ('Board B, top: PoE module + SFP', [
        ([(61, 44)], 'U4 YT9215SCH switch IC', (66, 8)),
        ([(52, 27)], 'PoE PSE module, U1 "2184A"', (48, 8)),
        ([(30, 65)], 'SFP cage over U12', (30, 88)),
        ([(17, 40)], 'RJ45 block', (8, 8)),
        ([(88, 62)], 'Single RJ45', (92, 88)),
        ([(84, 43)], 'PU1 SCT2622 3.3 V buck', (95, 35)),
        ([(78, 29)], 'L2 "701" input inductor', (82, 8)),
        ([(81, 22)], 'J2 power input', (94, 18)),
        ([(61, 56)], 'G2401PR magnetics (date 2523A)', (58, 88)),
        ([(63, 73)], 'Silkscreen LX-IS601F V2.0', (76, 88)),
    ]),
    '06': ('Board A, U4 close-up', [
        ([(62, 54)], 'U4 YT9215SCH, lot VKTP18287', (68, 66)),
        ([(38, 53)], 'Pin-1 dimple', (13, 70)),
        ([(49, 13)], 'Y6 25.000 MHz crystal', (62, 20)),
        ([(87, 40), (87, 42), (87, 44), (87, 46)], 'R44/R89/R92/R93: SPI flash lines (SPF0)', (96, 52)),
        ([(87, 10)], 'L2 "701" input inductor', (74, 7)),
        ([(10, 12)], 'ED1, one of the SOT-23-6 ESD arrays', (5, 22)),
        ([(84, 27)], '"4R7" inductor', (72, 26)),
        ([(35, 93)], 'G2401PR magnetics', (55, 92)),
    ]),
    '21': ('Board A, port edge, no PoE module', [
        ([(31.5, 46), (46.5, 46), (66.4, 46)], 'PoE module header, 8 holes, empty', (50, 6)),
        ([(76, 80)], 'POW / FX LED resistor pads (RJ7-RJ18)', (94, 82)),
        ([(77, 33)], 'LED6 through-hole footprint, empty', (90, 22)),
        ([(79, 42)], 'LED7, LED8', (94, 45)),
        ([(61, 60)], 'G2401PR magnetics (date 2632)', (74, 55)),
        ([(25, 78), (42, 81), (53, 84)], 'ESD arrays ED2, ED1, ED10', (47, 73)),
    ]),
    '26': ('Bottom side, under U4', [
        ([(44, 42)], 'U6 8-pin footprint, unpopulated', (44, 20)),
        ([(73, 70)], 'U10 HK24C08 I2C EEPROM', (88, 60)),
        ([(45, 58)], 'Tinned via field (probably under U4)', (22, 24)),
        ([(37, 36)], 'Small tinned via grid', (32, 12)),
        ([(57, 89), (80, 89)], 'Port-side row of 1206 capacitors', (65, 79)),
    ]),
    '32': ('Board B, PoE PSE module', [
        ([(55, 72)], 'U1 "2184A 533AQ1H" (PSE, unidentified)', (45, 79)),
        ([(40, 61), (54, 50), (68, 50), (77, 62)], 'R8/R12/R13/R14: R250 (0.25 ohm) sense', (61, 42)),
        ([(46, 33), (57, 33), (68, 33), (79, 33)], 'D1/D3/D5/D7 diodes "RGS 2616"', (62, 9)),
        ([(43, 25)], 'PIN1: 8-pin module header', (30, 9)),
        ([(15, 90)], 'U4 YT9215SCH (lot VKJC09324)', (10, 78)),
        ([(55, 90)], 'Y6 25 MHz crystal', (44, 84)),
    ]),
}


def strip(im):
    """Return an upright copy with no EXIF/GPS."""
    im = ImageOps.exif_transpose(im)
    out = Image.new('RGB', im.size)
    out.paste(im)
    return out


def annotate(im, title, points, height=1000):
    im = im.copy()
    im.thumbnail((10000, height))
    w, h = im.size
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 24)
    red = (220, 20, 20)
    P = lambda xy: (xy[0] * w / 100, xy[1] * h / 100)
    for targets, _, badge in points:          # leader lines first, under everything
        bx, by = P(badge)
        for t in targets:
            tx, ty = P(t)
            d.line((bx, by, tx, ty), fill='white', width=5)
            d.line((bx, by, tx, ty), fill=red, width=3)
    for targets, _, _ in points:
        for t in targets:
            tx, ty = P(t)
            d.ellipse((tx - 9, ty - 9, tx + 9, ty + 9), outline='white', width=5)
            d.ellipse((tx - 9, ty - 9, tx + 9, ty + 9), outline=red, width=3)
    r = 18
    for i, (_, _, badge) in enumerate(points, 1):
        bx, by = P(badge)
        d.ellipse((bx - r, by - r, bx + r, by + r), fill=red, outline='white', width=3)
        d.text((bx, by), str(i), font=f, fill='white', anchor='mm')
    fl = ImageFont.truetype(FONT_R, 22)
    pw = max(d.textlength(lab, font=fl) for _, lab, _ in points) + 110
    pw = int(max(pw, d.textlength(title, font=ImageFont.truetype(FONT, 26)) + 50))
    out = Image.new('RGB', (w + pw, h), (250, 250, 248))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    d.text((w + 24, 24), title, font=ImageFont.truetype(FONT, 26), fill=(30, 30, 30))
    y = 84
    for i, (_, label, _) in enumerate(points, 1):
        d.ellipse((w + 24, y, w + 56, y + 32), fill=red)
        d.text((w + 40, y + 16), str(i), font=ImageFont.truetype(FONT, 18), fill='white', anchor='mm')
        d.text((w + 70, y + 4), label, font=fl, fill=(30, 30, 30))
        y += 48
    return out


def main(src):
    for sub in ('web', 'thumbs', 'annotated'):
        os.makedirs(os.path.join(HERE, sub), exist_ok=True)
    for n in range(1, 35):
        key = f'{n:02d}'
        im = strip(Image.open(os.path.join(src, key + '.jpg')))
        web = im.copy(); web.thumbnail((1600, 1600))
        web.save(os.path.join(HERE, 'web', key + '.jpg'), quality=85, optimize=True)
        th = im.copy(); th.thumbnail((240, 240))
        th.save(os.path.join(HERE, 'thumbs', key + '.jpg'), quality=82, optimize=True)
        if key in CALLOUTS:
            title, pts = CALLOUTS[key]
            annotate(im, title, pts).save(os.path.join(HERE, 'annotated', key + '.jpg'), quality=85, optimize=True)


if __name__ == '__main__':
    main(sys.argv[1])
