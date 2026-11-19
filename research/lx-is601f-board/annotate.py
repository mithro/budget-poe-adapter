"""Draw the debug-pin annotations on crops of photo-u4-macro.jpg, and crop photo-u4-wide.jpg.

Writes four images next to this script:

  u4-pin-numbering-annotated.png    the whole package, pin 1 and the pin range of each side
  u4-pins-top-edge-annotated.png    pins 65 to 96 with their functions and vias
  u4-pins-right-edge-annotated.png  pins 46 to 55 with the SPF0 resistors
  u4-surroundings.jpg               U4 and the named parts beside it, from photo-u4-wide.jpg, not drawn on

Each image is a tight crop, and the label size is chosen so the text is still
readable when the image is scaled down to the width of a documentation page.
Needs Pillow and the DejaVu fonts. Coordinates are pixels in photo-u4-macro.jpg,
found by hand; see README.md.
"""
import os

from PIL import Image, ImageDraw, ImageFont, ImageEnhance

SP = os.path.dirname(os.path.abspath(__file__)) + '/'
F = '/usr/share/fonts/truetype/dejavu/'
UART = (255, 170, 40); SPI = (60, 220, 255); JTAG = (255, 110, 230); STRAP = (255, 240, 80)
REF = (215, 215, 215); I2C = (140, 255, 140); OTHER = (170, 170, 255); WHITE = (255, 255, 255)
BODY = [(1200, 1395), (2470, 1395), (2500, 1425), (2500, 2690), (2470, 2720), (1200, 2720), (1170, 2690), (1170, 1425)]


def font(size, bold=True):
    return ImageFont.truetype(F + ('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'), size)


def topx(n):
    """x of the lead of pin n on the top edge (pins 65 to 96)."""
    return 2430 - 38.4 * (n - 65)


def righty(n):
    """y of the lead of pin n on the right edge (pins 33 to 64)."""
    return 2670 - 38.2 * (n - 33)


class Crop:
    """A crop of the source photo that is drawn on in source-photo coordinates."""

    def __init__(self, src, box, darken=150):
        self.x0, self.y0 = box[0], box[1]
        img = ImageEnhance.Brightness(src.crop(box)).enhance(1.08).convert('RGBA')
        ov = Image.new('RGBA', img.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).polygon([self.P(*p) for p in BODY], fill=(0, 0, 0, darken))   # darken the package body
        self.img = Image.alpha_composite(img, ov).convert('RGB')
        self.d = ImageDraw.Draw(self.img)

    def P(self, x, y):
        return (x - self.x0, y - self.y0)

    def text(self, x, y, t, f, fill, anchor='la', sw=3):
        self.d.text(self.P(x, y), t, font=f, fill=fill, anchor=anchor, stroke_width=sw, stroke_fill=(0, 0, 0))

    def vtext(self, x, y, t, f, fill):
        """Text reading top to bottom, starting at (x, y) centre-top."""
        bb = f.getbbox(t, stroke_width=3)
        im = Image.new('RGBA', (bb[2] + 10, bb[3] + 12), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((5, 4), t, font=f, fill=fill + (255,), stroke_width=3, stroke_fill=(0, 0, 0, 255))
        im = im.rotate(-90, expand=True)
        px, py = self.P(x, y)
        self.img.paste(im, (int(px - im.width / 2), int(py)), im)

    def ring(self, x, y, colour, r=17, width=5):
        px, py = self.P(x, y)
        self.d.ellipse((px - r, py - r, px + r, py + r), outline=colour, width=width)

    def line(self, x0, y0, x1, y1, colour, width=3):
        self.d.line(self.P(x0, y0) + self.P(x1, y1), fill=colour, width=width)

    def save(self, name):
        self.img.save(SP + name, optimize=True)
        print('wrote %s %dx%d' % ((name,) + self.img.size))


src = Image.open(SP + 'photo-u4-macro.jpg').convert('RGB')

# ---------- the whole package: pin 1 and the pin range of each side ----------
c = Crop(src, (900, 1130, 2800, 2960), darken=90)
big, mid = font(64), font(50)
c.ring(1320, 2530, WHITE, r=72, width=6)
c.text(1410, 2530, 'pin-1 dimple', mid, WHITE, 'lm', 4)
c.text((1240 + 2430) / 2, 2655, 'pins 1 to 32', big, WHITE, 'mm', 4)
c.text(2390, (1486 + 2670) / 2, 'pins 33 to 64', big, WHITE, 'rm', 4)
c.text((1240 + 2430) / 2, 1500, 'pins 65 to 96', big, WHITE, 'mm', 4)
c.text(1270, (1486 + 2670) / 2 - 120, 'pins 97 to 128', big, WHITE, 'lm', 4)
for n, x, y, anchor in ((1, 1240, 2850, 'ma'), (32, 2430, 2850, 'ma'), (33, 2690, 2670, 'lm'), (64, 2690, 1486, 'lm'),
                        (65, 2430, 1260, 'md'), (96, 1240, 1260, 'md'), (97, 1050, 1486, 'rm'), (128, 1050, 2670, 'rm')):
    c.text(x, y, str(n), mid, STRAP, anchor, 4)
c.save('u4-pin-numbering-annotated.png')

# ---------- top edge: pins 65 to 96 and their vias ----------
c = Crop(src, (1180, 580, 2540, 2130))
fp = font(30)
TOP = [  # pin, text, colour
    (67, '67  JTAG1_TDO* — no trace', JTAG),
    (70, '70  UART1_RX · DIS_SPIS', UART),
    (72, '72  JTAG0_TMS* (P4LED1)', JTAG),
    (73, '73  JTAG0_TCK* (P3LED1)', JTAG),
    (74, '74  JTAG0_TDI* · EN_PWRLIGHT', JTAG),
    (75, '75  EN_SPIF strap (P3LED0)', STRAP),
    (76, '76  UART1_TX · DIS_MCU strap', UART),
    (77, '77  DISAUTOLOAD strap (P2LED0)', STRAP),
    (78, '78  SPF1_SO (P2LED1)', SPI),
    (79, '79  SPF1_SI — no trace', SPI),
    (81, '81  SPF1_CS · JTAG1_TMS*', SPI),
    (83, '83  SPF1_SCK · JTAG1_TCK* · EN_PHY', SPI),
    (84, '84  JTAG1_TDI* (LED_DA)', JTAG),
    (87, '87  XTALO', REF), (88, '88  XTALI', REF),
    (89, '89  nRESET', REF),
    (90, '90  JTAG0_TDO* — no trace', JTAG),
    (91, '91  SCL / MDC', I2C), (92, '92  SDA / MDIO', I2C),
]
for n, t, col in TOP:
    x = topx(n)
    c.ring(x, 1296, col, r=10, width=4)
    c.line(x, 1305, x, 1414, col)
    c.vtext(x, 1418, t, fp, col)
fs = font(34)
c.text(2430, 1232, '65', fs, WHITE, 'mm'); c.text(1240, 1232, '96', fs, WHITE, 'mm')
VIAS = [(80, 1925, 1030, OTHER, -8, -40), (77, 2022, 1065, STRAP, 0, 42), (76, 2087, 1005, UART, 0, -40),
        (75, 2142, 1047, STRAP, 0, 42), (74, 2197, 1002, JTAG, 0, -40), (70, 2380, 1067, UART, 46, 0),
        (78, 2102, 702, SPI, 46, 0), (81, 2025, 630, SPI, -46, 0),
        (85, 1644, 1136, OTHER, -44, 8), (84, 1664, 1064, JTAG, -46, -10), (83, 1720, 1022, SPI, 46, -6),
        (92, 1430, 1057, I2C, -6, -42), (91, 1410, 1112, I2C, -46, 6)]
for n, x, y, col, dx, dy in VIAS:
    c.ring(x, y, col)
    c.text(x + dx, y + dy, str(n), fs, col, 'mm')
c.save('u4-pins-top-edge-annotated.png')

# ---------- right edge: pins 46 to 55 and the SPF0 resistors ----------
c = Crop(src, (1540, 1740, 3072, 2260))
RIGHT = [
    (55, 'SPF0_CS → R44   55', SPI), (54, 'SPF0_SO → R89   54', SPI),
    (50, 'SPF0_SI → R92   50', SPI), (49, 'SPF0_SCK · SPF_MUX_SEL strap → R93   49', SPI),
    (47, 'UART0_TX — no trace   47', UART), (46, 'UART0_RX — no trace   46', UART),
]
for n, t, col in RIGHT:
    y = righty(n)
    c.ring(2603, y, col, r=10, width=4)
    c.line(2594, y, 2485, y, col)
    c.text(2479, y, t, fp, col, 'rm')
for lab, y in (('R44', 1825), ('R89', 1925), ('R92', 2025), ('R93', 2125)):
    px, py = c.P(2925, y)
    c.d.rounded_rectangle((px - 75, py - 36, px + 75, py + 36), radius=8, outline=SPI, width=5)
    c.text(3004, y, lab, fp, SPI, 'lm')                   # right of the box, clear of the trace into the pad
c.save('u4-pins-right-edge-annotated.png')

# ---------- U4 and the parts beside it, with their silkscreen names, on board A ----------
wide = Image.open(SP + 'photo-u4-wide.jpg').convert('RGB').crop((640, 825, 2300, 2790))
wide = wide.resize((850, round(850 * wide.height / wide.width)), Image.LANCZOS)
wide.save(SP + 'u4-surroundings.jpg', quality=88, optimize=True)
print('wrote u4-surroundings.jpg %dx%d' % wide.size)
