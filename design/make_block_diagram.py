#!/usr/bin/env python3
"""Draw the two block diagrams as SVG.

Usage: python3 make_block_diagram.py
Writes block-diagram-with-switch.svg and block-diagram-without-switch.svg next to
this script. Needs only the Python standard library. svg_to_png.js makes the PNG
copies from the SVGs.

The canvas is 940 units wide and the smallest text is 14 units, so the text stays
readable when the figure is scaled to the width of a documentation page.
"""
import os
from xml.sax.saxutils import escape

HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 940, 965
COL = {1: 20, 2: 360, 3: 700}          # left edge of each column
BW = 220                               # block width
ROW = {1: (70, 80), 2: (215, 140), 3: (445, 110), 4: (635, 100), 5: (800, 70)}   # top, height

INK, MUTED = '#0f172a', '#475569'
DATA, POWER, CTRL = '#1d4ed8', '#c2410c', '#15803d'
FILL = {'ext': ('#f1f5f9', MUTED), 'data': ('#dbeafe', DATA), 'switch': ('#ede9fe', '#6d28d9'),
        'mcu': ('#dcfce7', CTRL), 'power': ('#ffedd5', POWER)}
F_TITLE, F_NAME, F_TEXT = 22, 17, 14


class Svg:
    def __init__(self):
        self.out = []

    def text(self, x, y, s, size=F_TEXT, fill=INK, anchor='middle', bold=False):
        self.out.append('<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" font-weight="%d">%s</text>'
                        % (x, y, size, fill, anchor, 700 if bold else 400, escape(s)))

    def label(self, x, y, lines, fill, anchor='middle', bold=False, backing=True):
        """Lines of text, first baseline at y, on a white backing unless the label sits in clear space."""
        for i, s in enumerate(lines):
            if not backing:
                self.text(x, y + i * 17, s, fill=fill, anchor=anchor, bold=bold)
                continue
            w = len(s) * F_TEXT * 0.52 + 8
            x0 = {'middle': x - w / 2, 'start': x - 4, 'end': x - w + 4}[anchor]
            self.out.append('<rect x="%g" y="%g" width="%g" height="18" fill="#ffffff" opacity="0.92"/>'
                            % (x0, y + i * 17 - 13.5, w))
            self.text(x, y + i * 17, s, fill=fill, anchor=anchor, bold=bold)

    def line(self, pts, kind, both=False, start_only=False):
        colour, width, marker, dash = {'data': (DATA, 3.5, 'adata', ''), 'rmii': (DATA, 2, 'armii', ''),
                                       'power': (POWER, 4, 'apwr', ''),
                                       'ctrl': (CTRL, 2, 'actl', ' stroke-dasharray="6 4"')}[kind]
        (xa, ya), (xb, yb) = pts[0], pts[1]
        (xc, yc), (xd, yd) = pts[-2], pts[-1]
        pts = list(pts)
        # stop 2 units short of the block so the arrow tip touches its outline
        n = lambda a, b: (b > a) - (b < a)
        pts[-1] = (xd - 2 * n(xc, xd), yd - 2 * n(yc, yd))
        pts[0] = (xa + 2 * n(xa, xb), ya + 2 * n(ya, yb))
        d = 'M' + ' L'.join('%g,%g' % p for p in pts)
        ends = ''
        if both or start_only:
            ends += ' marker-start="url(#%s)"' % marker
        if not start_only:
            ends += ' marker-end="url(#%s)"' % marker
        self.out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%g"%s%s/>' % (d, colour, width, dash, ends))

    def block(self, col, row, name, lines, kind, cost=None):
        x, (y, h) = COL[col], ROW[row]
        fill, stroke = FILL[kind]
        self.out.append('<rect x="%g" y="%g" width="%g" height="%g" rx="8" fill="%s" stroke="%s" stroke-width="2"/>'
                        % (x, y, BW, h, fill, stroke))
        ty = y + h / 2 - (len(lines) * 19) / 2 + 6
        self.text(x + BW / 2, ty, name, F_NAME, bold=True)
        for i, s in enumerate(lines, 1):
            self.text(x + BW / 2, ty + 2 + i * 19, s)
        if cost:
            self.out.append('<rect x="%g" y="%g" width="66" height="24" rx="12" fill="%s"/>' % (x + BW - 62, y - 12, INK))
            self.text(x + BW - 29, y + 5, cost, fill='#ffffff', bold=True)


def marker(name, colour, size):
    return ('<marker id="%s" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="%d" '
            'markerHeight="%d" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="%s"/></marker>'
            % (name, size, size, colour))


def top(row):
    return ROW[row][0]


def bottom(row):
    return ROW[row][0] + ROW[row][1]


def mid(row):
    return ROW[row][0] + ROW[row][1] / 2


def draw(v):
    s = Svg()
    c1, c2, c3 = (COL[i] + BW / 2 for i in (1, 2, 3))
    l2, r2 = COL[2], COL[2] + BW
    r1, l3 = COL[1] + BW, COL[3]
    s.text(20, 36, v['title'], F_TITLE, anchor='start', bold=True)

    # blocks
    s.block(1, 1, 'PoE switch', ['(PSE) 44–57 V'], 'ext')
    s.block(1, 2, 'RJ45 IN', v['jack_in'], 'data', v['jack_in_cost'])
    s.block(1, 3, v['mid'], v['mid_lines'], v['mid_kind'], v['mid_cost'])
    s.block(1, 4, 'RJ45 OUT', v['jack_out'], 'data', v['jack_out_cost'])
    s.block(1, 5, 'Pi 5 / device', ['Ethernet port'], 'ext')
    s.block(2, 2, 'PoE PD front end', ['2× bridges + TVS', '24.9 kΩ signature', 'class/mark current sink',
                                       'low-side hot-swap NMOS', 'bootstrap reg → 3V3_BOOT'], 'power', '$0.53')
    s.block(2, 3, v['mcu'], v['mcu_lines'], 'mcu', v['mcu_cost'])
    s.block(3, 1, v['reg'], [v['reg_line']], 'power', v['reg_cost'])
    s.block(3, 2, '60 V sync buck', ['36–57 V → 5.1 V or 12 V', '5/12 V set by MCU GPIO'], 'power', '$1.09')
    s.block(3, 3, 'VBUS load switch', ['PMOS · I shunt', '15 V TVS'], 'power', '$0.16')
    s.block(3, 4, 'USB-C receptacle', ['PD 5 V / 12 V', 'CC 12 V-short protection'], 'power', '$0.26')
    s.block(3, 5, 'Pi 5 / device', ['USB-C power in'], 'ext')

    # gigabit data path, down the left column
    s.line([(c1, bottom(1)), (c1, top(2))], 'data', both=True)
    s.line([(c1, bottom(2)), (c1, top(3))], 'data', both=True)
    s.label(c1 + 12, bottom(2) + 50, ['MDI'], DATA, 'start')
    s.line([(c1, bottom(3)), (c1, top(4))], 'data', both=True)
    s.label(c1 + 12, bottom(3) + 45, ['MDI'], DATA, 'start')
    s.line([(c1, bottom(4)), (c1, top(5))], 'data', both=True)

    # power path
    y = mid(2)
    s.line([(r1, y), (l2, y)], 'power')
    s.label((r1 + l2) / 2, y - 29, ['4× centre taps', '(all 4 pairs)'], POWER)
    s.line([(r2, y), (l3, y)], 'power')
    s.label((r2 + l3) / 2, y - 12, ['36–57 V'], POWER)
    s.line([(c3 + 20, top(2)), (c3 + 20, bottom(1))], 'power')
    s.label(c3 + 32, top(2) - 28, ['5.1 / 12 V'], POWER, 'start')
    s.line([(c3 + 20, bottom(2)), (c3 + 20, top(3))], 'power')
    s.label(c3 + 32, bottom(2) + 50, ['5.1 / 12 V'], POWER, 'start')
    s.line([(c3 + 20, bottom(3)), (c3 + 20, top(4))], 'power')
    s.label(c3 + 32, bottom(3) + 45, ['VBUS'], POWER, 'start')
    s.line([(c3, bottom(4)), (c3, top(5))], 'power')

    # supply stubs
    yb = bottom(3)
    s.line([(l2 + 50, yb + 34), (l2 + 50, yb)], 'power')
    s.label(l2 + 50, yb + 50, ['3V3_BOOT'], POWER, bold=True)
    s.line([(l2 + 120, yb + 34), (l2 + 120, yb)], 'power')
    s.label(l2 + 120, yb + 50, ['3V3'], POWER, bold=True)
    if v['switch']:
        s.line([(COL[1] + 40, yb + 34), (COL[1] + 40, yb)], 'power')
        s.label(COL[1] + 40, yb + 50, ['3V3'], POWER, bold=True)
        # MCU on the switch's RMII port
        y = mid(3)
        s.line([(r1, y), (l2, y)], 'rmii', both=True)
        s.label((r1 + l2) / 2, y - 10, ['RMII 100 Mb/s'], DATA)
        s.label((r1 + l2) / 2, y + 22, ['+ MDIO'], DATA)

    # MCU control and sense
    s.line([(l2 + 40, top(3)), (l2 + 40, bottom(2))], 'ctrl')
    s.label(l2 + 30, bottom(2) + 40, ['class PWM ·', 'hot-swap gate'], CTRL, 'end')
    s.line([(l2 + 75, bottom(2)), (l2 + 75, top(3))], 'ctrl')
    s.label(l2 + 85, bottom(2) + 66, ['VIN / I sense'], CTRL, 'start')
    ys = bottom(2) + 36
    s.line([(r2 - 30, top(3)), (r2 - 30, ys), (l3 + 40, ys), (l3 + 40, bottom(2))], 'ctrl')
    s.label((r2 - 30 + l3 + 40) / 2, ys - 9, ['5V/12V SEL (default 5 V)'], CTRL)
    s.line([(r2, top(3) + 32), (l3, top(3) + 32)], 'ctrl')
    s.label((r2 + l3) / 2, top(3) + 23, ['VBUS_EN (gate)'], CTRL)
    s.line([(l3, top(3) + 78), (r2, top(3) + 78)], 'ctrl')
    s.label((r2 + l3) / 2, top(3) + 99, ['VBUS V / I sense'], CTRL, backing=False)
    yc = bottom(3) + 42
    s.line([(r2 - 30, bottom(3)), (r2 - 30, yc), (l3 + 40, yc), (l3 + 40, top(4))], 'ctrl', both=True)
    s.label((r2 - 30 + l3 + 40) / 2, yc + 22, ['CC1 / CC2 (Rp, PD BMC)'], CTRL)

    # legend
    y = 918
    s.out.append('<line x1="20" y1="%g" x2="%g" y2="%g" stroke="#cbd5e1" stroke-width="1"/>' % (y - 28, W - 20, y - 28))
    x = 20
    for kind, name, both, w in (('data', 'Gigabit data (MDI)', True, 215), ('rmii', '100 Mb/s RMII + MDIO', True, 240),
                                ('power', 'Power', False, 135), ('ctrl', 'MCU control / sense', False, 0)):
        s.line([(x - 2, y), (x + 54, y)], kind, both=both)
        s.text(x + 64, y + 5, name, anchor='start')
        x += w + 20
    s.text(20, y + 32, 'Black tags are the cost of each block at 1k units.', fill=MUTED, anchor='start')

    head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
            'font-family="Helvetica, Arial, sans-serif"><defs>%s%s%s%s</defs><rect width="%d" height="%d" fill="#ffffff"/>'
            % (W, H, W, H, marker('adata', DATA, 11), marker('armii', DATA, 9), marker('apwr', POWER, 11),
               marker('actl', CTRL, 11), W, H))
    return head + '\n' + '\n'.join(s.out) + '\n</svg>\n'


VARIANTS = {
    'block-diagram-with-switch.svg': dict(
        title='A. With switch chip (≈ $8.60 @1k)', switch=True,
        jack_in=['PoE GbE magjack', '(magnetics built in)'], jack_in_cost='$1.10',
        mid='RTL8363NB-VB-CG', mid_lines=['2× GbE PHY + RMII MAC', '25 MHz xtal, 3V3 in'], mid_kind='switch', mid_cost='$1.62',
        jack_out=['GbE magjack'], jack_out_cost='$0.65',
        mcu='CH32V307 (MCU)', mcu_lines=['PoE PD state machine', 'USB-PD source · LLDP'], mcu_cost='$1.38',
        reg='3.3 V buck', reg_line='3V3 rail → switch + MCU', reg_cost='$0.15'),
    'block-diagram-without-switch.svg': dict(
        title='B. Without switch chip (≈ $4.10 @1k)', switch=False,
        jack_in=['plain jack, no magnetics', '(×2 jacks @ $0.10)'], jack_in_cost='$0.10',
        mid='4-ch PoE splitter', mid_lines=['transformer', 'data through, taps out'], mid_kind='data', mid_cost='$0.50',
        jack_out=['plain jack'], jack_out_cost='$0.10',
        mcu='CH32V203 (MCU)', mcu_lines=['PoE PD state machine', 'USB-PD source'], mcu_cost='$0.43',
        reg='3.3 V LDO', reg_line='3V3 rail → MCU', reg_cost='$0.04'),
}

if __name__ == '__main__':
    for name, v in VARIANTS.items():
        with open(os.path.join(HERE, name), 'w', encoding='utf-8') as f:
            f.write(draw(v))
        print('wrote', name)
