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

# Callouts: photo -> (title, [(x, y, label)]), x/y as fractions of the photo.
CALLOUTS = {
    '04': ('Board A, top, heatsink removed', [
        (0.365, 0.555, 'U4 YT9215SCH switch IC'),
        (0.965, 0.170, 'Removed heatsink (thermal pad residue)'),
        (0.515, 0.290, 'U12 SFP host connector, no cage'),
        (0.195, 0.315, 'Single RJ45 (uplink side)'),
        (0.820, 0.540, 'RJ45 block, ports 1-4'),
        (0.610, 0.410, 'G2401PR magnetics (date 2632)'),
        (0.195, 0.520, 'PU1 SCT2622 3.3 V buck'),
        (0.250, 0.660, 'L2 "701" input inductor'),
        (0.200, 0.765, 'J2 POWER2 input connector'),
        (0.330, 0.780, 'Blue disc capacitors (x3)'),
    ]),
    '08': ('Board B, top: PoE module + SFP', [
        (0.660, 0.405, 'U4 YT9215SCH switch IC'),
        (0.525, 0.275, 'PoE PSE module, U1 "2184A"'),
        (0.290, 0.645, 'SFP cage (U12)'),
        (0.180, 0.375, 'RJ45 block'),
        (0.875, 0.600, 'Single RJ45'),
        (0.850, 0.433, 'PU1 SCT2622 3.3 V buck'),
        (0.790, 0.290, 'L2 "701" input inductor'),
        (0.810, 0.215, 'J2 power input'),
        (0.610, 0.575, 'G2401PR magnetics (date 2523A)'),
        (0.640, 0.790, 'Silkscreen LX-IS601F V2.0'),
    ]),
    '06': ('Board A, U4 close-up', [
        (0.560, 0.555, 'U4 YT9215SCH, lot VKTP18287'),
        (0.300, 0.475, 'Pin-1 dimple (small, lower left)'),
        (0.483, 0.130, 'Y6 25.000 MHz crystal'),
        (0.840, 0.410, 'R44/R89/R92/R93 (debug-pin straps)'),
        (0.830, 0.100, 'L2 "701"'),
        (0.090, 0.110, 'ED1-ED9: SOT-23-6 ESD arrays'),
        (0.880, 0.270, '"4R7" inductor'),
        (0.330, 0.950, 'G2401PR magnetics'),
    ]),
    '21': ('Board A, port edge, no PoE module', [
        (0.600, 0.460, 'PoE module header (8 holes, empty)'),
        (0.800, 0.810, 'POW / FX LED resistor pads'),
        (0.760, 0.290, 'LED6 footprint (empty)'),
        (0.530, 0.590, 'G2401PR magnetics (date 2632)'),
        (0.370, 0.800, 'ESD arrays (ED1, ED2, ED10)'),
    ]),
    '26': ('Bottom side, under U4', [
        (0.417, 0.410, 'U6 8-pin footprint, unpopulated'),
        (0.725, 0.656, 'U10 HK24C08 I2C EEPROM'),
        (0.450, 0.580, 'Via field (likely U4 exposed pad)'),
        (0.250, 0.800, 'Port-side row of 1206 caps'),
    ]),
    '32': ('Board B, PoE PSE module', [
        (0.505, 0.745, 'U1 "2184A 533AQ1H" (PSE, unidentified)'),
        (0.525, 0.510, 'R250 (0.25 ohm) sense resistors, x4'),
        (0.600, 0.330, 'D1/D3/D5/D7 diodes "RGS 2616"'),
        (0.600, 0.245, 'PIN1: 8-pin module header'),
        (0.170, 0.900, 'U4 YT9215SCH (lot VKJC09324)'),
        (0.600, 0.930, 'Y6 25 MHz crystal'),
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
    f = ImageFont.truetype(FONT, 26)
    r = 20
    for i, (x, y, _) in enumerate(points, 1):
        cx, cy = x * w, y * h
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(220, 20, 20), outline='white', width=3)
        d.text((cx, cy), str(i), font=f, fill='white', anchor='mm')
    pw = 600
    out = Image.new('RGB', (w + pw, h), (250, 250, 248))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    ft = ImageFont.truetype(FONT, 26)
    fl = ImageFont.truetype(FONT_R, 22)
    d.text((w + 24, 24), title, font=ft, fill=(30, 30, 30))
    y = 84
    for i, (_, _, label) in enumerate(points, 1):
        d.ellipse((w + 24, y, w + 56, y + 32), fill=(220, 20, 20))
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
