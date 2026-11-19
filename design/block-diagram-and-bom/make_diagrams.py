#!/usr/bin/env python3
"""Draw option-a.svg, option-b.svg and power-tree.svg next to this file.

Every drawing is 850 units wide with 14-unit text, so the text is 14 px tall on a page
that shows the drawing at its natural width.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
W = 850
BLUE, GREEN, YELLOW, GREY, RED = "#e8eefc", "#e8f6e8", "#fbf7e6", "#f4f6fa", "#fdecea"


class Drawing:
    def __init__(self, height):
        self.h = height
        self.out = []

    def box(self, x, y, w, h, lines, fill=GREY, top=False):
        self.out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="#222" '
                        'stroke-width="1.5"/>' % (x, y, w, h, fill))
        y0 = y + 20 if top else y + h / 2 - (len(lines) - 1) * 9
        for i, line in enumerate(lines):
            self.text(x + w / 2, y0 + i * 18, line, bold=(i == 0))

    def text(self, x, y, s, bold=False, anchor="middle"):
        self.out.append('<text x="%d" y="%d" text-anchor="%s" dominant-baseline="middle"%s>%s</text>'
                        % (x, y, anchor, ' font-weight="bold"' if bold else "", s))

    def line(self, points, both=False, power=False):
        d = "M" + " L".join("%d,%d" % p for p in points)
        self.out.append('<path d="%s" fill="none" stroke="%s" stroke-width="%s" marker-end="url(#%s)"%s/>'
                        % (d, "#b3261e" if power else "#222", "2.5" if power else "1.5",
                           "pa" if power else "a", ' marker-start="url(#b)"' if both else ""))

    def save(self, name):
        head = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
                'font-family="DejaVu Sans, Arial, sans-serif" font-size="14">' % (W, self.h, W, self.h)
                + '<defs><marker id="a" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto">'
                '<path d="M0,0 L9,4 L0,8 z" fill="#222"/></marker>'
                '<marker id="b" markerWidth="9" markerHeight="8" refX="1" refY="4" orient="auto">'
                '<path d="M9,0 L0,4 L9,8 z" fill="#222"/></marker>'
                '<marker id="pa" markerWidth="7" markerHeight="6" refX="6" refY="3" orient="auto">'
                '<path d="M0,0 L7,3 L0,6 z" fill="#b3261e"/></marker></defs>'
                + '<rect width="%d" height="%d" fill="#ffffff"/>' % (W, self.h))
        (HERE / name).write_text(head + "\n" + "\n".join(self.out) + "\n</svg>\n", encoding="utf-8")
        print(name)


def block_diagram(name, downstream, usb, cc_label, cable_label):
    """One upstream port, `downstream` downstream ports and `usb` USB-C outputs."""
    eth_h = 75 * downstream            # height taken by the downstream Ethernet rows
    usb_top = 30 + eth_h + 15
    usb_h = 170 * usb
    chip_h = max(usb_top + usb_h - 20, 330)
    power_y = 20 + chip_h + 50
    d = Drawing(power_y + 150)

    # Switch IC
    d.box(340, 20, 180, chip_h, ["YT9215", "switch IC"], fill=BLUE, top=True)
    d.box(352, 80, 156, 46, ["Switch core", "5 gigabit PHYs"], fill="#ffffff")
    d.box(352, 140, 156, 100, ["RISC-V CPU", "LLDP power request", "USB PD source", "power sequencing"],
          fill="#ffffff")
    d.box(352, 254, 156, 46, ["Core regulator", "3.3 V to 1.15 V"], fill="#ffffff")

    # Upstream Ethernet
    d.box(15, 30, 120, 60, ["RJ45 jack", "upstream", "PoE in"], fill=GREEN)
    d.box(170, 30, 140, 60, ["LAN transformer", "carries PoE"])
    d.line([(135, 60), (170, 60)], both=True)
    d.line([(310, 60), (340, 60)], both=True)
    d.text(325, 44, "P0")

    # Support parts on the left of the chip
    d.box(170, 125, 140, 44, ["Crystal", "25 MHz"], fill=YELLOW)
    d.line([(310, 147), (340, 147)])
    d.box(170, 185, 140, 44, ["SPI flash", "firmware"], fill=YELLOW)
    d.line([(310, 207), (340, 207)], both=True)
    d.box(170, 245, 140, 60, ["Strap resistors", "reset resistor", "reset capacitor"], fill=YELLOW)
    d.line([(310, 275), (340, 275)])

    # Downstream Ethernet
    for i in range(downstream):
        y = 30 + 75 * i
        d.box(585, y, 135, 60, ["LAN transformer"])
        d.box(745, y, 90, 60, ["RJ45 jack", "downstream"], fill=GREEN)
        d.line([(520, y + 30), (585, y + 30)], both=True)
        d.text(542, y + 16, "P%d" % (i + 1))
        d.line([(720, y + 30), (745, y + 30)], both=True)

    # USB-C outputs
    for i in range(usb):
        y = usb_top + 170 * i
        d.box(585, y, 135, 66, ["CC interface"] + cc_label, fill=YELLOW)
        d.line([(520, y + 33), (585, y + 33)], both=True)
        d.box(585, y + 84, 135, 60, ["VBUS switch", "off at reset"], fill=RED)
        d.line([(520, y + 100), (585, y + 100)])
        d.text(552, y + 86, "GPIO")
        d.box(745, y, 90, 144, cable_label + (["output %d" % (i + 1)] if usb > 1 else []), fill=GREEN)
        d.line([(720, y + 33), (745, y + 33)], both=True)
        d.text(733, y + 17, "CC")
        d.line([(720, y + 114), (745, y + 114)], power=True)

    # Power path along the bottom
    d.box(15, power_y, 150, 100, ["PoE front end", "2 bridges", "signature", "class sink", "hot-swap switch"],
          fill=RED)
    d.line([(190, 90), (190, 108), (75, 108), (75, power_y)], power=True)
    d.text(85, 240, "centre taps", anchor="start")
    d.text(85, 258, "up to 57 V", anchor="start")
    d.box(200, power_y, 130, 100, ["5 V converter", "5 A output"], fill=RED)
    d.line([(165, power_y + 50), (200, power_y + 50)], power=True)
    d.box(380, power_y, 130, 100, ["3.3 V converter"], fill=RED)
    d.line([(330, power_y + 30), (380, power_y + 30)], power=True)
    d.text(355, power_y + 16, "5 V")
    d.line([(445, power_y), (445, 20 + chip_h)], power=True)
    d.text(437, power_y - 24, "3.3 V", anchor="end")
    # 5 V rail to every VBUS switch
    trunk = 565
    top = usb_top + 130
    d.line([(330, power_y + 75), (355, power_y + 75), (355, power_y + 125), (trunk, power_y + 125),
            (trunk, top), (585, top)], power=True)
    for i in range(1, usb):
        d.line([(trunk, top + 170 * i), (585, top + 170 * i)], power=True)
    d.text(trunk + 10, power_y + 110, "5 V rail to each VBUS switch" if usb > 1 else "5 V rail to the VBUS switch", anchor="start")
    d.text(15, power_y + 125, "Red: power. Black: signal.", anchor="start")
    d.save(name)


def power_tree(name):
    d = Drawing(430)
    d.box(10, 150, 125, 80, ["PoE input", "up to 57 V", "25.5 W granted"], fill=GREEN)
    d.box(160, 150, 110, 80, ["Bridges", "hot-swap", "switch"], fill=RED)
    d.line([(135, 190), (160, 190)], power=True)
    d.box(305, 150, 120, 80, ["5 V converter", "87 % assumed"], fill=RED)
    d.line([(270, 190), (305, 190)], power=True)
    d.text(288, 140, "24.4 W")
    # 5 V branches
    d.box(480, 20, 140, 60, ["VBUS switch", "per output"], fill=RED)
    d.box(680, 20, 155, 60, ["USB-C outputs", "5 V", "19.7 to 20.0 W"], fill=GREEN)
    d.line([(425, 170), (450, 170), (450, 50), (480, 50)], power=True)
    d.line([(620, 50), (680, 50)], power=True)
    d.text(455, 120, "5 V rail, 21.2 W", anchor="start")
    d.box(480, 160, 140, 60, ["3.3 V converter"], fill=RED)
    d.line([(425, 190), (480, 190)], power=True)
    d.box(680, 120, 155, 60, ["YT9215 3.3 V pins", "logic and analogue"], fill=BLUE)
    d.line([(620, 180), (650, 180), (650, 150), (680, 150)], power=True)
    d.box(680, 210, 155, 76, ["YT9215 regulator", "3.3 V to 1.15 V", "one inductor"], fill=BLUE)
    d.line([(620, 200), (650, 200), (650, 248), (680, 248)], power=True)
    d.box(680, 320, 155, 60, ["YT9215 core pins", "1.15 V"], fill=BLUE)
    d.line([(757, 286), (757, 320)], power=True)
    d.text(430, 262, "Switch supply: 1.2 to 1.5 W", anchor="start")
    d.text(430, 280, "taken from the 5 V rail", anchor="start")
    d.text(15, 300, "Power values are for a 25.5 W grant.", anchor="start")
    d.text(15, 318, "Bridge loss assumed: 1.1 W.", anchor="start")
    d.save(name)


block_diagram("option-a.svg", downstream=1, usb=1,
              cc_label=["PD transceiver", "or software"], cable_label=["USB-C", "output"])
block_diagram("option-b.svg", downstream=2, usb=2,
              cc_label=["PD transceiver", "or software"], cable_label=["USB-C"])
power_tree("power-tree.svg")
