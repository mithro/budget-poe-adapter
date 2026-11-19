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

# Rotation applied to each photo so all share one orientation (see README):
# top side with the RJ45 block on the left and the LX-IS601F silkscreen readable;
# bottom side as if the board were flipped left-to-right (RJ45 block on the right).
# Values are degrees counter-clockwise; photos not listed are already upright.
ROTATE = {'04': 180, '21': 90, '22': 180, '23': 180, '24': 270, '25': 270,
          '26': 90, '27': 180, '28': 180, '29': 180, '30': 90, '31': 90, '32': 90}


# Crop box (x0, y0, x1, y1) in percent of the rotated photo: the bounding box of the
# board. On angled shots some background stays in the corners of that box. Photos not
# listed show board from edge to edge.
CROP = {'01': (5, 19, 97, 88), '02': (10, 22, 92, 80), '03': (10, 26, 92, 81),
        '04': (8, 15, 90, 82), '05': (1, 10, 100, 80), '08': (1, 17, 100, 79),
        '14': (0, 0, 98, 100), '15': (0, 0, 98, 100),
        '17': (0, 6, 95, 100), '18': (0, 17, 92, 100), '19': (0, 0, 62, 100),
        '21': (12, 9, 100, 100), '22': (15, 33, 100, 100), '24': (0, 0, 57, 79),
        '25': (0, 12, 63, 100), '26': (29, 0, 100, 100), '27': (0, 8, 98, 100),
        '30': (0, 9, 100, 100), '33': (0, 0, 100, 74), '34': (0, 0, 100, 73)}


def crop(im, key):
    if key not in CROP:
        return im
    x0, y0, x1, y1 = CROP[key]
    w, h = im.size
    return im.crop((round(w * x0 / 100), round(h * y0 / 100), round(w * x1 / 100), round(h * y1 / 100)))


# Callouts: photo -> (title, [(targets, label, badge)]). Positions are percentages of
# the width and height of the rotated, cropped photo. A target (x, y) gets a small ring
# and a target (x0, y0, x1, y1) gets a box around a group of parts. A numbered badge
# sits at `badge` with a leader line to every target, so badges can be put on empty
# background instead of over markings.
CALLOUTS = {
    '04': ('Board A, top, heatsink removed', [
        ([(68.3, 43.3)], 'U4 YT9215SCH switch IC', (68.3, 3)),
        ([(50.0, 83.6)], 'U12 SFP host connector, no cage', (50.0, 97)),
        ([(87.8, 82.1)], 'Single RJ45', (87.8, 97)),
        ([(13.4, 37.3)], 'RJ45 block', (4, 37.3)),
        ([(39.0, 67.2)], 'G2401PR magnetics (date 2632)', (29.3, 97)),
        ([(89.0, 49.3)], 'PU1 SCT2622 3.3 V buck', (96, 52.2)),
        ([(86.6, 27.0)], 'L2 "701" input inductor', (96, 28.4)),
        ([(87.8, 10.4)], 'J2 POWER2 input connector', (96, 3)),
        ([(72.0, 13.4)], 'Blue disc capacitors (x3)', (80.5, 3)),
        ([(25.6, 25.4)], 'PoE module header, empty', (11, 17)),
    ]),
    '08': ('Board B, top: PoE module + SFP', [
        ([(60.6, 32.5)], 'U4 YT9215SCH switch IC', (65.7, 3)),
        ([(51.5, 16.1)], 'PoE PSE module, U1 "2184A"', (47.5, 3)),
        ([(29.3, 77.4)], 'SFP cage over U12', (29.3, 97)),
        ([(16.2, 37.1)], 'RJ45 block', (7.1, 3)),
        ([(87.9, 72.6)], 'Single RJ45', (91.9, 97)),
        ([(83.8, 41.9)], 'PU1 SCT2622 3.3 V buck', (94.9, 29.0)),
        ([(75.4, 17.6)], 'L2 "701" input inductor', (95.8, 17)),
        ([(80.8, 8.1)], 'J2 power input', (93.9, 3)),
        ([(60.6, 62.9)], 'G2401PR magnetics (date 2523A)', (57.6, 97)),
        ([(68.0, 93.6)], 'Silkscreen LX-IS601F V2.0', (64.5, 97.8)),
    ]),
    '06': ('Board A, U4 close-up', [
        ([(62.0, 54.0)], 'U4 YT9215SCH, lot VKTP18287', (68.0, 66.0)),
        ([(38.0, 53.0)], 'Pin-1 dimple', (13.0, 70.0)),
        ([(49.0, 13.0)], 'Y6 25.000 MHz crystal', (62.0, 20.0)),
        ([(83.2, 38.9, 88.6, 47.1)], 'R44, R89, R92, R93 (top to bottom): SPI flash lines (SPF0)', (79.4, 61.2)),
        ([(85.3, 10.0)], 'L2 "701" input inductor', (74.0, 7.0)),
        ([(10.0, 12.0)], 'ED1, one of the SOT-23-6 ESD arrays', (5.0, 22.0)),
        ([(84.0, 27.0)], '"4R7" inductor', (72.0, 26.0)),
        ([(35.0, 93.0)], 'G2401PR magnetics', (55.0, 92.0)),
    ]),
    '21': ('Board A, port edge, no PoE module', [
        ([(38.6, 65.4), (38.6, 48.9), (38.6, 27.0)], 'PoE module header, 8 holes, empty', (4, 45.1)),
        ([(77.3, 16.5)], 'POW / FX LED resistor pads (RJ7-RJ18)', (79.5, 3)),
        ([(23.9, 15.4)], 'LED6 through-hole footprint, empty', (11.4, 3)),
        ([(34.1, 13.2), (36.3, 13.2)], 'LED7 (left), LED8 (right)', (46, 2.5)),
        ([(54.5, 33.0)], 'G2401PR magnetics (date 2632)', (48.9, 18.7)),
        ([(75.0, 72.5), (78.4, 53.8), (81.8, 41.8)], 'ESD arrays ED2, ED1, ED10', (69.3, 48.4)),
    ]),
    '26': ('Bottom side, under U4', [
        ([(18.3, 56.0)], 'U6 8-pin footprint, unpopulated', (4, 56.0)),
        ([(60.1, 24.6)], 'U10 HK24C08 I2C EEPROM', (43.7, 12.0)),
        ([(40.8, 55.0)], 'Tinned via field (probably under U4)', (4, 78.0)),
        ([(9.9, 63.0)], 'Small tinned via grid', (4, 68.0)),
        ([(84.5, 43.0), (84.5, 20.0)], 'Port-side row of 1206 capacitors', (70.4, 35.0)),
    ]),
    '32': ('Board B, PoE PSE module', [
        ([(72.0, 45.0)], 'U1 "2184A 533AQ1H" (PSE, unidentified)', (79.0, 55.0)),
        ([(61.0, 60.0), (49.0, 46.8), (50.9, 35.0), (60.1, 26.2)], 'R8, R12, R13, R14: R250 (0.25 ohm) sense', (42.0, 39.0)),
        ([(30.4, 54.0), (30.4, 43.0), (30.4, 32.0), (30.4, 21.0)], 'D1, D3, D5, D7 diodes "RGS 2616"', (9.0, 38.0)),
        ([(25.0, 57.0)], 'PIN1: 8-pin module header', (9.0, 70.0)),
        ([(86.7, 94.0)], 'U4 YT9215SCH (lot VKJC09324)', (78.0, 90.0)),
        ([(92.8, 46.2)], 'Y6 25 MHz crystal', (84.0, 56.0)),
    ]),
}


def strip(im, deg=0):
    """Return an upright copy with no EXIF/GPS, rotated `deg` counter-clockwise."""
    im = ImageOps.exif_transpose(im)
    if deg:
        im = im.transpose({90: Image.Transpose.ROTATE_90, 180: Image.Transpose.ROTATE_180,
                           270: Image.Transpose.ROTATE_270}[deg])
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
    def shape(t):
        """Pixel box of a target: a ring around a point, or the given box."""
        if len(t) == 2:
            tx, ty = P(t)
            return (tx - 9, ty - 9, tx + 9, ty + 9)
        return P(t[:2]) + P(t[2:])

    for targets, _, badge in points:          # leader lines first, under everything
        bx, by = P(badge)
        for t in targets:
            x0, y0, x1, y1 = shape(t)
            if len(t) == 2:                   # to the centre of a ring
                tx, ty = (x0 + x1) / 2, (y0 + y1) / 2
            else:                             # to the nearest point of a box
                tx, ty = min(max(bx, x0), x1), min(max(by, y0), y1)
            d.line((bx, by, tx, ty), fill='white', width=5)
            d.line((bx, by, tx, ty), fill=red, width=3)
    for targets, _, _ in points:
        for t in targets:
            draw = d.ellipse if len(t) == 2 else d.rectangle
            draw(shape(t), outline='white', width=5)
            draw(shape(t), outline=red, width=3)
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
        im = crop(strip(Image.open(os.path.join(src, key + '.jpg')), ROTATE.get(key, 0)), key)
        web = im.copy(); web.thumbnail((1600, 1600))
        web.save(os.path.join(HERE, 'web', key + '.jpg'), quality=85, optimize=True)
        th = im.copy(); th.thumbnail((240, 240))
        th.save(os.path.join(HERE, 'thumbs', key + '.jpg'), quality=82, optimize=True)
        if key in CALLOUTS:
            title, pts = CALLOUTS[key]
            annotate(im, title, pts).save(os.path.join(HERE, 'annotated', key + '.jpg'), quality=85, optimize=True)


if __name__ == '__main__':
    main(sys.argv[1])
