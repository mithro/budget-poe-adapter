"""Draw the diagrams of the documentation as SVG, with no dependencies.

Every function returns one ``<svg>`` element as text. The drawings use CSS
classes only; the colours come from ``docs/_static/yt921x.css`` when the SVG
is placed inline in a page, or from :data:`STYLE` when it is saved as a file.
Boxes can carry a link, so a field in a register diagram is a link to its
description.
"""
from html import escape

FONT = 15          # px, the sans-serif font of the page
CHAR = FONT * 0.58  # upper estimate of the mean advance of one character
SMALL = 13
CHAR_S = SMALL * 0.58

#: Colours for an SVG saved as a file. Inline SVGs use the page style sheet.
STYLE = """
.yt-d text{font-family:system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;font-size:15px;fill:#1c1e21}
.yt-d .yt-s{font-size:13px;fill:#5a6270}
.yt-d .yt-b{font-weight:600}
.yt-d .yt-box{fill:#eef4fb;stroke:#4b5563;stroke-width:1}
.yt-d .yt-ro{fill:#eaf6ec}
.yt-d .yt-sp{fill:#fdf1dc}
.yt-d .yt-rsv{fill:#eceef1}
.yt-d .yt-alt{fill:#f3ecfa}
.yt-d .yt-ln{stroke:#4b5563;stroke-width:1;fill:none}
.yt-d .yt-thin{stroke:#9aa3af;stroke-width:1;fill:none}
.yt-d .yt-dash{stroke:#9aa3af;stroke-width:1;stroke-dasharray:4 3;fill:none}
.yt-d .yt-sig{stroke:#1d4ed8;stroke-width:1.6;fill:none}
.yt-d .yt-fill{fill:#4b5563}
"""


def tw(text, small=False):
    """Width of a text in pixels."""
    return len(text) * (CHAR_S if small else CHAR)


class Svg:
    def __init__(self, width, height, label):
        self.w, self.h, self.label = width, height, label
        self.out = []

    def add(self, s):
        self.out.append(s)

    def rect(self, x, y, w, h, cls="yt-box", rx=0):
        self.add('<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" class="%s"%s/>'
                 % (x, y, w, h, cls, ' rx="%d"' % rx if rx else ""))

    def line(self, x1, y1, x2, y2, cls="yt-ln"):
        self.add('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" class="%s"/>'
                 % (x1, y1, x2, y2, cls))

    def path(self, d, cls="yt-ln"):
        self.add('<path d="%s" class="%s"/>' % (d, cls))

    def text(self, x, y, s, cls="", anchor="middle", rotate=False):
        attr = ' class="%s"' % cls if cls else ""
        if rotate:
            attr += ' transform="rotate(-90 %.1f %.1f)"' % (x, y)
        self.add('<text x="%.1f" y="%.1f" text-anchor="%s"%s>%s</text>'
                 % (x, y, anchor, attr, escape(s)))

    def arrow(self, x1, y1, x2, y2, cls="yt-ln"):
        """Line with an arrow head at (x2, y2); horizontal or vertical."""
        self.line(x1, y1, x2, y2, cls)
        if y1 == y2:
            d = 7 if x2 > x1 else -7
            pts = (x2, y2, x2 - d, y2 - 3.5, x2 - d, y2 + 3.5)
        else:
            d = 7 if y2 > y1 else -7
            pts = (x2, y2, x2 - 3.5, y2 - d, x2 + 3.5, y2 - d)
        self.add('<polygon points="%.1f,%.1f %.1f,%.1f %.1f,%.1f" class="yt-fill"/>' % pts)

    def open_link(self, href, tip=None):
        self.add('<a href="%s">' % escape(href, quote=True))
        if tip:
            self.add("<title>%s</title>" % escape(tip))

    def close_link(self):
        self.add("</a>")

    def render(self, standalone=False):
        style = "<style>%s</style>" % STYLE if standalone else ""
        ns = ' xmlns="http://www.w3.org/2000/svg"' if standalone else ""
        return ('<svg%s class="yt-d" viewBox="0 0 %d %d" width="%d" height="%d" role="img" '
                'aria-label="%s">%s%s</svg>'
                % (ns, self.w, self.h, self.w, self.h, escape(self.label, quote=True), style,
                   "".join(self.out)))


# ---------------------------------------------------------------- bit fields

ROW_BITS = 16      # bits drawn in one row, so that a bit is wide enough for a name
WIDTH = 748
PAD = 6


def bitfield(label, words, fields, bits=32):
    """Register diagram: rows of at most 16 bits, the highest bit on the left.

    ``fields`` is a list of dicts with ``name``, ``lsb``, ``width`` and
    optionally ``cls`` (box class), ``href``, ``tip`` and ``ticks`` (bit
    numbers where a thin divider is drawn, for arrays). A field that crosses
    the end of a row is drawn in both rows.
    """
    per = min(bits, ROW_BITS)
    cell = (WIDTH - 2 * PAD) // per
    total = words * bits
    rows = []
    for lo in range(total - per, -1, -per):
        hi = lo + per - 1
        segs = []
        for f in fields:
            a, b = max(f["lsb"], lo), min(f["lsb"] + f["width"] - 1, hi)
            if a <= b:
                segs.append((a, b, f))
        segs.sort(key=lambda s: -s[0])
        full, top = [], hi
        for a, b, f in segs:
            if b < top:
                full.append((b + 1, top, None))
            full.append((a, b, f))
            top = a - 1
        if top >= lo:
            full.append((lo, top, None))
        tall = 38
        for a, b, f in full:
            if f and tw(f["name"]) > (b - a + 1) * cell - 6:
                tall = max(tall, len(f["name"]) * FONT * 0.7 + 16)
        rows.append((lo, full, tall))
    width = per * cell + 2 * PAD
    height = sum(20 + t + 10 for _, _, t in rows) + 2
    s = Svg(width, height, label)
    y = 2
    for lo, full, tall in rows:
        ny, by = y + 15, y + 20
        for a, b, f in full:
            x = PAD + (per - 1 - (b - lo)) * cell
            w = (b - a + 1) * cell
            if f and f.get("href"):
                s.open_link(f["href"], f.get("tip"))
            s.rect(x, by, w, tall, "yt-box " + (f.get("cls", "") if f else "yt-rsv"))
            if f:
                for t in f.get("ticks", ()):
                    if a < t <= b:
                        tx = PAD + (per - 1 - (t - lo)) * cell + cell
                        s.line(tx, by + tall - 7, tx, by + tall, "yt-thin")
                if tw(f["name"]) <= w - 6:
                    s.text(x + w / 2, by + tall / 2 + 5, f["name"])
                else:
                    s.text(x + w / 2 + 5, by + tall / 2, f["name"], rotate=True)
            if f and f.get("href"):
                s.close_link()
            if a == b:
                s.text(x + w / 2, ny, str(a), "yt-s")
            else:
                s.text(x + 4, ny, str(b), "yt-s", "start")
                s.text(x + w - 4, ny, str(a), "yt-s", "end")
        y = by + tall + 10
    return s


# ------------------------------------------------------- strips of labelled boxes

def strip(label, rows, width=748, unit_labels=False):
    """Rows of labelled boxes with widths in proportion to their units.

    Each row is ``(row label, [cell, ...])``; a cell is a dict with ``units``,
    ``title`` and optionally ``sub`` (second line), ``top`` (small text above
    the box), ``cls``, ``href`` and ``tip``.
    """
    left = max([tw(r[0]) for r in rows] + [0])
    left = left + 12 if left else 0
    row_h = 0
    for _, cells in rows:
        row_h = max(row_h, 18 + (46 if any(c.get("sub") for c in cells) else 32) + 10)
    s = Svg(width, row_h * len(rows) + 2, label)
    y = 2
    for name, cells in rows:
        total = sum(c["units"] for c in cells)
        scale = (width - left - 2) / total
        box_h = row_h - 28
        if name:
            s.text(0, y + 18 + box_h / 2 + 5, name, "yt-b", "start")
        x = left + 1
        for c in cells:
            w = c["units"] * scale
            if c.get("href"):
                s.open_link(c["href"], c.get("tip"))
            s.rect(x, y + 18, w, box_h, "yt-box " + c.get("cls", ""))
            if c.get("sub"):
                s.text(x + w / 2, y + 18 + box_h / 2 - 3, c["title"], "yt-b")
                s.text(x + w / 2, y + 18 + box_h / 2 + 14, c["sub"], "yt-s")
            else:
                s.text(x + w / 2, y + 18 + box_h / 2 + 5, c["title"], "yt-b")
            if c.get("href"):
                s.close_link()
            if c.get("top"):
                s.text(x + w / 2, y + 13, c["top"], "yt-s")
            x += w
        y += row_h
    return s


# ------------------------------------------------------------ sequence diagrams

def sequence(label, actors, steps, width=748):
    """Message sequence between actors.

    ``steps`` holds ``(from, to, text)`` messages, ``("note", actor, text)``
    notes on one lifeline and ``("box", text)`` separators that span all
    lifelines. Actors are named by their index.
    """
    n = len(actors)
    margin = 70
    xs = [margin + i * (width - 2 * margin) / max(n - 1, 1) for i in range(n)]
    step_h = 34
    height = 34 + step_h * len(steps) + 14
    s = Svg(width, height, label)
    for x, a in zip(xs, actors):
        w = tw(a) + 18
        s.line(x, 26, x, height - 4, "yt-dash")
        s.rect(x - w / 2, 2, w, 24, "yt-box", 3)
        s.text(x, 18, a, "yt-b")
    y = 34
    for st in steps:
        mid = y + step_h / 2
        if st[0] == "note":
            _, actor, text = st
            w = tw(text) + 14
            x = min(max(xs[actor] - w / 2, 1), width - w - 1)
            s.rect(x, mid - 11, w, 22, "yt-box yt-sp", 3)
            s.text(x + w / 2, mid + 4, text)
        elif st[0] == "box":
            s.rect(1, mid - 11, width - 2, 22, "yt-box yt-rsv", 3)
            s.text(width / 2, mid + 4, st[1], "yt-b")
        else:
            a, b, text = st
            s.arrow(xs[a], mid + 6, xs[b], mid + 6)
            s.text((xs[a] + xs[b]) / 2, mid, text)
        y += step_h
    return s


# ------------------------------------------------------------------ pipelines

def pipeline(label, stages, per_row=4, width=748):
    """Chain of boxes joined by arrows, wrapped into rows.

    A stage is a dict with ``title``, ``lines`` (list of short texts) and
    optionally ``href`` and ``cls``.
    """
    gap = 26
    bw = (width - 2 - gap * (per_row - 1)) / per_row
    lines = max(len(st.get("lines", ())) for st in stages)
    bh = 28 + 16 * lines + 8
    nrows = (len(stages) + per_row - 1) // per_row
    s = Svg(width, nrows * (bh + gap) - gap + 2, label)
    for i, st in enumerate(stages):
        r, c = divmod(i, per_row)
        x, y = 1 + c * (bw + gap), 1 + r * (bh + gap)
        if st.get("href"):
            s.open_link(st["href"])
        s.rect(x, y, bw, bh, "yt-box " + st.get("cls", ""), 4)
        s.text(x + bw / 2, y + 20, st["title"], "yt-b")
        for k, t in enumerate(st.get("lines", ())):
            s.text(x + bw / 2, y + 39 + 16 * k, t, "yt-s")
        if st.get("href"):
            s.close_link()
        if i + 1 < len(stages):
            if c + 1 < per_row:
                s.arrow(x + bw, y + bh / 2, x + bw + gap, y + bh / 2)
            else:
                my = y + bh + gap / 2
                s.path("M%.1f %.1f V%.1f H%.1f" % (x + bw / 2, y + bh, my, 1 + bw / 2))
                s.arrow(1 + bw / 2, my, 1 + bw / 2, y + bh + gap)
    return s


# ---------------------------------------------------------------- address map

def addrmap(label, rows, width=748):
    """Stack of address regions, lowest address first.

    A row is a dict with ``addr`` (text), ``name``, ``title``, ``note`` and
    optionally ``href``; ``gap`` set draws a break above the row.
    """
    row_h = 30
    left = 84
    height = sum(row_h + (8 if r.get("gap") else 0) for r in rows) + 2
    s = Svg(width, height, label)
    y = 1
    for r in rows:
        if r.get("gap"):
            y += 8
        if r.get("href"):
            s.open_link(r["href"])
        s.rect(left, y, width - left - 1, row_h, "yt-box " + r.get("cls", ""))
        s.text(left + 10, y + 20, r["name"], "yt-b", "start")
        s.text(left + 130, y + 20, r["title"], "", "start")
        s.text(width - 10, y + 20, r.get("note", ""), "yt-s", "end")
        if r.get("href"):
            s.close_link()
        s.text(left - 8, y + 20, r["addr"], "", "end")
        y += row_h
    return s


# ------------------------------------------------------------------- waveforms

def smi_timing(label="MDC and MDIO timing of the management interface"):
    """MDC/MDIO timing with the six parameters of the datasheet."""
    s = Svg(748, 264, label)
    s.add('<g transform="translate(0 12)">')
    x0, per = 110, 200
    hi, lo = 40, 80
    s.text(8, 64, "MDC", "yt-b", "start")
    # clock: low, rise at x0+60, period 200, duty 50 %
    r1 = x0 + 60
    d = "M%d %d" % (x0, lo)
    x = r1
    for _ in range(3):
        d += " H%d V%d H%d V%d" % (x, hi, x + per // 2, lo)
        x += per
    d += " H%d" % 740
    s.path(d, "yt-sig")

    def dim(xa, xb, y, text, above=True):
        s.line(xa, y - 5, xa, y + 5, "yt-thin")
        s.line(xb, y - 5, xb, y + 5, "yt-thin")
        s.arrow(xa + 12, y, xa, y, "yt-thin")
        s.arrow(xb - 12, y, xb, y, "yt-thin")
        s.line(xa + 12, y, xb - 12, y, "yt-thin")
        s.text((xa + xb) / 2, y - 6 if above else y + 14, text)

    dim(r1, r1 + per, 14, "t1")
    dim(r1 + per, r1 + per + per // 2, 28, "t2")
    dim(r1 + per + per // 2, r1 + 2 * per, 28, "t3")
    # MDIO driven by the host: valid window around the first rising edge
    s.text(8, 132, "MDIO", "yt-b", "start")
    s.text(8, 146, "host drives", "yt-s", "start")
    ya, yb, ym = 115, 145, 130
    a, b = r1 - 44, r1 + 44
    s.path("M%d %d H%d L%d %d H%d L%d %d H%d M%d %d L%d %d H%d L%d %d"
           % (x0, ym, a - 8, a, ya, b, b + 8, ym, 740, a - 8, ym, a, yb, b, b + 8, ym), "yt-sig")
    s.text(r1, ym + 4, "valid")
    s.line(r1, hi, r1, 172, "yt-dash")
    dim(a, r1, 164, "t4", above=False)
    dim(r1, b, 164, "t5", above=False)
    # MDIO driven by the switch: changes t6 after a rising edge
    s.text(8, 212, "MDIO", "yt-b", "start")
    s.text(8, 226, "switch drives", "yt-s", "start")
    ya, yb, ym = 195, 225, 210
    r2 = r1 + per
    c = r2 + 60
    s.path("M%d %d H%d L%d %d H%d M%d %d H%d L%d %d H%d M%d %d L%d %d H%d M%d %d L%d %d H%d"
           % (x0, ya, c - 8, c, yb, 740, x0, yb, c - 8, c, ya, 740,
              c - 8, ya, c, ya, 740, c - 8, yb, c, yb, 740), "yt-sig")
    s.text((x0 + c) / 2, ym + 4, "bit n")
    s.text((c + 740) / 2, ym + 4, "bit n − 1")
    s.line(r2, hi, r2, 246, "yt-dash")
    dim(r2, c, 242, "t6", above=True)
    s.add("</g>")
    return s
