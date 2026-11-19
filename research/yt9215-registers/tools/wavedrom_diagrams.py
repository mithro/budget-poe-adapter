"""Render WaveDrom sources as inline SVG.

A source is the WaveDrom JSON of a waveform (``signal``) or of a register
(``reg``), as a dict. The JavaScript renderer of WaveDrom draws it, through
``wavedrom/render.js`` and Node.js; ``npm ci`` in ``tools/wavedrom`` installs
the renderer. :func:`register` builds the source of a register from its
fields, and picks the row length and the direction of each name so that
every name fits its box.
"""
import atexit
import json
import os
import re
import subprocess
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
NODE_DIR = os.path.join(HERE, "wavedrom")

WIDTH = 732          # px, the width of a register diagram: the page column of the theme
FONT = 14            # px, text of a register diagram
FONT_FAMILY = "Helvetica, Arial, sans-serif"   # the fonts of the WaveDrom waveform skin
CHAR = FONT * 0.66   # px, upper estimate of the mean advance of one character
PAD = 8              # px between a name and its box
ARC_FONT = 13        # px, labels on the arrows of a waveform
ROW = 70             # px, height of one row of a register diagram
ROW_EXTRA = 1.5 * FONT + 4   # px that WaveDrom keeps of a row for the bit numbers

#: WaveDrom field types (fill colours) of the kinds of field.
TYPE_READ_ONLY = 6
TYPE_LAYOUT = 7


def text_width(text):
    return len(text) * CHAR


def segments(lsb, width, per):
    """Bit counts of the parts of a field in each row it touches, lowest row first."""
    out, a, hi = [], lsb, lsb + width - 1
    while a <= hi:
        e = min(hi, (a // per + 1) * per - 1)
        out.append(e - a + 1)
        a = e + 1
    return out


def register(fields, bits=32):
    """WaveDrom source of a register.

    ``fields`` is a list of dicts with ``name``, ``lsb``, ``width`` and
    optionally ``type`` (a WaveDrom field type). Bits that no field covers
    become unnamed fields, which WaveDrom shades. A row holds 32 bits. A name
    that is wider than its box is drawn upwards, and the rows are as tall as
    the longest such name.
    """
    per = 32 if bits % 32 == 0 else bits
    cell = (WIDTH - 9) / per
    vspace = ROW
    reg, pos = [], 0
    for f in sorted(fields, key=lambda f: f["lsb"]):
        if f["lsb"] > pos:
            reg.append({"bits": f["lsb"] - pos})
        e = {"name": f["name"], "bits": f["width"]}
        if text_width(f["name"]) > min(segments(f["lsb"], f["width"], per)) * cell - PAD:
            e["rotate"] = -90
            vspace = max(vspace, int(text_width(f["name"]) + 2 * PAD + ROW_EXTRA))
        if f.get("type"):
            e["type"] = f["type"]
        reg.append(e)
        pos = f["lsb"] + f["width"]
    if pos < bits:
        reg.append({"bits": bits - pos})
    return {"reg": reg, "config": {"bits": bits, "lanes": bits // per, "vspace": vspace}}


class RenderError(Exception):
    pass


_worker = {}


def _node():
    """The renderer process of this Python process."""
    proc = _worker.get(os.getpid())
    if proc is None or proc.poll() is not None:
        if not os.path.isdir(os.path.join(NODE_DIR, "node_modules", "wavedrom")):
            raise RenderError("WaveDrom is not installed: run 'npm ci' in " + NODE_DIR)
        try:
            proc = subprocess.Popen(["node", os.path.join(NODE_DIR, "render.js")],
                                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                                    encoding="utf-8")
        except OSError as err:
            raise RenderError("Node.js is needed to draw the WaveDrom diagrams: %s" % err)
        _worker[os.getpid()] = proc
        atexit.register(_stop, proc)
    return proc


def _stop(proc):
    if proc.poll() is None:
        proc.stdin.close()
        proc.wait()


_cache = {}


def draw(source):
    """SVG text of a WaveDrom source, as WaveDrom writes it."""
    key = json.dumps(source, sort_keys=True)
    if key not in _cache:
        proc = _node()
        proc.stdin.write(key + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        if not line:
            raise RenderError("the WaveDrom renderer stopped")
        out = json.loads(line)
        if "error" in out:
            raise RenderError("WaveDrom cannot draw the source: " + out["error"])
        _cache[key] = out["svg"]
    return _cache[key]


def scope_style(svg):
    """Limit the style sheet of a waveform to WaveDrom drawings.

    The skin of WaveDrom styles every ``text`` element and classes such as
    ``warning``; inside a page those rules would reach other content. The
    rules of the classes ``s1``, ``s2`` and so on stay as they are: they
    style the shapes that the drawing clones with ``use``, where a selector
    cannot name an ancestor.
    """
    def rule(r):
        selector = r.group(2).strip()
        if not re.fullmatch(r"\.s\d+", selector):
            selector = "svg.WaveDrom " + selector
        return "%s%s{" % (r.group(1), selector)

    def scoped(m):
        return m.group(1) + re.sub(r"(^|\})\s*([^{}]+)\{", rule, m.group(2)) + m.group(3)
    return re.sub(r"(<style[^>]*>)(.*?)(</style>)", scoped, svg, flags=re.S)


def add_links(svg, links):
    """Make the names of a register diagram links.

    ``links`` maps a field name to ``(href, tooltip)``.
    """
    def linked(m):
        link = links.get(m.group(2))
        if not link:
            return m.group(0)
        title = "<title>%s</title>" % escape(link[1]) if link[1] else ""
        return '<a href="%s">%s%s</a>' % (escape(link[0], quote=True), title, m.group(0))
    return re.sub(r"(<text[^>]*>)<tspan>([^<]*)</tspan></text>", linked, svg)


def render(source, label, links=None):
    """Inline ``<svg>`` element of a WaveDrom source."""
    source = json.loads(json.dumps(source))
    config = source.setdefault("config", {})
    if source.get("reg"):
        config.setdefault("hspace", WIDTH)
        config.setdefault("vspace", ROW)
        config.setdefault("fontsize", FONT)
        config.setdefault("fontfamily", FONT_FAMILY)
    else:
        config.setdefault("arcFontSize", ARC_FONT)
    svg = draw(source)
    if source.get("signal"):
        svg = scope_style(svg)
    if links:
        svg = add_links(svg, {escape(k): v for k, v in links.items()})
    svg = re.sub(r'^<svg id="[^"]*"', "<svg", svg)
    return svg.replace("<svg", '<svg role="img" aria-label="%s"' % escape(label, quote=True), 1)
