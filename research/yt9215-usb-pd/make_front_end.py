#!/usr/bin/env python3
"""Draw front-end.svg: the parts between the YT9215 pins and the USB-C connector."""
import pathlib

W, H = 850, 640
out = []


def box(x, y, w, h, lines, fill="#f4f6fa"):
    out.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="#222" stroke-width="1.5"/>'
               % (x, y, w, h, fill))
    y0 = y + h / 2 - (len(lines) - 1) * 9
    for i, line in enumerate(lines):
        weight = "bold" if i == 0 else "normal"
        out.append('<text x="%d" y="%d" text-anchor="middle" dominant-baseline="middle" font-weight="%s">%s</text>'
                   % (x + w / 2, y0 + i * 18, weight, line))


def arrow(x1, y1, x2, y2, label="", above=True, both=False):
    out.append('<line x1="%d" y1="%d" x2="%d" y2="%d" stroke="#222" stroke-width="1.5" marker-end="url(#a)"%s/>'
               % (x1, y1, x2, y2, ' marker-start="url(#b)"' if both else ""))
    if label:
        out.append('<text x="%d" y="%d" text-anchor="middle">%s</text>'
                   % ((x1 + x2) / 2, (y1 + y2) / 2 + (-7 if above else 18), label))


out.append('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d" '
           'font-family="DejaVu Sans, Arial, sans-serif" font-size="14">' % (W, H, W, H))
out.append('<defs><marker id="a" markerWidth="9" markerHeight="8" refX="8" refY="4" orient="auto">'
           '<path d="M0,0 L9,4 L0,8 z" fill="#222"/></marker>'
           '<marker id="b" markerWidth="9" markerHeight="8" refX="1" refY="4" orient="auto">'
           '<path d="M9,0 L0,4 L9,8 z" fill="#222"/></marker></defs>')
out.append('<rect width="%d" height="%d" fill="#ffffff"/>' % (W, H))

box(20, 20, 150, 600, ["YT9215SCH"], fill="#e8eefc")
box(680, 20, 150, 600, ["USB-C cable"], fill="#e8f6e8")
out.append('<text x="95" y="48" text-anchor="middle">port 9 pins</text>')
out.append('<text x="95" y="400" text-anchor="middle">GPIO pins</text>')

# Transmit path
box(300, 40, 190, 70, ["Buffer with enable", "74AUP1G126", "supply 1.15 V"])
arrow(170, 60, 300, 60, "TXD1, pin 48")
arrow(170, 92, 300, 92, "TX_CTL, pin 50", above=False)
box(540, 50, 90, 50, ["47 Ω"])
arrow(490, 75, 540, 75)
arrow(630, 75, 680, 75, "CC")

# Protection shared by both comparators
box(540, 150, 90, 170, ["1 kΩ", "and", "clamp"])
arrow(680, 235, 630, 235, "CC")

# Receive path
box(300, 150, 190, 70, ["Comparator 1", "threshold 0.55 V", "output inverted"])
arrow(540, 185, 490, 185)
arrow(300, 185, 170, 185, "RXD3, pin 57")

# Attach detection
box(300, 250, 190, 70, ["Comparator 2", "threshold 2.6 V", "attach detect"])
arrow(540, 285, 490, 285)
arrow(300, 285, 170, 285, "GPIO input")

# Fixed wiring of the receive side
box(300, 345, 330, 80, ["Fixed wiring for receive", "RXD0 and RXD2 to 3.3 V, RXD1 to ground",
                        "TXC, pin 51, looped to RXC, pin 52"], fill="#fbf7e6")
arrow(170, 385, 300, 385, "RX_CTL, pin 53")
out.append('<text x="235" y="403" text-anchor="middle">from a GPIO</text>')

# Rp
box(300, 450, 190, 70, ["Rp", "12 kΩ to a GPIO", "7.5 kΩ to a GPIO"])
arrow(170, 485, 300, 485, "2 GPIO outputs")
arrow(490, 485, 680, 485, "CC")

# VBUS switch
box(300, 545, 190, 60, ["Load switch", "with discharge"])
arrow(170, 575, 300, 575, "GPIO output")
arrow(490, 575, 680, 575, "VBUS, 5 V")

out.append("</svg>")
pathlib.Path(__file__).with_name("front-end.svg").write_text("\n".join(out), encoding="utf-8")
