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
# Values are degrees counter-clockwise; photos not listed need no rotation.
ROTATE = {'04': 180, '21': 90, '22': 180, '23': 180, '24': 270, '25': 270,
          '26': 90, '27': 180, '28': 180, '29': 180, '30': 90, '31': 90, '32': 90}


# Crop box (x0, y0, x1, y1) in percent of the rotated photo: the bounding box of the
# board. On angled shots some background stays in the corners of that box. Photos not
# listed need no crop.
CROP = {'01': (7.2, 22.2, 97, 88), '02': (11, 23.3, 90.1, 80), '03': (10, 26, 92, 81),
        '04': (8, 16.8, 87.5, 78.3), '05': (1, 10, 100, 76), '08': (2.5, 17, 97.2, 77.4),
        '14': (0, 0, 98, 100), '15': (0, 0, 98, 100),
        '17': (0, 6, 95, 100), '18': (0, 17, 92, 100), '19': (0, 0, 60.8, 100),
        '21': (12, 9, 100, 100), '22': (15, 34.7, 100, 100), '24': (0, 0, 54.8, 76.8),
        '25': (0, 12, 63, 100), '26': (31.3, 0, 100, 100), '27': (0, 8, 98, 100),
        '30': (0, 9, 100, 100), '33': (0, 0, 100, 73), '34': (0, 0, 100, 73)}


def crop(im, key):
    if key not in CROP:
        return im
    x0, y0, x1, y1 = CROP[key]
    w, h = im.size
    return im.crop((round(w * x0 / 100), round(h * y0 / 100), round(w * x1 / 100), round(h * y1 / 100)))


# Callouts: photo -> (title, [(targets, label, badge)]). Positions are percentages of
# the width and height of the rotated, cropped photo. A target (x0, y0, x1, y1) is a box
# drawn around a part, so the marking inside it stays readable; a target (x, y) is a
# small ring for a spot with no marking. A numbered badge sits at `badge` with a leader
# line to the first target; further targets of the same callout are only outlined. A badge
# position below 0 or above 100 puts the badge in the plain margin that surrounds the photo.
CALLOUTS = {
    '04': ('Board A, top, U4 without heatsink', [
        ([(61.4, 36.5, 78.4, 53.5)], 'U4 YT9215SCH switch IC', (59.1, 42.0)),
        ([(45.4, 80.0, 57.8, 95.0)], 'U12 SFP host connector, no cage', (51.6, 103)),
        ([(81.5, 74.0, 101.1, 92.0)], 'Single RJ45', (90.8, 103)),
        ([(1.5, 9.5, 22.7, 82.0)], 'RJ45 block', (-3, 40.0)),
        ([(33.0, 59.5, 46.4, 76.0)], 'G2401PR magnetics (date 2632)', (38.2, 103)),
        ([(87.7, 46.3, 94.2, 52.3)], 'PU1 SCT2622 3.3 V buck', (103, 49.0)),
        ([(78.4, 22.5, 91.8, 30.5)], 'L2 "701" input inductor', (103, 23.5)),
        ([(84.1, 5.0, 96.4, 15.0)], 'J2 POWER2 input connector', (103, 10.0)),
        ([(66.5, 4.5, 82.0, 16.5)], 'RV1-RV3 blue disc parts', (74.3, -3)),
        ([(23.7, 11.0, 27.3, 34.0)], 'PoE module header, empty', (27.8, -3)),
    ]),
    '08': ('Board B, top, with PoE module and SFP cage', [
        ([(59.0, 31.3, 75.0, 48.8)], 'U4 YT9215SCH switch IC', (54.9, 47.5)),
        ([(27.7, 5.1, 58.5, 29.3)], 'PoE PSE module, U1 "2184A"', (40.2, -3)),
        ([(0.5, 70.8, 55.9, 91.4)], 'SFP cage over U12', (28.7, 103)),
        ([(4.7, 2.6, 28.7, 66.7)], 'RJ45 block', (-3, 30.8)),
        ([(81.5, 60.6, 98.8, 82.1)], 'Single RJ45', (103, 71.9)),
        ([(84.1, 42.1, 90.0, 47.2)], 'PU1 SCT2622 3.3 V buck', (103, 45.2)),
        ([(76.3, 17.5, 87.3, 25.7)], 'L2 "701" input inductor', (103, 19.5)),
        ([(77.3, 2.1, 86.8, 13.9)], 'J2 POWER2 input connector', (103, 7.2)),
        ([(53.8, 60.6, 70.5, 73.4)], 'G2401PR magnetics (date 2523A)', (57.5, 103)),
        ([(64.8, 90.3, 78.9, 100.6)], 'Silkscreen LX-IS601F V2.0', (71.6, 103)),
    ]),
    '06': ('Board A, U4 close-up', [
        ([(29, 29.5, 77, 62)], 'U4 YT9215SCH, lot VKTP18287', (67, 64.7)),
        ([(35.5, 51.7, 39.8, 55)], 'Pin-1 dimple', (24, 57)),
        ([(43.5, 11.6, 54.5, 17.2)], 'Y6 25.000 MHz crystal', (62, 20)),
        ([(83, 39.2, 88.8, 47)], 'R44, R89, R92, R93 (top to bottom): SPI flash lines (SPF0)', (80, 43)),
        ([(80, 3, 100, 17)], 'L2 "701" input inductor', (72, 13)),
        ([(4.5, 8.3, 15.3, 15.8)], 'ED1, one of the SOT-23-6 ESD arrays', (7, 20.5)),
        ([(78.5, 22.5, 90.5, 33.5)], '"4R7" inductor', (104, 28)),
        ([(10, 89, 59, 100)], 'G2401PR magnetics', (5, 95)),
    ]),
    '21': ('Board A, port edge, no PoE module', [
        ([(37.2, 24, 41.2, 68)], 'PoE module header, 8 holes, empty', (44.3, 47)),
        ([(68.8, 3.5, 88, 21.5)], 'POW and FX LED array, 6 x 2', (79, -4)),
        ([(20, 9, 28.3, 22.5)], 'LED6 through-hole footprint, empty', (14, 14)),
        ([(32.8, 10, 38, 16.2)], 'LED7 (left), LED8 (right)', (42, -4)),
        ([(48.5, 17, 62.5, 51.5)], 'G2401PR magnetics (date 2632)', (53, -4)),
        ([(75, 48.5, 81.3, 56.3)], 'ED1, one of the SOT-23-6 ESD arrays', (79.3, 45.3)),
    ]),
    '26': ('Bottom side, under U4', [
        ([(10.5, 48, 20, 62.5)], 'U6 8-pin footprint, unpopulated', (-3, 55)),
        ([(50.7, 20.5, 60.5, 33)], 'U10 "HK 24C08" I2C EEPROM', (55.5, -3)),
        ([(35, 50, 44.5, 59.5)], 'Tinned pad with a solder blob, under U4', (48, 56.5)),
        ([(3.5, 59, 11, 64.5)], 'Small tinned via grid', (-3, 62)),
        ([(81, 2, 91, 50.5)], 'Port-side row of 1206 capacitors', (75.5, 26)),
    ]),
    '32': ('Board B, PoE PSE module', [
        ([(60, 30, 74, 47.5)], 'U1 "2184A 533AQ1H" (PSE, unidentified)', (59.5, 29.5)),
        ([(47.5, 43.5, 55, 50.5), (48.5, 26.5, 54, 36), (59, 51.5, 64.5, 61), (59.5, 18, 64.5, 28)],
         'R12, R13, R8, R14: R250 (0.25 ohm) sense', (45, 47.5)),
        ([(30, 49.5, 39.5, 57.5), (30, 38.5, 39.5, 46.5), (30, 27.5, 39.5, 35.5), (30, 16.5, 39.5, 24.5),
          (66, 10, 74.5, 17.5)], 'D1, D3, D5, D7 and one more diode: "2616" over "RGS"', (44.5, 58.5)),
        ([(23, 15.5, 27.5, 59)], 'PIN1: 8-pin module header', (14, 37)),
        ([(81.5, 68, 100, 100)], 'U4 YT9215SCH (lot VKJC09324)', (78, 88)),
        ([(87, 42.3, 94, 48.5)], 'Y6 25.000 MHz crystal', (97.5, 39.5)),
    ]),
}


def strip(im, deg=0):
    """Return an upright copy with no EXIF data, rotated `deg` counter-clockwise."""
    im = ImageOps.exif_transpose(im)
    if deg:
        im = im.transpose({90: Image.Transpose.ROTATE_90, 180: Image.Transpose.ROTATE_180,
                           270: Image.Transpose.ROTATE_270}[deg])
    out = Image.new('RGB', im.size)
    out.paste(im)
    return out


PAD = 56    # plain margin around an annotated photo, for badges


def annotate(im, title, points, height=1000):
    photo = im.copy()
    photo.thumbnail((10000, height))
    w, h = photo.size
    im = Image.new('RGB', (w + 2 * PAD, h + 2 * PAD), (250, 250, 248))
    im.paste(photo, (PAD, PAD))
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 24)
    f2 = ImageFont.truetype(FONT, 18)        # two-digit badge numbers
    red = (220, 20, 20)
    P = lambda xy: (PAD + xy[0] * w / 100, PAD + xy[1] * h / 100)
    def shape(t):
        """Pixel box of a target: a ring around a point, or the given box."""
        if len(t) == 2:
            tx, ty = P(t)
            return (tx - 9, ty - 9, tx + 9, ty + 9)
        return P(t[:2]) + P(t[2:])

    for targets, _, badge in points:          # leader lines first, under everything
        bx, by = P(badge)
        for t in targets[:1]:
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
        d.text((bx, by), str(i), font=f if i < 10 else f2, fill='white', anchor='mm')
    w, h = im.size
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
