"""Tiny KiCad 7 schematic writer used by gen_schematic.py.

It loads symbols from the installed KiCad libraries (or from inline custom
definitions), places them, works out pin coordinates, and writes wires,
labels, power ports, sheets and graphics. Connectivity is checked afterwards
with `kicad-cli sch export netlist` (see gen_schematic.py).
"""
import os, re, uuid

LIBDIR = os.environ.get('KICAD7_SYMBOL_DIR', '/usr/share/kicad/symbols')
GRID = 1.27
_NS = uuid.UUID('6c782d69-7336-3031-662d-736368656d61')
_count = [0]


def U():
    """Next UUID in a fixed sequence, so regenerating gives identical files."""
    _count[0] += 1
    return str(uuid.uuid5(_NS, str(_count[0])))


# ------------------------------------------------------------ s-expressions
class Q(str):
    """A quoted string atom."""


def parse(text):
    tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))', re.S)
    pos, stack, cur = 0, [], []
    n = len(text)
    while pos < n:
        m = tok.match(text, pos)
        if not m:
            break
        pos = m.end()
        if m.group(1):
            stack.append(cur); cur = []
        elif m.group(2):
            done = cur; cur = stack.pop(); cur.append(done)
        elif m.group(3) is not None:
            cur.append(Q(m.group(3).replace('\\"', '"').replace('\\\\', '\\')))
        elif m.group(4):
            cur.append(m.group(4))
    return cur


def dump(node):
    if isinstance(node, list):
        return '(' + ' '.join(dump(x) for x in node) + ')'
    if isinstance(node, Q):
        return '"' + node.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n') + '"'
    if isinstance(node, float):
        return ('%.4f' % node).rstrip('0').rstrip('.')
    return str(node)


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


_libcache = {}


def _lib(name):
    if name not in _libcache:
        _libcache[name] = parse(open(os.path.join(LIBDIR, name + '.kicad_sym')).read())[0]
    return _libcache[name]


def _rename(node, old, new):
    for x in node:
        if isinstance(x, list) and x and x[0] == 'symbol' and isinstance(x[1], Q) and x[1].startswith(old + '_'):
            x[1] = Q(new + x[1][len(old):])


def load_lib_symbol(lib, name):
    """Return a flattened copy of lib:name as a symbol node named 'lib:name'."""
    import copy
    L = _lib(lib)
    syms = {x[1]: x for x in find(L, 'symbol')}
    node = copy.deepcopy(syms[name])
    ext = find(node, 'extends')
    if ext:
        base = copy.deepcopy(syms[ext[0][1]])
        _rename(base, ext[0][1], name)
        props = {p[1]: p for p in find(node, 'property')}
        out = [base[0], Q(name)]
        for x in base[2:]:
            if isinstance(x, list) and x and x[0] == 'property' and x[1] in props:
                out.append(props.pop(x[1]))
            else:
                out.append(x)
        # insert derived-only props before first sub-symbol
        extra = list(props.values())
        i = next(i for i, x in enumerate(out) if isinstance(x, list) and x[0] == 'symbol')
        out[i:i] = extra
        node = out
    node[1] = Q(lib + ':' + name)
    return node


def symbol_pins(sym):
    """{(unit, number): (x, y, angle, length, name)} from a symbol node."""
    base = sym[1].split(':')[-1]
    pins = {}
    for sub in find(sym, 'symbol'):
        m = re.match(re.escape(base) + r'_(\d+)_(\d+)$', sub[1])
        unit = int(m.group(1)) if m else 0
        for p in find(sub, 'pin'):
            at = find(p, 'at')[0]
            ln = find(p, 'length')[0][1]
            nm = find(p, 'name')[0][1]
            num = find(p, 'number')[0][1]
            pins.setdefault((unit, str(num)), (float(at[1]), float(at[2]), int(float(at[3]) if len(at) > 3 else 0), float(ln), str(nm)))
    return pins


def xform(x, y, rot, mirror=None):
    """Library coords -> offset in schematic coords (y down)."""
    if mirror == 'y':
        x = -x
    if mirror == 'x':
        y = -y
    r = rot % 360
    if r == 0:
        dx, dy = x, y
    elif r == 90:
        dx, dy = -y, x
    elif r == 180:
        dx, dy = -x, -y
    else:
        dx, dy = y, -x
    return dx, -dy


def snap(v):
    return round(round(v / GRID) * GRID, 4)


# ------------------------------------------------------------ custom symbols
def box_symbol(name, units, ref='U', value=None, w=20.32, pin_len=2.54, props=None, power_top_bottom=False):
    """Build a rectangular symbol node.

    units: list of dicts {'left': [...], 'right': [...], 'top': [...], 'bottom': [...], 'w': width}
    each pin entry: (number, name, etype) or None for a gap.
    """
    full = 'lxr:' + name
    nunits = len(units)
    out = [Q('symbol'), Q(full)]
    out = ['symbol', Q(full)]
    if nunits > 1:
        out.append(['unit_name_hint'] if False else ['in_bom', 'yes'])
    else:
        out.append(['in_bom', 'yes'])
    out.append(['on_board', 'yes'])
    hmax = 0
    out.append(['property', Q('Reference'), Q(ref), ['at', 0.0, 0.0, 0], ['effects', ['font', ['size', 1.27, 1.27]]]])
    out.append(['property', Q('Value'), Q(value or name), ['at', 0.0, 0.0, 0], ['effects', ['font', ['size', 1.27, 1.27]]]])
    out.append(['property', Q('Footprint'), Q(''), ['at', 0.0, 0.0, 0], ['effects', ['font', ['size', 1.27, 1.27]], 'hide']])
    out.append(['property', Q('Datasheet'), Q(''), ['at', 0.0, 0.0, 0], ['effects', ['font', ['size', 1.27, 1.27]], 'hide']])
    for k, v in (props or {}).items():
        out.append(['property', Q(k), Q(v), ['at', 0.0, 0.0, 0], ['effects', ['font', ['size', 1.27, 1.27]], 'hide']])
    for ui, u in enumerate(units, 1):
        L, R = u.get('left', []), u.get('right', [])
        T, B = u.get('top', []), u.get('bottom', [])
        uw = u.get('w', w)
        rows = max(len(L), len(R), 1)
        h = (rows + 1) * 2.54
        # widen for top/bottom pins
        cols = max(len(T), len(B))
        uw = max(uw, (cols + 1) * 2.54)
        uw = round(uw / 2.54) * 2.54
        h = round(h / 2.54) * 2.54
        x0, y0 = -uw / 2, h / 2
        gfx = ['symbol', Q('%s_%d_1' % (name, ui)),
               ['rectangle', ['start', x0, y0], ['end', -x0, -y0], ['stroke', ['width', 0.254], ['type', 'default']],
                ['fill', ['type', 'background']]]]
        for side, lst in (('L', L), ('R', R), ('T', T), ('B', B)):
            for i, pe in enumerate(lst):
                if pe is None:
                    continue
                num, nm, et = pe
                if side == 'L':
                    at = [x0 - pin_len, y0 - 2.54 * (i + 1), 0]
                elif side == 'R':
                    at = [-x0 + pin_len, y0 - 2.54 * (i + 1), 180]
                elif side == 'T':
                    at = [x0 + 2.54 * (i + 1), y0 + pin_len, 270]
                else:
                    at = [x0 + 2.54 * (i + 1), -y0 - pin_len, 90]
                gfx.append(['pin', et, 'line', ['at'] + at, ['length', pin_len],
                            ['name', Q(nm), ['effects', ['font', ['size', 1.016, 1.016]]]],
                            ['number', Q(num), ['effects', ['font', ['size', 1.016, 1.016]]]]])
        out.append(gfx)
        u['_h'] = h; u['_w'] = uw
    return out


# ------------------------------------------------------------ sheet writer
STYLE = {
    'C': ['stroke', ['width', 0.254], ['type', 'solid'], ['color', 0, 132, 0, 1]],
    'V': ['stroke', ['width', 0.254], ['type', 'solid'], ['color', 0, 72, 200, 1]],
    'I': ['stroke', ['width', 0.254], ['type', 'dash'], ['color', 214, 110, 0, 1]],
    'U': ['stroke', ['width', 0.254], ['type', 'dot'], ['color', 200, 0, 0, 1]],
    None: ['stroke', ['width', 0], ['type', 'default']],
}


class Part:
    def __init__(self, sheet, lib_id, ref, x, y, rot, mirror, unit, pins):
        self.sheet, self.lib_id, self.ref, self.x, self.y = sheet, lib_id, ref, x, y
        self.rot, self.mirror, self.unit, self._pins = rot, mirror, unit, pins

    def p(self, num):
        key = (self.unit, str(num))
        if key not in self._pins:
            key = (0, str(num))
        x, y, a, ln, nm = self._pins[key]
        dx, dy = xform(x, y, self.rot, self.mirror)
        return (round(self.x + dx, 4), round(self.y + dy, 4))

    def pdir(self, num):
        """Unit vector pointing away from the body at this pin (screen coords)."""
        key = (self.unit, str(num))
        if key not in self._pins:
            key = (0, str(num))
        x, y, a, ln, nm = self._pins[key]
        # pin angle: direction from connection point toward body; outward is opposite
        import math
        ox, oy = -math.cos(math.radians(a)), -math.sin(math.radians(a))
        dx, dy = xform(ox, oy, self.rot, self.mirror)
        return (round(dx), round(dy))



def textbox_height(s, w, size):
    """Estimate the height KiCad needs for text s word-wrapped in a box w mm wide."""
    cw = size * 0.92                      # average stroke-font advance incl. spacing
    per = max(8, int((w - 2.0) / cw))
    n = 0
    for para in s.split('\n'):
        line = 0
        words = para.split(' ')
        n += 1
        for wd in words:
            add = len(wd) + (1 if line else 0)
            if line and line + add > per:
                n += 1; line = len(wd)
            else:
                line += add
    return snap(n * size * 1.62 + 2.6)

class Sheet:
    def __init__(self, project, fname, title, paper='A3', page='1'):
        self.project, self.fname, self.title, self.paper, self.page = project, fname, title, paper, page
        self.uuid = U()
        self.lib = {}
        self.items = []
        self.symbols = []
        self.pins_used = []   # (ref, pin, net, conf)
        self.sheets = []
        self.comments = {}

    # library -----------------------------------------------------------
    def use(self, lib_id, node=None):
        if lib_id not in self.lib:
            if node is None:
                lib, name = lib_id.split(':')
                node = load_lib_symbol(lib, name)
            self.lib[lib_id] = node
        return self.lib[lib_id]

    # placement ---------------------------------------------------------
    def place(self, lib_id, ref, value, x, y, rot=0, mirror=None, unit=1, dnp=False, fields=None,
              node=None, show_value=True, ref_at=None, val_at=None, footprint='', center=None):
        center_override = center
        just = {}
        sym = self.use(lib_id, node)
        pins = symbol_pins(sym)
        x, y = snap(x), snap(y)
        if ref_at is None or val_at is None:
            props = {p[1]: p for p in find(sym, 'property')}
            def lp(name):
                at = find(props[name], 'at')[0] if name in props else None
                if at is None or (float(at[1]) == 0 and float(at[2]) == 0):
                    return None
                eff = find(props[name], 'effects')
                js = find(eff[0], 'justify') if eff else []
                if js and rot == 0 and not mirror:
                    just[name] = str(js[0][1])
                dx, dy = xform(float(at[1]), float(at[2]), rot, mirror)
                return (x + dx, y + dy)
            upins = [v for (u, n), v in pins.items() if u in (0, unit)]
            ys = [xform(px, py, rot, mirror)[1] for px, py, a, l, nm in upins] or [0]
            xs = [xform(px, py, rot, mirror)[0] for px, py, a, l, nm in upins] or [0]
            import math
            inner = [xform(px + l * math.cos(math.radians(a)), py + l * math.sin(math.radians(a)), rot, mirror)[0]
                     for px, py, a, l, nm in upins] or [0]
            lx = x + min(inner)
            center = set()
            if ref_at is None:
                ref_at = lp('Reference')
                if ref_at and 'Reference' not in just: center.add('ref')
                else: ref_at = (lx, y + min(ys) - 3.81)
            if val_at is None:
                val_at = lp('Value')
                if val_at and 'Value' not in just: center.add('val')
                else: val_at = (lx, y + max(ys) + 3.81)
        else:
            center = set()
        if center_override is not None:
            center = center_override
        part = Part(self, lib_id, ref, x, y, rot, mirror, unit, pins)
        self.symbols.append(dict(lib_id=lib_id, ref=ref, value=value, x=x, y=y, rot=rot, mirror=mirror,
                                 unit=unit, dnp=dnp, fields=fields or {}, pins=pins, show_value=show_value,
                                 ref_at=ref_at, val_at=val_at, footprint=footprint, center=center, just=just))
        return part

    def power(self, name, x, y, lib_name=None, rot=0):
        """Place a power port with its pin at (x, y). GND-like ports point down."""
        lib_name = lib_name or {'GND': 'GND', 'CHASSIS': 'Earth_Protective'}.get(name, None)
        lid = 'power:' + (lib_name or name)
        if lib_name and lib_name not in (name, 'PWR_FLAG', 'Earth_Protective'):
            # A rail the library lacks: copy a library port and give its pin the rail's
            # name, because KiCad names the net after the pin, not after the Value.
            node = parse(dump(load_lib_symbol('power', lib_name)).replace(lib_name, name))[0]
            lid, lib_name = 'power:' + name, name
            self.use(lid, node)
        self.use(lid)
        n = len([s for s in self.symbols if s['lib_id'].startswith('power:')]) + 1
        props = {p[1]: p for p in find(self.lib[lid], 'property')}
        at = find(props['Value'], 'at')[0]
        dx, dy = xform(float(at[1]), float(at[2]), rot)
        self.symbols.append(dict(lib_id=lid, ref='#PWR%03d' % n, value=name, x=snap(x), y=snap(y), rot=rot,
                                 mirror=None, unit=1, dnp=False, fields={}, pins=symbol_pins(self.lib[lid]),
                                 show_value=lib_name != 'PWR_FLAG', ref_at=(x, y), val_at=(x + dx, y + dy), footprint='',
                                 power=True, center={'ref', 'val'}))

    # wiring ------------------------------------------------------------
    def wire(self, pts, conf=None):
        pts = [(snap(a), snap(b)) for a, b in pts]
        for a, b in zip(pts, pts[1:]):
            if a != b:
                self.items.append(['wire', ['pts', ['xy', a[0], a[1]], ['xy', b[0], b[1]]], STYLE[conf], ['uuid', U()]])

    def route(self, a, b, conf=None, hfirst=None, xm=None):
        """Manhattan route. Default: horizontal - vertical (at mid x) - horizontal."""
        a = (snap(a[0]), snap(a[1])); b = (snap(b[0]), snap(b[1]))
        if a[0] == b[0] or a[1] == b[1]:
            self.wire([a, b], conf)
        elif hfirst is True:
            self.wire([a, (b[0], a[1]), b], conf)
        elif hfirst is False:
            self.wire([a, (a[0], b[1]), b], conf)
        else:
            if xm is None:
                xm = snap(round((a[0] + b[0]) / 2 / 2.54) * 2.54)
            xm = snap(xm)
            self.wire([a, (xm, a[1]), (xm, b[1]), b], conf)

    def junction(self, p):
        self.items.append(['junction', ['at', snap(p[0]), snap(p[1])], ['diameter', 0], ['color', 0, 0, 0, 0], ['uuid', U()]])

    def label(self, net, p, d, kind='label', shape='bidirectional', size=1.27):
        """d: outward direction (dx,dy) the label text should extend toward."""
        ang = {(1, 0): 0, (0, -1): 90, (-1, 0): 180, (0, 1): 270}[d]
        just = {0: 'left', 90: 'left', 180: 'right', 270: 'right'}[ang]
        eff = ['effects', ['font', ['size', size, size]], ['justify', just]]
        if kind == 'label':
            eff = ['effects', ['font', ['size', size, size]], ['justify', just, 'bottom']]
            self.items.append(['label', Q(net), ['at', snap(p[0]), snap(p[1]), ang], ['fields_autoplaced'], eff, ['uuid', U()]])
        elif kind == 'hier':
            self.items.append(['hierarchical_label', Q(net), ['shape', shape], ['at', snap(p[0]), snap(p[1]), ang],
                               ['fields_autoplaced'], eff, ['uuid', U()]])
        else:
            self.items.append(['global_label', Q(net), ['shape', shape], ['at', snap(p[0]), snap(p[1]), ang],
                               ['fields_autoplaced'], eff, ['uuid', U()],
                               ['property', Q('Intersheetrefs'), Q('${INTERSHEET_REFS}'), ['at', 0, 0, 0],
                                ['effects', ['font', ['size', 1.27, 1.27]], 'hide']]])

    def nc(self, p):
        self.items.append(['no_connect', ['at', snap(p[0]), snap(p[1])], ['uuid', U()]])

    def stub(self, part, num, net, conf='I', length=5.08, kind='label', shape='bidirectional', near=False):
        """Short wire out of a pin ending in a label. near=True anchors a local label
        2.54 mm from the pin so its text sits on the wire, clear of anything at the far end."""
        p = part.p(num)
        d = part.pdir(num)
        e = (p[0] + d[0] * length, p[1] + d[1] * length)
        self.wire([p, e], conf)
        self.label(net, (p[0] + d[0] * 2.54, p[1] + d[1] * 2.54) if near else e, d, kind, shape)
        self.pins_used.append((part.ref, str(num), net, conf))
        return e

    def pin_power(self, part, num, net, conf='I', length=2.54):
        p = part.p(num)
        d = part.pdir(num)
        e = (p[0] + d[0] * length, p[1] + d[1] * length)
        self.wire([p, e], conf)
        down = net in ('GND', 'CHASSIS')
        self.power(net, e[0], e[1], rot=0 if (down or d[1] <= 0) else 180) if not down else self.power(net, e[0], e[1])
        self.pins_used.append((part.ref, str(num), net, conf))

    def mark(self, part, num, net, conf):
        self.pins_used.append((part.ref, str(num), net, conf))

    # graphics ----------------------------------------------------------
    def text(self, s, x, y, size=1.27, bold=False, italic=False, color=None, justify='left'):
        f = ['font', ['size', size, size]]
        if bold: f.append('bold')
        if italic: f.append('italic')
        if color: f.append(['color'] + list(color) + [1])
        self.items.append(['text', Q(s), ['at', snap(x), snap(y), 0], ['effects', f, ['justify', justify, 'top']], ['uuid', U()]])

    def frame(self, x1, y1, x2, y2, title=None, color=(110, 110, 110)):
        self.items.append(['rectangle', ['start', snap(x1), snap(y1)], ['end', snap(x2), snap(y2)],
                           ['stroke', ['width', 0.254], ['type', 'dash'], ['color'] + list(color) + [1]],
                           ['fill', ['type', 'none']], ['uuid', U()]])
        if title:
            self.text(title, x1 + 2.54, y1 + 2.54, size=2.0, bold=True, color=(0, 0, 132))

    def textbox(self, s, x, y, w, h=None, size=1.27, fill=(255, 255, 225)):
        """Text box w wide; the height is fitted to the wrapped text (h is ignored)."""
        h = textbox_height(s, w, size)
        self.items.append(['text_box', Q(s), ['at', snap(x), snap(y), 0], ['size', snap(w), snap(h)],
                           ['stroke', ['width', 0.1524], ['type', 'solid'], ['color', 120, 120, 120, 1]],
                           ['fill', ['type', 'color'], ['color'] + list(fill) + [1]],
                           ['effects', ['font', ['size', size, size]], ['justify', 'left', 'top']], ['uuid', U()]])

    def subsheet(self, child, x, y, w, h, pins):
        """pins: list of (name, side 'L'/'R', etype)."""
        node = ['sheet', ['at', snap(x), snap(y)], ['size', snap(w), snap(h)], ['fields_autoplaced'],
                ['stroke', ['width', 0.1524], ['type', 'solid']], ['fill', ['color', 255, 255, 240, 1]], ['uuid', child.uuid],
                ['property', Q('Sheetname'), Q(child.title), ['at', snap(x), snap(y) - 0.7116, 0],
                 ['effects', ['font', ['size', 1.524, 1.524], 'bold'], ['justify', 'left', 'bottom']]],
                ['property', Q('Sheetfile'), Q(child.fname), ['at', snap(x), snap(y + h) + 0.5846, 0],
                 ['effects', ['font', ['size', 1.27, 1.27]], ['justify', 'left', 'top']]]]
        pos = {}
        li = ri = 0
        for name, side, et in pins:
            if side == 'L':
                li += 1; px, py, ang, j = x, y + 2.54 * li + 2.54, 180, 'left'
            else:
                ri += 1; px, py, ang, j = x + w, y + 2.54 * ri + 2.54, 0, 'right'
            node.append(['pin', Q(name), et, ['at', snap(px), snap(py), ang],
                         ['effects', ['font', ['size', 1.27, 1.27]], ['justify', j]], ['uuid', U()]])
            pos[name] = (snap(px), snap(py))
        self.sheets.append((child, node))
        return pos

    # output ------------------------------------------------------------
    def _split_wires(self):
        """Break wires where a junction or another wire's end lands mid-segment,
        so kicad-cli (which does not do this on load) sees the connection."""
        flat = []
        for x in self.items:
            if x[0] in ('wire', 'bus') and len(x[1]) > 3:
                for a, b in zip(x[1][1:], x[1][2:]):
                    flat.append([x[0], ['pts', a, b], x[2], ['uuid', U()]])
            else:
                flat.append(x)
        self.items = flat
        wires = [x for x in self.items if x[0] in ('wire', 'bus')]
        others = [x for x in self.items if x[0] not in ('wire', 'bus')]
        pts = set()
        for x in self.items:
            if x[0] == 'junction':
                pts.add((x[1][1], x[1][2]))
        for w in wires:
            pts.add((w[1][1][1], w[1][1][2])); pts.add((w[1][2][1], w[1][2][2]))
        out = []
        for w in wires:
            (x1, y1), (x2, y2) = (w[1][1][1], w[1][1][2]), (w[1][2][1], w[1][2][2])
            cuts = []
            for (px, py) in pts:
                if (px, py) in ((x1, y1), (x2, y2)):
                    continue
                if x1 == x2 == px and min(y1, y2) < py < max(y1, y2):
                    cuts.append((px, py))
                elif y1 == y2 == py and min(x1, x2) < px < max(x1, x2):
                    cuts.append((px, py))
            if not cuts:
                out.append(w); continue
            seq = sorted(cuts + [(x1, y1), (x2, y2)], key=lambda p: (p[0] - x1) ** 2 + (p[1] - y1) ** 2)
            for a, b in zip(seq, seq[1:]):
                out.append([w[0], ['pts', ['xy', a[0], a[1]], ['xy', b[0], b[1]]], w[2], ['uuid', U()]])
        deg = {}
        for w in out:
            if w[0] != 'wire' or (w[1][1][1], w[1][1][2]) == (w[1][2][1], w[1][2][2]):
                continue
            for e in (w[1][1], w[1][2]):
                deg[(e[1], e[2])] = deg.get((e[1], e[2]), 0) + 1
        have = {(x[1][1], x[1][2]) for x in others if x[0] == 'junction'}
        for p, d in deg.items():
            if d >= 3 and p not in have:
                others.append(['junction', ['at', p[0], p[1]], ['diameter', 0], ['color', 0, 0, 0, 0], ['uuid', U()]])
        self.items = out + others

    def render(self, root_uuid, path):
        self._split_wires()
        out = ['kicad_sch', ['version', 20230121], ['generator', 'eeschema'], ['uuid', self.uuid],
               ['paper', Q(self.paper)],
               ['title_block', ['title', Q(self.project['title'])], ['date', Q(self.project['date'])],
                ['rev', Q(self.project['rev'])], ['company', Q(self.project['company'])]] +
               [['comment', i, Q(c)] for i, c in sorted(self.comments.items())]]
        out.append(['lib_symbols'] + list(self.lib.values()))
        out += self.items
        for s in self.symbols:
            ent = ['symbol', ['lib_id', Q(s['lib_id'])], ['at', s['x'], s['y'], s['rot']]]
            if s['mirror']:
                ent.append(['mirror', s['mirror']])
            ent += [['unit', s['unit']], ['in_bom', 'no' if s.get('power') else 'yes'], ['on_board', 'yes'],
                    ['dnp', 'yes' if s['dnp'] else 'no'], ['uuid', U()]]
            rx, ry = s['ref_at'] or (s['x'] + 2.54, s['y'] - 1.27)
            vx, vy = s['val_at'] or (s['x'] + 2.54, s['y'] + 1.27)
            c = s.get('center', set())
            fa = 90 if s['rot'] in (90, 270) else 0   # keeps field text horizontal on rotated parts
            ent.append(['property', Q('Reference'), Q(s['ref']), ['at', round(rx, 3), round(ry, 3), fa],
                        ['effects', ['font', ['size', 1.27, 1.27]]] + ([] if 'ref' in c else [['justify', s.get('just', {}).get('Reference', 'left')]]) + (['hide'] if s.get('power') else [])])
            ent.append(['property', Q('Value'), Q(s['value']), ['at', round(vx, 3), round(vy, 3), fa],
                        ['effects', ['font', ['size', 1.27, 1.27]]] + ([] if 'val' in c else [['justify', s.get('just', {}).get('Value', 'left')]]) + ([] if s['show_value'] else ['hide'])])
            ent.append(['property', Q('Footprint'), Q(s['footprint']), ['at', s['x'], s['y'], 0],
                        ['effects', ['font', ['size', 1.27, 1.27]], 'hide']])
            ent.append(['property', Q('Datasheet'), Q(''), ['at', s['x'], s['y'], 0],
                        ['effects', ['font', ['size', 1.27, 1.27]], 'hide']])
            for k, v in s['fields'].items():
                ent.append(['property', Q(k), Q(v), ['at', s['x'], s['y'], 0], ['effects', ['font', ['size', 1.27, 1.27]], 'hide']])
            nums = sorted({n for (u, n) in s['pins'] if u in (0, s['unit'])})
            for n in nums:
                ent.append(['pin', Q(n), ['uuid', U()]])
            ent.append(['instances', ['project', Q(self.project['name']),
                                      ['path', Q(path), ['reference', Q(s['ref'])], ['unit', s['unit']]]]])
            out.append(ent)
        for child, node in self.sheets:
            node = list(node)
            node.append(['instances', ['project', Q(self.project['name']),
                                       ['path', Q(path), ['page', Q(child.page)]]]])
            out.append(node)
        if path == '/' + root_uuid:
            out.append(['sheet_instances', ['path', Q('/'), ['page', Q(self.page)]]])
        self._shift(out)
        self._check_margins(out)
        return pretty(out)

    # page padding -------------------------------------------------------
    PAPER = {'A4': (297, 210), 'A3': (420, 297), 'A2': (594, 420), 'A1': (841, 594)}
    MARGIN = 10.0                     # clear space inside the page border (mm)
    BORDER = 12.0                     # inner line of KiCad's drawing border (mm)
    TITLE_BLOCK = (108.0, 32.0)       # title block, measured from the inner border line (mm)
    offset = (10.16, 10.16)           # everything is drawn this far right/down

    def _shift(self, out):
        dx, dy = self.offset
        def walk(n):
            if not isinstance(n, list) or not n:
                return
            if n[0] in ('at', 'start', 'end', 'xy') and len(n) >= 3 and isinstance(n[1], (int, float)):
                n[1] = round(n[1] + dx, 4); n[2] = round(n[2] + dy, 4)
                return
            for c in n[1:]:
                walk(c)
        for item in out[1:]:
            if isinstance(item, list) and item and item[0] not in ('lib_symbols', 'title_block', 'sheet_instances'):
                walk(item)

    @staticmethod
    def _text_extents(item):
        """Estimated far end of each visible string in item (stroke font, about 0.9 x size per character)."""
        out = []
        def far(text, at, eff):
            if 'hide' in eff[0] if eff else False:
                return
            size = find(find(eff[0], 'font')[0], 'size')[0][1] if eff else 1.27
            js = [str(j) for j in find(eff[0], 'justify')[0][1:]] if eff and find(eff[0], 'justify') else []
            lines = str(text).split('\n')
            n = max(len(l) for l in lines) * size * 0.9
            ang = at[3] if len(at) > 3 else 0
            sgn = -1 if 'right' in js else 1
            half = 0 if ('left' in js or 'right' in js) else 0.5
            for f in ((1 - half) * sgn, -half * sgn):
                d = n * f
                if ang in (90, 270):
                    out.append((at[1], at[2] - d))
                else:
                    out.append((at[1] + d, at[2] + (len(lines) - 1) * size * 1.62))
        if item[0] in ('text', 'label', 'hierarchical_label', 'global_label'):
            far(item[1], find(item, 'at')[0], find(item, 'effects'))
        for p in find(item, 'property'):
            if p[1] not in ('Footprint', 'Datasheet', 'Intersheetrefs') and 'hide' not in str(find(p, 'effects')):
                far(p[2], find(p, 'at')[0], find(p, 'effects'))
        return out

    def _check_margins(self, out):
        """Report anything closer than MARGIN to the page border or the title block."""
        W, H = self.PAPER[self.paper]
        lo, hix, hiy = self.BORDER + self.MARGIN, W - self.BORDER - self.MARGIN, H - self.BORDER - self.MARGIN
        tbx, tby = W - self.BORDER - self.TITLE_BLOCK[0] - self.MARGIN, H - self.BORDER - self.TITLE_BLOCK[1] - self.MARGIN
        bad = []
        for item in out[1:]:
            if not isinstance(item, list) or not item or item[0] in ('lib_symbols', 'title_block', 'sheet_instances'):
                continue
            pts = []
            def walk(n):
                if not isinstance(n, list) or not n:
                    return
                if n[0] in ('at', 'start', 'end', 'xy') and len(n) >= 3 and isinstance(n[1], (int, float)):
                    pts.append((n[1], n[2])); return
                if n[0] == 'property' and n[1] in ('Footprint', 'Datasheet', 'Intersheetrefs'):
                    return
                for c in n[1:]:
                    walk(c)
            walk(item if item[0] != 'symbol' else [x for x in item if not (isinstance(x, list) and x and x[0] == 'property' and 'hide' in str(x))])
            if item[0] in ('text_box', 'sheet'):
                at, sz = find(item, 'at')[0], find(item, 'size')[0]
                pts.append((at[1] + sz[1], at[2] + sz[2]))
            pts += self._text_extents(item)
            for x, y in pts:
                if x < lo or y < lo or x > hix or y > hiy or (x > tbx and y > tby):
                    bad.append((item[0], round(x, 1), round(y, 1)))
                    break
        self.margin_report = bad



def pretty(node, ind=0):
    """Indent top-level and second-level lists for readable diffs."""
    if not isinstance(node, list):
        return dump(node)
    head = '(' + dump(node[0])
    parts = []
    for x in node[1:]:
        if isinstance(x, list) and ind < 2 and len(dump(x)) > 100:
            parts.append('\n' + '  ' * (ind + 1) + pretty(x, ind + 1))
        else:
            parts.append(' ' + dump(x) if not isinstance(x, list) or ind >= 1 else '\n' + '  ' * (ind + 1) + dump(x))
    return head + ''.join(parts) + ')'
