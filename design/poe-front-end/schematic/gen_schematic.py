#!/usr/bin/env python3
"""Draws the KiCad schematic of the discrete PoE front end and checks it against the simulated circuit.

    python3 gen_schematic.py

Writes poe-front-end.kicad_sch, exports poe-front-end.pdf and the images in renders/ with kicad-cli
and pdftoppm, and compares KiCad's netlist with the netlist that ../sim/frontend.py simulates:
every pair of pins must be connected in one exactly when it is connected in the other.

Values come from ../parts.py. The drawing helpers are those of the LX-IS601F schematic generator,
../../../research/lx-is601f-board/schematic/kisch.py. Coordinates are in grid units of 1.27 mm.
"""
import copy
import collections, itertools, os, re, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'sim'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'research', 'lx-is601f-board', 'schematic'))
import kisch
from kisch import Sheet
from parts import PARTS, OTHER

G = 1.27


def xform(x, y, rot, mirror=None):
    """Library coordinates to schematic offset, as KiCad does it: rotate, then mirror on the sheet."""
    a, b = x, -y
    for _ in range((rot // 90) % 4):
        a, b = b, -a
    if mirror == 'x':
        b = -b
    if mirror == 'y':
        a = -a
    return a, b


kisch.xform = xform     # the helper's own transform mirrors before rotating, which differs at 90 and 270 degrees
PROJ = dict(name='poe-front-end', title='Discrete PoE front end', date='', rev='', company='budget-poe-adapter')
S = Sheet(PROJ, 'poe-front-end.kicad_sch', 'Discrete PoE front end', 'A3', '1')
S.comments = {1: 'Powered device interface for IEEE 802.3af and 802.3at, built from discrete parts',
              2: 'VSS: PoE return after the bridges. GND: system ground, switched to VSS by Q13.'}

SYM = {
    'R': 'Device:R', 'C': 'Device:C', 'CP': 'Device:C_Polarized', 'Z': 'Device:D_Zener', 'S': 'Device:D_Schottky',
    'BR': 'poe-front-end:ABS210', 'NPN': 'Transistor_BJT:MMBT3904', 'PNP': 'Transistor_BJT:MMBT3906',
    'PNP89': 'Transistor_BJT:BCX53', 'NFET': 'Transistor_FET:BSS123', 'PFET': 'Device:Q_NMOS_GDS',
    'REF': 'Reference_Voltage:TL432DBZ',
}


def abs210_symbol():
    """Bridge symbol numbered as the ABS210 datasheet: 1 and 2 are the AC pins, 3 is +, 4 is -."""
    node = copy.deepcopy(kisch.load_lib_symbol('Device', 'D_Bridge_+-AA'))
    renumber = {'1': '3', '2': '4', '3': '1', '4': '2'}

    def walk(n):
        for i, c in enumerate(n):
            if isinstance(c, list):
                if c and c[0] == 'number':
                    c[1] = type(c[1])(renumber[str(c[1])])
                elif c and c[0] == 'symbol':
                    c[1] = type(c[1])(str(c[1]).replace('D_Bridge_+-AA', 'ABS210'))
                walk(c)
    walk(node)
    node[1] = type(node[1])('poe-front-end:ABS210')
    return node


S.use('poe-front-end:ABS210', abs210_symbol())
# Wanted pin offsets (grid units, y down) per orientation name; the rotation and mirror are searched for.
WANT = {
    ('R', 'v'): {'1': (0, -3), '2': (0, 3)}, ('R', 'h'): {'1': (-3, 0), '2': (3, 0)},
    ('C', 'v'): {'1': (0, -3), '2': (0, 3)}, ('C', 'h'): {'1': (-3, 0), '2': (3, 0)},
    ('CP', 'v'): {'1': (0, -3), '2': (0, 3)},
    ('Z', 'kup'): {'1': (0, -3), '2': (0, 3)},          # cathode up
    ('S', 'kup'): {'1': (0, -3), '2': (0, 3)},
    ('S', 'kright'): {'1': (3, 0), '2': (-3, 0)},
    ('BR', 'n'): {'3': (6, 0), '4': (-6, 0), '1': (0, -6), '2': (0, 6)},
    ('NPN', 'n'): {'1': (-4, 0), '3': (2, -4), '2': (2, 4)},      # collector up
    ('PNP', 'eup'): {'1': (-4, 0), '2': (2, -4), '3': (2, 4)},    # emitter up
    ('PNP89', 'eup'): {'1': (-4, 0), '3': (2, -4), '2': (2, 4)},
    ('NFET', 'n'): {'1': (-4, 0), '3': (2, -4), '2': (2, 4)},     # drain up
    ('PFET', 'n'): {'1': (-4, 0), '2': (2, -4), '3': (2, 4)},
    ('REF', 'kup'): {'2': (0, -2), '3': (0, 2), '1': (2, 0)},     # cathode up, anode down, REF right
}
_orient = {}


def orient(kind, how):
    if (kind, how) not in _orient:
        node = S.use(SYM[kind])
        pins = {n: (x, y) for (u, n), (x, y, a, l, nm) in kisch.symbol_pins(node).items()}
        for mir, rot in itertools.product((None, 'x', 'y'), (0, 90, 180, 270)):
            got = {n: tuple(round(v / G) for v in kisch.xform(x, y, rot, mir)) for n, (x, y) in pins.items()}
            if got == WANT[(kind, how)]:
                _orient[(kind, how)] = (rot, mir)
                break
        else:
            raise SystemExit('no orientation for %s %s' % (kind, how))
    return _orient[(kind, how)]


class Frame:
    """A dashed frame; parts and wires inside it use grid units from its top-left corner."""
    def __init__(self, title, x, y, w, h):
        self.title, self.x, self.y, self.w, self.h = title, x, y, w, h
        S.frame(x * G, y * G, (x + w) * G, (y + h) * G, title)

    def pt(self, p):
        return ((self.x + p[0]) * G, (self.y + p[1]) * G)

    def part(self, kind, how, ref, x, y, value=None):
        rot, mir = orient(kind, how)
        if value is None:
            value = (PARTS.get(ref) or OTHER[ref])[1]
        horizontal = how in ('h', 'kright')
        px, py = self.pt((x, y))
        kw = {}
        if kind in ('R', 'C', 'CP', 'Z', 'S'):
            if horizontal:       # reference above, value below
                up = 3.9 if kind in ('C', 'S') else 2.9
                kw = dict(ref_at=(px, py - up), val_at=(px, py + up), center={'ref', 'val'})
            else:                # reference and value to the right of the body
                kw = dict(ref_at=(px + 2.3, py - 1.1), val_at=(px + 2.3, py + 1.1), center=set())
        elif kind in ('NPN', 'PNP', 'PNP89', 'NFET', 'PFET'):
            kw = dict(ref_at=(px + 5.4, py - 1.1), val_at=(px + 5.4, py + 1.1), center=set())
        elif kind == 'REF':
            kw = dict(ref_at=(px - 2.6, py - 1.1), val_at=(px - 2.6, py + 1.1), center=set())
        elif kind == 'BR':
            kw = dict(ref_at=(px + 4.2, py - 6.2), val_at=(px + 4.2, py + 6.2), center=set())
        p = S.place(SYM[kind], ref, value, px, py, rot=rot, mirror=mir, **kw)
        if kind == 'REF':        # text sits left of the body: right-justify it
            S.symbols[-1]['just'] = {'Reference': 'right', 'Value': 'right'}
        p.frame = self
        return p

    def w_(self, *pts):
        """Wire through points; a point may be a (part, pin) pair or frame coordinates."""
        out = []
        for p in pts:
            if isinstance(p[0], kisch.Part):
                out.append(p[0].p(p[1]))
            else:
                out.append(self.pt(p))
        # keep every segment horizontal or vertical: insert a corner when both coordinates change
        fixed = [out[0]]
        for b in out[1:]:
            a = fixed[-1]
            if abs(a[0] - b[0]) > 1e-6 and abs(a[1] - b[1]) > 1e-6:
                raise SystemExit('diagonal wire in %s: %s -> %s' % (self.title, a, b))
            fixed.append(b)
        S.wire(fixed)

    def label(self, net, p, d, kind='label', shape='bidirectional'):
        S.label(net, self.pt(p), d, kind, shape)

    def power(self, name, p, up=None):
        """Power port at p with a one-unit stub: up for supplies, down for returns."""
        down = name in ('VSS', 'GND') if up is None else not up
        e = (p[0], p[1] + (1.0 if down else -1.0) * 2)
        self.w_(p, e)
        x, y = self.pt(e)
        S.power(name, x, y, lib_name='GND' if name == 'VSS' else None)

    def note(self, text, x, y, w):
        S.textbox(text, (self.x + x) * G, (self.y + y) * G, w * G)


# ---------------------------------------------------------------------------------------------
# Input and detection
# ---------------------------------------------------------------------------------------------
TOP, ROW2, FH = 10, 98, 82      # frame rows (grid units) and frame height
f = Frame('Input and detection', 10, TOP, 88, FH)
br1 = f.part('BR', 'n', 'BR1', 30, 22)
br2 = f.part('BR', 'n', 'BR2', 30, 50)
for br, ytop, ybot, a, b in ((br1, 14, 32, 'PAIR_1_2', 'PAIR_3_6'), (br2, 40, 60, 'PAIR_4_5', 'PAIR_7_8')):
    x = 30
    f.w_((br, '1'), (x, ytop), (18, ytop)); f.label(a, (18, ytop), (-1, 0), 'global', 'input')
    f.w_((br, '2'), (x, ybot), (18, ybot)); f.label(b, (18, ybot), (-1, 0), 'global', 'input')
    yc = 22 if br is br1 else 50
    f.w_((br, '4'), (21, yc)); f.power('VSS', (21, yc))
f.w_((br1, '3'), (42, 22), (42, 50), (br2, '3'))
d1 = f.part('Z', 'kup', 'D1', 50, 32)
r1 = f.part('R', 'v', 'R1', 62, 32)
c1 = f.part('C', 'v', 'C1', 74, 32)
f.w_((42, 22), (74, 22)); f.power('VDD', (56, 22))
for p in (d1, r1, c1):
    f.w_((p, '1'), (round((p.x / G) - f.x), 22))
    f.w_((p, '2'), (round((p.x / G) - f.x), 44))
f.w_((50, 44), (74, 44)); f.power('VSS', (56, 44))
f.note('The four inputs are the centre taps of the uplink transformer. BR1 rectifies mode A '
       '(pairs 1-2 and 3-6), BR2 mode B (pairs 4-5 and 7-8), in either polarity. '
       'R1 and C1 are the detection signature. D1 clamps surges.', 42, 54, 42)

# ---------------------------------------------------------------------------------------------
# Class window and class current sink
# ---------------------------------------------------------------------------------------------
f = Frame('Class window and class current sink', 102, TOP, 104, FH)
VDD, CSS, VSS = 10, 62, 74
d3 = f.part('Z', 'kup', 'D3', 8, 16)
r7 = f.part('R', 'v', 'R7', 8, 25)
r8 = f.part('R', 'v', 'R8', 8, 37)
q4 = f.part('NPN', 'n', 'Q4', 18, 32)
f.w_((d3, '1'), (8, VDD)); f.w_((d3, '2'), (r7, '1')); f.w_((r7, '2'), (r8, '1')); f.w_((8, 32), (q4, '1'))
f.w_((r8, '2'), (8, VSS)); f.w_((q4, '2'), (20, VSS))
r5 = f.part('R', 'v', 'R5', 32, 16)
r6 = f.part('R', 'v', 'R6', 32, 31)
f.w_((r5, '1'), (32, VDD)); f.w_((r5, '2'), (r6, '1')); f.w_((r6, '2'), (32, VSS))
f.w_((q4, '3'), (20, 24), (32, 24))
q3 = f.part('NFET', 'n', 'Q3', 44, 68)
f.w_((32, 24), (40, 24), (40, 68), (q3, '1')); f.label('NG', (34, 24), (1, 0))
f.w_((q3, '2'), (46, VSS)); f.w_((q3, '3'), (46, CSS))
d2 = f.part('Z', 'kup', 'D2', 54, 16)
r2 = f.part('R', 'v', 'R2', 54, 27)
u1 = f.part('REF', 'kup', 'U1', 54, 48)
f.w_((d2, '1'), (54, VDD)); f.w_((d2, '2'), (r2, '1')); f.w_((54, 21), (60, 21)); f.label('NA', (60, 21), (1, 0))
r32 = f.part('R', 'v', 'R32', 44, 27)
f.w_((r32, '1'), (44, 21), (54, 21)); f.w_((r32, '2'), (44, CSS), (46, CSS))
f.w_((r2, '2'), (u1, '2')); f.w_((u1, '3'), (54, CSS))
q1 = f.part('NPN', 'n', 'Q1', 74, 35)
f.w_((54, 35), (q1, '1'))
c7 = f.part('C', 'v', 'C7', 64, 41)
f.w_((c7, '1'), (64, 35)); f.w_((c7, '2'), (64, 48))
r29 = f.part('R', 'h', 'R29', 70, 48)
f.w_((u1, '1'), (r29, '1')); f.w_((r29, '2'), (76, 48))
r4 = f.part('R', 'v', 'R4', 76, 55, value='35.7 Ω')
f.w_((q1, '2'), (r4, '1')); f.w_((r4, '2'), (76, CSS))
r3 = f.part('R', 'v', 'R3', 76, 16)
q2 = f.part('PNP89', 'eup', 'Q2', 88, 25)
f.w_((r3, '1'), (76, VDD)); f.w_((r3, '2'), (q1, '3')); f.w_((76, 25), (q2, '1'))
f.w_((q2, '3'), (90, VDD)); f.w_((q2, '2'), (90, 48), (76, 48))
f.w_((8, VDD), (90, VDD)); f.power('VDD', (44, VDD))
f.w_((8, VSS), (46, VSS)); f.power('VSS', (26, VSS))
f.w_((46, CSS), (94, CSS)); f.label('CSS', (94, CSS), (1, 0))
f.note('R4 sets the class: 140 Ω for Class 1, 73.2 Ω for Class 2, 47.5 Ω for Class 3, 31.6 Ω for Class 4, '
       'and 35.7 Ω for Class 4 with the mark latch and the two-event detector fitted.', 60, 66, 40)

# ---------------------------------------------------------------------------------------------
# Hot swap
# ---------------------------------------------------------------------------------------------
f = Frame('Hot swap', 210, TOP, 94, FH)
VDD, VSS = 10, 54
d6 = f.part('Z', 'kup', 'D6', 8, 16)
r27 = f.part('R', 'v', 'R27', 8, 25)
r28 = f.part('R', 'v', 'R28', 8, 39)
d7 = f.part('Z', 'kup', 'D7', 20, 39)
c4 = f.part('C', 'v', 'C4', 32, 39)
f.w_((d6, '1'), (8, VDD)); f.w_((d6, '2'), (r27, '1')); f.w_((r27, '2'), (r28, '1'))
for p in (r28, d7, c4):
    f.w_((p, '2'), (round(p.x / G) - f.x, VSS))
f.w_((d7, '1'), (20, 32)); f.w_((c4, '1'), (32, 32))
q13 = f.part('PFET', 'n', 'Q13', 66, 32)
f.w_((8, 32), (q13, '1'))
r31 = f.part('R', 'h', 'R31', 48, 22)
c5 = f.part('C', 'h', 'C5', 58, 22)
f.w_((42, 32), (42, 22), (r31, '1')); f.w_((r31, '2'), (c5, '1')); f.w_((c5, '2'), (68, 22))
f.w_((q13, '2'), (68, 22)); f.w_((q13, '3'), (68, VSS))
c6 = f.part('CP', 'v', 'C6', 80, 16)
f.w_((c6, '1'), (80, VDD)); f.w_((c6, '2'), (80, 22), (68, 22)); f.w_((80, 22), (88, 22)); f.power('GND', (88, 22))
f.w_((8, VDD), (80, VDD)); f.power('VDD', (44, VDD))
f.w_((8, VSS), (68, VSS)); f.power('VSS', (44, VSS))
f.note('Q13 connects the system ground GND to VSS once VDD has passed the voltage of D6 plus the gate threshold. '
       'C5 and C4 slow the turn-on so that the inrush current into C6 stays under the limit of the PSE. '
       'C6 is the input capacitor of the 5 V converter.', 8, 62, 80)

# ---------------------------------------------------------------------------------------------
# Mark latch
# ---------------------------------------------------------------------------------------------
f = Frame('Mark latch', 10, ROW2, 76, FH)
VDD, CSS = 10, 64
r9 = f.part('R', 'h', 'R9', 14, 32)
f.w_((7, 32), (r9, '1')); f.label('NA', (7, 32), (-1, 0))
r10 = f.part('R', 'v', 'R10', 20, 43)
q5 = f.part('NPN', 'n', 'Q5', 36, 32)
f.w_((r9, '2'), (q5, '1')); f.w_((20, 32), (r10, '1')); f.w_((r10, '2'), (20, CSS)); f.w_((q5, '2'), (38, CSS))
r12 = f.part('R', 'v', 'R12', 38, 13)
r11 = f.part('R', 'v', 'R11', 38, 23)
f.w_((r12, '2'), (r11, '1')); f.w_((r11, '2'), (q5, '3'))
q6 = f.part('PNP', 'eup', 'Q6', 54, 18)
f.w_((38, 18), (q6, '1')); f.w_((q6, '2'), (56, VDD))
r13 = f.part('R', 'v', 'R13', 56, 43)
f.w_((q6, '3'), (r13, '1')); f.w_((r13, '2'), (56, CSS))
f.w_((56, 32), (64, 32)); f.label('VM', (64, 32), (1, 0))
r14 = f.part('R', 'h', 'R14', 44, 54)
f.w_((30, 32), (30, 54), (r14, '1')); f.w_((r14, '2'), (51, 54), (51, 36), (56, 36))
f.w_((38, VDD), (56, VDD)); f.power('VDD', (47, VDD))
f.w_((20, CSS), (62, CSS)); f.label('CSS', (62, CSS), (1, 0))

# ---------------------------------------------------------------------------------------------
# Two-event detector
# ---------------------------------------------------------------------------------------------
f = Frame('Two-event detector', 90, ROW2, 104, FH)
VM, CSS = 10, 68
r15 = f.part('R', 'h', 'R15', 12, 50)
f.w_((6, 50), (r15, '1')); f.label('NA', (6, 50), (-1, 0))
r16 = f.part('R', 'v', 'R16', 18, 58)
q7 = f.part('NPN', 'n', 'Q7', 30, 50)
q8 = f.part('NPN', 'n', 'Q8', 30, 34)
f.w_((r15, '2'), (q7, '1')); f.w_((18, 50), (r16, '1')); f.w_((r16, '2'), (18, CSS)); f.w_((q7, '2'), (32, CSS))
f.w_((q8, '2'), (q7, '3'))
r30 = f.part('R', 'v', 'R30', 20, 38)
r19 = f.part('R', 'v', 'R19', 20, 27)
f.w_((r19, '2'), (20, 34), (r30, '1')); f.w_((20, 34), (q8, '1')); f.w_((r30, '2'), (20, 42), (32, 42))
f.w_((r19, '1'), (20, 22), (14, 22)); f.label('ARM', (14, 22), (-1, 0))
r20 = f.part('R', 'v', 'R20', 32, 25)
r21 = f.part('R', 'v', 'R21', 32, 13)
f.w_((q8, '3'), (r20, '2')); f.w_((r20, '1'), (r21, '2'))
q9 = f.part('PNP', 'eup', 'Q9', 50, 19)
f.w_((32, 19), (q9, '1')); f.w_((q9, '2'), (52, VM))
f.w_((q9, '3'), (52, 26), (58, 26)); f.label('EVENT2', (58, 26), (1, 0))
r17 = f.part('R', 'v', 'R17', 68, 32)
f.w_((r17, '1'), (68, VM)); f.w_((r17, '2'), (68, 42))
d4 = f.part('S', 'kright', 'D4', 74, 42)
f.w_((32, 42), (d4, '2'))
c2 = f.part('C', 'v', 'C2', 80, 52)
r18 = f.part('R', 'v', 'R18', 94, 52)
d8 = f.part('S', 'kup', 'D8', 80, 26)
f.w_((d4, '1'), (98, 42)); f.label('ARM', (98, 42), (1, 0))
f.w_((c2, '1'), (80, 42)); f.w_((r18, '1'), (94, 42)); f.w_((c2, '2'), (80, CSS)); f.w_((r18, '2'), (94, CSS))
f.w_((d8, '2'), (80, 42)); f.w_((d8, '1'), (80, VM))
f.w_((24, VM), (32, VM), (80, VM)); f.label('VM', (24, VM), (-1, 0))
f.w_((18, CSS), (98, CSS)); f.label('CSS', (98, CSS), (1, 0))

# ---------------------------------------------------------------------------------------------
# Hold and T2P output
# ---------------------------------------------------------------------------------------------
f = Frame('Hold and T2P output', 198, ROW2, 104, FH)
VSS = 68
r22 = f.part('R', 'h', 'R22', 16, 30)
d5 = f.part('S', 'kright', 'D5', 26, 30)
f.w_((7, 30), (r22, '1')); f.label('EVENT2', (7, 30), (-1, 0))
f.w_((r22, '2'), (d5, '2'))
q10 = f.part('NFET', 'n', 'Q10', 36, 38)
f.w_((d5, '1'), (38, 30), (q10, '3'))
f.w_((q10, '1'), (26, 38)); f.label('NG', (26, 38), (-1, 0))
c3 = f.part('C', 'v', 'C3', 44, 54)
r23 = f.part('R', 'v', 'R23', 58, 54)
q11 = f.part('NFET', 'n', 'Q11', 70, 46)
f.w_((q10, '2'), (38, 46), (q11, '1'))
f.w_((c3, '1'), (44, 46)); f.w_((r23, '1'), (58, 46)); f.w_((c3, '2'), (44, VSS)); f.w_((r23, '2'), (58, VSS))
f.w_((q11, '2'), (72, VSS)); f.w_((44, VSS), (72, VSS)); f.power('VSS', (64, VSS))
r24 = f.part('R', 'v', 'R24', 72, 33)
r25 = f.part('R', 'v', 'R25', 72, 17)
f.w_((q11, '3'), (r24, '2')); f.w_((r24, '1'), (r25, '2'))
q12 = f.part('PNP', 'eup', 'Q12', 86, 24)
f.w_((72, 24), (q12, '1'))
f.w_((r25, '1'), (72, 12), (88, 12), (q12, '2')); f.power('+3V3', (80, 12))
r26 = f.part('R', 'v', 'R26', 88, 42)
f.w_((q12, '3'), (r26, '1')); f.power('GND', (88, 45)); 
f.w_((88, 34), (94, 34)); f.label('T2P', (94, 34), (1, 0), 'global', 'output')
f.note('T2P is high (3.3 V) when the PSE ran two class events, which is its grant of 25.5 W. '
       'C3 holds the result for at least 1.3 s after power-up; the firmware reads it at boot.', 6, 10, 44)


# ---------------------------------------------------------------------------------------------
# Output, netlist check, renders
# ---------------------------------------------------------------------------------------------
SCH = os.path.join(HERE, S.fname)
open(SCH, 'w').write(S.render(S.uuid, '/' + S.uuid))
if S.margin_report:
    print('MARGIN', S.margin_report[:10])

ROLE = {'D': ('2', '1'), 'Q': ('3', '1', '2'), 'M': ('3', '1', '2'), 'X': ('2', '1', '3')}   # SPICE node order -> pin numbers
RENAME = {'M3': 'Q3', 'M10': 'Q10', 'M11': 'Q11', 'M13': 'Q13', 'XU1': 'U1', 'Rc5': 'R31'}
# Pin numbers read from the datasheets in datasheets/components/ (function -> pin number).
DATASHEET_PINS = {
    'BR': {'~a': '1', '~b': '2', '+': '3', '-': '4'},     # Yongyutai ABS210
    'Q2': {'B': '1', 'C': '2', 'E': '3'},                 # R+O BCX53-16, SOT-89
    'Q13': {'G': '1', 'D': '2', 'S': '3'},                # UMW 15N10, TO-252
    'SOT23_BJT': {'B': '1', 'E': '2', 'C': '3'},          # MMBT3904, PMBS3906
    'SOT23_FET': {'G': '1', 'S': '2', 'D': '3'},          # MDD BSS123
    'U1': {'REF': '1', 'K': '2', 'A': '3'},               # LRC LR432B
}
PINS = {'Q2': ('2', '1', '3'), 'Q13': ('2', '1', '3')}      # BCX53: B1 C2 E3; TO-252 FET: G1 D2 S3 (order C/D, B/G, E/S)


def expected():
    """Pin -> node of the simulated netlist, for the parts drawn on the schematic."""
    from frontend import circuit
    pin_node = {}
    alias = {'vss0': '0'}
    for line in circuit(cls=4, t2p=True).splitlines():
        t = line.split()
        if not t or t[0][0] in '*.' or t[0] in ('Vvss', 'V0p', 'Vpse', 'Vpl'):
            continue
        name = RENAME.get(t[0], t[0])
        nodes = [alias.get(n, n) for n in t[1:4]]
        if t[0].startswith('DB'):
            continue
        if name not in PARTS and name != 'C6':
            continue
        kind = t[0][0]
        if kind in 'RC':
            for n in nodes[:2]:
                pin_node.setdefault((name, '*'), []).append(n)
        else:
            order = PINS.get(name, ROLE[kind])
            for pin, n in zip(order, nodes):
                pin_node[(name, pin)] = n
    # bridges: + VDD, - VSS, each ~ pin on a net of its own
    for br in ('BR1', 'BR2'):
        pin_node[(br, DATASHEET_PINS['BR']['+'])] = 'vdd'; pin_node[(br, DATASHEET_PINS['BR']['-'])] = '0'
        pin_node[(br, '1')] = br + 'a'; pin_node[(br, '2')] = br + 'b'
    return pin_node


def value_check():
    """The values on the schematic (../parts.py) against the values the simulation uses."""
    import frontend
    mult = {'Ω': 1, 'kΩ': 1e3, 'MΩ': 1e6, 'nF': 1e-9, 'µF': 1e-6}
    bad = []
    for ref, sim in frontend.PARTS.items():
        if sim is None:
            continue
        num, unit = (PARTS.get(ref) or OTHER[ref])[1].split()[:2]
        if abs(float(num) * mult[unit] - sim) > 1e-6 * sim:
            bad.append('%s: schematic %s %s, simulation %g' % (ref, num, unit, sim))
    return bad


def netlist_check(tmp):
    out = os.path.join(tmp, 'check.net')
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '-o', out, SCH], check=True, capture_output=True)
    text = open(out).read()
    actual = {}
    for m in re.finditer(r'\(net \(code "?\d+"?\) \(name "([^"]*)"\)(.*?)(?=\(net \(code|\Z)', text, re.S):
        for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m.group(2)):
            actual[(ref, pin)] = m.group(1)
    exp = expected()
    # two-pin passives: compare as unordered pairs
    a_nodes, e_nodes = collections.defaultdict(set), collections.defaultdict(set)
    problems = []
    for (ref, pin), node in exp.items():
        if pin == '*':
            got = sorted(actual.get((ref, p), '?') for p in ('1', '2'))
            for n, g in zip(sorted(node), got):
                pass
            e_pair = sorted(node)
            # match the pair to KiCad nets by trying both assignments later
            a_nodes[ref] = got; e_nodes[ref] = e_pair
        else:
            if (ref, pin) not in actual:
                problems.append('pin %s.%s is not connected in KiCad' % (ref, pin))
    # build the mapping sim node -> KiCad net from the polarised parts, then test every pin
    m = {}
    def bind(node, net, who):
        if m.setdefault(node, net) != net:
            problems.append('%s: sim node %s is KiCad net %s and %s' % (who, node, m[node], net))
    for (ref, pin), node in exp.items():
        if pin != '*' and (ref, pin) in actual:
            bind(node, actual[(ref, pin)], ref + '.' + pin)
    changed = True
    while changed:
        changed = False
        for ref, pair in e_nodes.items():
            got = a_nodes[ref]
            known = [n for n in pair if n in m]
            if len(known) == 2 or not known:
                continue
            other = [n for n in pair if n not in m][0]
            rest = list(got)
            if m[known[0]] in rest:
                rest.remove(m[known[0]])
                m[other] = rest[0]; changed = True
    for ref, pair in e_nodes.items():
        want = sorted(m.get(n, '?' + n) for n in pair)
        if want != a_nodes[ref]:
            problems.append('%s: simulated between %s, drawn between %s' % (ref, pair, a_nodes[ref]))
    inv = collections.defaultdict(set)
    for node, net in m.items():
        inv[net].add(node)
    for net, nodes in inv.items():
        if len(nodes) > 1:
            problems.append('KiCad net %s joins the simulated nodes %s' % (net, sorted(nodes)))
    drawn = {ref for ref, pin in actual if not ref.startswith('#')}
    missing = (set(PARTS) | {'C6'}) - drawn
    if missing:
        problems.append('not drawn: %s' % sorted(missing))
    return problems, len(exp), m


DETAIL_SCALE = 6.6     # pixels per mm in the detail images


def render(tmp):
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    pdf = os.path.join(HERE, 'poe-front-end.pdf')
    subprocess.run(['kicad-cli', 'sch', 'export', 'pdf', '-o', pdf, SCH], check=True, capture_output=True)
    subprocess.run(['pdftoppm', '-r', '300', '-png', '-singlefile', pdf, os.path.join(tmp, 'p')], check=True)
    im = Image.open(os.path.join(tmp, 'p.png')).convert('RGB')
    k = im.size[0] / Sheet.PAPER[S.paper][0]
    os.makedirs(os.path.join(HERE, 'renders'), exist_ok=True)
    whole = im.resize((round(im.size[0] * 110 / 300), round(im.size[1] * 110 / 300)), Image.LANCZOS)
    whole.save(os.path.join(HERE, 'renders', 'sheet.png'), optimize=True)
    dx, dy = Sheet.offset
    for x1, y1, x2, y2, title in S.frames:
        box = [round(v * k) for v in (x1 + dx - 1, y1 + dy - 1, x2 + dx + 1, y2 + dy + 1)]
        piece = im.crop(box)
        w = round((x2 - x1 + 2) * DETAIL_SCALE)
        piece = piece.resize((w, round(piece.size[1] * w / piece.size[0])), Image.LANCZOS)
        name = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-') + '.png'
        piece.save(os.path.join(HERE, 'renders', name), optimize=True)
        print('render %-44s %d x %d px' % (name, piece.size[0], piece.size[1]))


with tempfile.TemporaryDirectory() as tmp:
    problems, n, mapping = netlist_check(tmp)
    problems += value_check()
    for p in problems:
        print('NETLIST', p)
    print('netlist check: %d pins compared, %d problems' % (n, len(problems)))
    render(tmp)
sys.exit(1 if problems or S.margin_report else 0)
