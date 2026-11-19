"""Render WaveDrom sources as inline SVG.

A source is the WaveDrom JSON of a waveform (``signal``) or of a register
(``reg``), as a dict. The JavaScript renderer of WaveDrom draws it, through
``wavedrom/render.js`` and Node.js; ``npm ci`` in ``tools/wavedrom`` installs
the renderer. :func:`register` builds the sources of a register from its
fields, one per 32-bit word, and picks the direction of each name so that
every name fits its box.
"""
import atexit
import hashlib
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


def register(fields, bits=32):
    """WaveDrom sources of a register, the highest 32-bit word first.

    ``fields`` is a list of dicts with ``name``, ``lsb``, ``width`` and
    optionally ``type`` (a WaveDrom field type) and ``link``. Bits that no
    field covers become unnamed fields, which WaveDrom shades. A name that
    is wider than its box is drawn upwards, and the row is as tall as its
    longest such name. Each source comes with the ``link`` values of its
    named fields, lowest bit first.
    """
    fields = sorted(fields, key=lambda f: f["lsb"])
    for a, b in zip(fields, fields[1:]):
        if a["lsb"] + a["width"] > b["lsb"]:
            raise ValueError("fields %s and %s overlap" % (a["name"], b["name"]))
    per = 32 if bits % 32 == 0 else bits
    cell = (WIDTH - 9) / per
    out = []
    for base in range(bits - per, -1, -per):
        height = ROW - ROW_EXTRA
        reg, links, pos = [], [], base
        for f in fields:
            lo, hi = max(f["lsb"], base), min(f["lsb"] + f["width"], base + per)
            if lo >= hi:
                continue
            if lo > pos:
                reg.append({"bits": lo - pos})
            e = {"name": f["name"], "bits": hi - lo}
            if text_width(f["name"]) > (hi - lo) * cell - PAD:
                e["rotate"] = -90
                # WaveDrom draws a tick of an eighth of the height at each end of
                # every bit boundary inside a field.
                need = text_width(f["name"]) + 2 * PAD
                height = max(height, need if hi - lo == 1 else need / 0.75)
            if f.get("type"):
                e["type"] = f["type"]
            reg.append(e)
            links.append(f.get("link"))
            pos = hi
        if pos < base + per:
            reg.append({"bits": base + per - pos})
        config = {"bits": per, "vspace": int(height + ROW_EXTRA + 1)}
        if base:
            config["offset"] = base
        out.append(({"reg": reg, "config": config}, links))
    return out


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
    """Limit the style sheet of a waveform to waveforms.

    The skin of WaveDrom styles every ``text`` element and classes such as
    ``warning``; inside a page those rules would reach other content. The
    rules of the classes ``s1``, ``s2`` and so on stay as they are: they
    style the shapes that the drawing clones with ``use``, where a selector
    cannot name an ancestor.
    """
    def rule(r):
        selector = r.group(2).strip()
        if not re.fullmatch(r"\.s\d+", selector):
            selector = "svg.yt-wave " + selector
        return "%s%s{" % (r.group(1), selector)

    def scoped(m):
        return m.group(1) + re.sub(r"(^|\})\s*([^{}]+)\{", rule, m.group(2)) + m.group(3)
    svg = re.sub(r"(<style[^>]*>)(.*?)(</style>)", scoped, svg, flags=re.S)
    return svg.replace('class="WaveDrom"', 'class="WaveDrom yt-wave"', 1)


def unique_ids(svg, prefix):
    """Give the ids of a waveform a prefix, so that two waveforms in one page share none."""
    svg = re.sub(r'\bid="([^"]+)"', lambda m: 'id="%s-%s"' % (prefix, m.group(1)), svg)
    svg = re.sub(r'href="#([^"]+)"', lambda m: 'href="#%s-%s"' % (prefix, m.group(1)), svg)
    return re.sub(r"url\(#([^)]+)\)", lambda m: "url(#%s-%s)" % (prefix, m.group(1)), svg)


def add_links(svg, reg, links):
    """Make the names of a register diagram links.

    ``links`` holds ``(href, tooltip)`` or None for each named field of
    ``reg``, in the order of the fields. WaveDrom writes the names in that
    order, and the bit numbers of a row before its names.
    """
    todo = [(escape(e["name"]), link) for e, link in
            zip([e for e in reg if e.get("name")], links)]

    def linked(m):
        if not todo or m.group(2) != todo[0][0]:
            return m.group(0)
        link = todo.pop(0)[1]
        if not link:
            return m.group(0)
        title = "<title>%s</title>" % escape(link[1]) if link[1] else ""
        return '<a href="%s">%s%s</a>' % (escape(link[0], quote=True), title, m.group(0))
    svg = re.sub(r"(<text[^>]*>)<tspan>([^<]*)</tspan></text>", linked, svg)
    if todo:
        raise RenderError("WaveDrom did not draw the name " + todo[0][0])
    return svg


def render(source, label, links=None):
    """Inline ``<svg>`` element of a WaveDrom source.

    ``links`` holds ``(href, tooltip)`` or None for each named field of a
    register source.
    """
    if not isinstance(source, dict) or not (source.get("reg") or source.get("signal")):
        raise RenderError('a WaveDrom source is an object with "signal" or "reg"')
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
        key = json.dumps(source, sort_keys=True).encode("utf-8")
        svg = unique_ids(scope_style(svg), "w" + hashlib.sha1(key).hexdigest()[:8])
    elif links:
        svg = add_links(svg, source["reg"], links)
    return svg.replace("<svg", '<svg role="img" aria-label="%s"' % escape(label, quote=True), 1)
