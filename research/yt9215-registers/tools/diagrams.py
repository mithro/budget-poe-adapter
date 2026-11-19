"""Draw the block diagrams and the address map of the documentation as SVG.

Every function returns one ``<svg>`` element as text. The drawings use CSS
classes only; the colours come from ``docs/_static/yt921x.css`` when the SVG
is placed inline in a page, or from :data:`STYLE` when it is saved as a file.
Boxes can carry a link. WaveDrom draws the register, timing, sequence and
frame diagrams, through ``wavedrom_diagrams.py``.
"""
from html import escape

#: Colours for an SVG saved as a file. Inline SVGs use the page style sheet.
STYLE = """
.yt-d text{font-family:system-ui,-apple-system,'Segoe UI',Helvetica,Arial,sans-serif;font-size:15px;fill:#1c1e21}
.yt-d .yt-s{font-size:13px;fill:#5a6270}
.yt-d .yt-b{font-weight:600}
.yt-d .yt-box{fill:#eef4fb;stroke:#4b5563;stroke-width:1}
.yt-d .yt-sp{fill:#fdf1dc}
.yt-d .yt-rsv{fill:#eceef1}
.yt-d .yt-ln{stroke:#4b5563;stroke-width:1;fill:none}
.yt-d .yt-fill{fill:#4b5563}
"""


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

    def text(self, x, y, s, cls="", anchor="middle"):
        attr = ' class="%s"' % cls if cls else ""
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

