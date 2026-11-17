#!/usr/bin/env python3
"""Generate the LX-IS601F V2.0 reverse-engineered schematic (KiCad 7, hierarchical).

Layout follows well-regarded open KiCad projects
(Antmicro baseboards, Olimex ESP32-PoE): a root sheet with a block diagram of
hierarchical sheets, one function per sheet, KiCad library symbols for
standard parts, power ports instead of rail labels, signal flow left to right,
framed functional groups, notes in text boxes, and a title block on every sheet.

Confidence codes (also the wire style):
  C  confirmed: traced on both sides, or measured        green solid
  V  seen on one side of the board in photos             blue solid
  I  inferred from datasheet / marking / usual practice   orange dashed
  U  unknown: pin exists, destination not traced          red dotted

Run:  python3 gen_schematic.py
Writes lx-is601f.kicad_sch (+ child sheets), lx-is601f-nets.csv and, when
kicad-cli is installed, checks the netlist KiCad computes against the model.
"""
import csv, os, subprocess, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kisch import Sheet, box_symbol, snap, U

HERE = os.path.dirname(os.path.abspath(__file__))
G = 2.54
PROJ = dict(name='lx-is601f', title='LX-IS601F V2.0 switch board (reverse-engineered)', date='2026-11-17', rev='0.2',
            company='budget-poe-adapter research')


def g(n):
    return round(n * G, 4)


def sheet(fname, title, paper='A3', page='1'):
    s = Sheet(PROJ, fname, title, paper, page)
    s.comments = {1: title, 2: 'Traced from photos only; wire style = confidence (see root sheet legend)',
                  3: 'YT9215SCH pin functions: Motorcomm datasheet V1.03 (2025-02-10)'}
    return s


def two(s, lib, ref, val, x, y, horiz, conf='I', **kw):
    """Place a two-terminal part. Vertical: pin 1 on top. Horizontal: pin 1 left."""
    rot = 90 if horiz else 0
    flip = kw.pop('flip', False)
    # Device:R/C/L have pin 1 at +y (top); rot 90 puts pin 1 on the left.
    if lib in ('Device:D_Schottky', 'Device:LED', 'Device:D_TVS', 'Device:Crystal', 'Device:D'):
        rot = 0 if horiz else 270  # these are horizontal in the library, pin 1 (K) left / top
    if flip:
        rot = (rot + 180) % 360
    dy = 3.81 if (horiz and (lib.startswith('Device:C') or lib == 'Device:LED')) else 2.54
    ra = kw.pop('ref_at', None) or ((x, y - dy) if horiz else (x + 2.54, y - 1.27))
    va = kw.pop('val_at', None) or ((x, y + 3.175) if horiz else (x + 2.54, y + 1.27))
    cen = kw.pop('center', {'ref', 'val'} if horiz else set())
    return s.place(lib, ref, val, x, y, rot=rot, ref_at=ra, val_at=va, center=cen, **kw)


def link(s, a, an, b, bn, net, conf='I', hfirst=None):
    s.route(a.p(an), b.p(bn), conf, hfirst)
    s.mark(a, an, net, conf); s.mark(b, bn, net, conf)


# ======================================================================
# custom symbols
# ======================================================================
def u4_symbol():
    MDI = ['A+', 'A-', 'B+', 'B-', 'C+', 'C-', 'D+', 'D-']
    mpins = {0: [95, 96, 97, 98, 100, 101, 102, 103], 1: [105, 106, 107, 108, 110, 111, 112, 113],
             2: [119, 120, 121, 122, 124, 125, 126, 127], 3: [1, 2, 3, 4, 6, 7, 8, 9], 4: [19, 20, 21, 22, 24, 25, 26, 27]}
    right = []
    for p in range(5):
        if p:
            right.append(None)
        for k, n in enumerate(mpins[p]):
            right.append((str(n), 'P%dMDI%s' % (p, MDI[k]), 'bidirectional'))
    unitA = dict(right=right, w=22.86)
    unitB = dict(right=[('39', 'HSOP_0', 'output'), ('38', 'HSON_0', 'output'), ('41', 'HSIP_0', 'input'), ('42', 'HSIN_0', 'input'), None,
                        ('32', 'HSOP_1', 'output'), ('31', 'HSON_1', 'output'), ('34', 'HSIP_1', 'input'), ('35', 'HSIN_1', 'input')], w=17.78)
    unitC = dict(left=[('88', 'XTALI', 'input'), ('87', 'XTALO', 'output'), None, ('89', '~{nRESET}', 'input'), ('12', 'RBIAS', 'passive'),
                       ('60', 'EN_SWR', 'input'), ('63', 'LX', 'output'), ('64', 'LX', 'passive'), None,
                       ('91', 'GPIO48/SCL/MDC', 'bidirectional'), ('92', 'GPIO49/SDA/MDIO', 'bidirectional'), None,
                       ('49', 'GPIO9/SPF0_SCK/SPF_MUX_SEL', 'bidirectional'), ('50', 'GPIO10/SPF0_SI', 'bidirectional'),
                       ('54', 'GPIO14/SPF0_SO', 'bidirectional'), ('55', 'GPIO15/SPF0_CS', 'bidirectional'), None,
                       ('46', 'GPIO6/UART0_RX', 'bidirectional'), ('47', 'GPIO7/UART0_TX', 'bidirectional'), None,
                       ('90', 'GPIO47/SSPI_CS', 'bidirectional'), ('93', 'GPIO50/SSPI_SO', 'bidirectional'),
                       ('44', 'GPIO5/INTERRUPT', 'bidirectional'), ('48', 'GPIO8', 'bidirectional'), ('51', 'GPIO11/SWITCH_ID_0', 'bidirectional'),
                       ('52', 'GPIO12', 'bidirectional'), ('53', 'GPIO13', 'bidirectional'), ('56', 'GPIO16', 'bidirectional'),
                       ('57', 'GPIO17', 'bidirectional')],
                 right=[('85', 'GPIO46/P0LED0/LED_CK', 'bidirectional'), ('84', 'GPIO45/P0LED1/LED_DA', 'bidirectional'),
                        ('83', 'GPIO44/P0LED2/SPF1_SCK/EN_PHY', 'bidirectional'), None,
                        ('80', 'GPIO42/P1LED0', 'bidirectional'), ('81', 'GPIO43/P1LED1/SPF1_CS', 'bidirectional'),
                        ('79', 'GPIO41/P1LED2/SPF1_SI', 'bidirectional'), None,
                        ('77', 'GPIO39/P2LED0/DISAUTOLOAD', 'bidirectional'), ('78', 'GPIO40/P2LED1/SPF1_SO', 'bidirectional'),
                        ('76', 'GPIO38/P2LED2/UART1_TX/DIS_MCU', 'bidirectional'), None,
                        ('75', 'GPIO37/P3LED0/EN_SPIF', 'bidirectional'), ('73', 'GPIO35/P3LED1', 'bidirectional'),
                        ('74', 'GPIO36/P3LED2/EN_PWRLIGHT', 'bidirectional'), None,
                        ('71', 'GPIO33/P4LED0/EEPROM_MOD', 'bidirectional'), ('72', 'GPIO34/P4LED1', 'bidirectional'),
                        ('70', 'GPIO32/P4LED2/UART1_RX/DIS_SPIS', 'bidirectional'), None,
                        ('67', 'GPIO31/P9LED0', 'bidirectional'), None,
                        ('14', 'NC', 'no_connect'), ('15', 'NC', 'no_connect'), ('116', 'NC', 'no_connect')], w=63.5)
    p33 = [(str(n), 'AVDDH', 'power_in') for n in (10, 16, 18, 28, 86, 94, 104, 114, 118, 128)] + \
          [('68', 'DVDDIO', 'power_in'), ('82', 'DVDDIO', 'power_in'), ('45', 'DVDDIO_1', 'power_in'), ('59', 'DVDDIO_1', 'power_in'),
           ('29', 'SVDDH', 'power_in'), ('65', 'HV_SWR', 'power_in'), ('66', 'HV_SWR', 'power_in')]
    p115 = [(str(n), 'AVDDL', 'power_in') for n in (5, 13, 23, 99, 109, 123)] + \
           [(str(n), 'DVDDL', 'power_in') for n in (17, 58, 69)] + \
           [('33', 'SVDDL_1', 'power_in'), ('40', 'SVDDL_0', 'power_in'), ('115', 'PLLVDDL', 'power_in')]
    gnd = [('11', 'AGND', 'power_in'), ('30', 'SGND_1', 'power_in'), ('36', 'SGND_1', 'power_in'), ('37', 'SGND_0', 'power_in'),
           ('43', 'SGND_0', 'power_in'), ('61', 'GND_SWR', 'power_in'), ('62', 'GND_SWR', 'power_in'), ('117', 'PLLGND', 'power_in'),
           ('129', 'EPAD', 'power_in')]
    unitD = dict(left=p33, right=p115 + [None] + gnd, w=25.4)
    units = [unitA, unitB, unitC, unitD]
    node = box_symbol('YT9215SCH', units, ref='U', value='YT9215SCH')
    allp = set()
    for u in units:
        for side in ('left', 'right', 'top', 'bottom'):
            for pe in u.get(side, []):
                if pe:
                    allp.add(int(pe[0]))
    assert allp == set(range(1, 130)), sorted(set(range(1, 130)) - allp)
    return node, units


def g2401_symbol():
    left = [('2', 'TD1+', 'passive'), ('1', 'TCT1', 'passive'), ('3', 'TD1-', 'passive'), None,
            ('5', 'TD2+', 'passive'), ('4', 'TCT2', 'passive'), ('6', 'TD2-', 'passive'), None,
            ('8', 'TD3+', 'passive'), ('7', 'TCT3', 'passive'), ('9', 'TD3-', 'passive'), None,
            ('11', 'TD4+', 'passive'), ('10', 'TCT4', 'passive'), ('12', 'TD4-', 'passive')]
    right = [('23', 'MX1+', 'passive'), ('24', 'MCT1', 'passive'), ('22', 'MX1-', 'passive'), None,
             ('20', 'MX2+', 'passive'), ('21', 'MCT2', 'passive'), ('19', 'MX2-', 'passive'), None,
             ('17', 'MX3+', 'passive'), ('18', 'MCT3', 'passive'), ('16', 'MX3-', 'passive'), None,
             ('14', 'MX4+', 'passive'), ('15', 'MCT4', 'passive'), ('13', 'MX4-', 'passive')]
    return box_symbol('G2401PR', [dict(left=left, right=right, w=15.24)], ref='T', value='G2401PR',
                      props={'Note': 'Pin numbers assumed (common 24-pin 1-port GbE layout); no datasheet found'})


def sct2622_symbol():
    return box_symbol('SCT2622', [dict(left=[('2', 'VIN', 'power_in'), ('3', 'EN', 'input'), ('4', 'RT', 'passive'), None],
                                       right=[('1', 'BOOT', 'passive'), ('8', 'SW', 'power_out'), ('5', 'FB', 'input'), None],
                                       bottom=[None, ('7', 'GND', 'power_in'), None, None, ('9', 'EP', 'passive')], w=20.32)],
                      ref='U', value='SCT2622', props={'Note': 'Pin numbers not verified'})


def pse_symbol():
    left = [('?1', 'VDD48', 'power_in'), ('?2', 'VDD3V3', 'power_in'), None, ('?3', 'SCL/LED?', 'bidirectional'),
            ('?4', 'SDA/LED?', 'bidirectional'), None, ('?5', 'GND', 'power_in')]
    right = []
    for ch in range(1, 5):
        if ch > 1:
            right += [None, None]
        right += [('?%d0' % ch, 'PORT%d' % ch, 'passive'), ('?%d1' % ch, 'SENSE%d' % ch, 'passive')]
    return box_symbol('PSE_2184A', [dict(left=left, right=right, w=22.86)], ref='U', value='2184A',
                      props={'Note': 'Unidentified 4-port PSE (QFN-48, marking 2184A 533AQ1H). Functional pins only.'})


# ======================================================================
# sheets  (coordinates in mm; m() snaps to the 2.54 mm grid)
# ======================================================================
def m(v):
    return round(round(v / G) * G, 4)


root = sheet('lx-is601f.kicad_sch', 'Root: block diagram', 'A3', '1')
power = sheet('power.kicad_sch', 'Power input and 3.3 V buck', 'A3', '2')
switch = sheet('switch.kicad_sch', 'Switch IC YT9215SCH', 'A2', '3')
eth = sheet('ethernet_poe.kicad_sch', 'Ports 1-4 (PoE): magnetics, ESD, RJ45', 'A3', '4')
upl = sheet('uplink_sfp.kicad_sch', 'Port 5 uplink and SFP', 'A3', '5')
poe = sheet('poe_module.kicad_sch', 'PoE PSE module (daughterboard)', 'A3', '6')
leds = sheet('leds.kicad_sch', 'Port LEDs', 'A3', '7')
ALL = [root, power, switch, eth, upl, poe, leds]

LEGEND = ('Wire style = confidence of each connection\n'
          'green solid      C  confirmed (traced on both sides, or measured)\n'
          'blue solid       V  seen on one side of the board in the photos\n'
          'orange dashed    I  inferred from datasheet, marking or usual practice\n'
          'red dotted       U  unknown: pin exists, destination not traced\n\n'
          'Nothing is C yet. Every connection still needs a continuity check.')


def gnd(s, p, conf='I', drop=2.54):
    s.wire([p, (p[0], p[1] + drop)], conf); s.power('GND', p[0], p[1] + drop)


def bus(s, pts):
    for a, b in zip(pts, pts[1:]):
        s.items.append(['bus', ['pts', ['xy', m(a[0]), m(a[1])], ['xy', m(b[0]), m(b[1])]], ['stroke', ['width', 0], ['type', 'default']], ['uuid', U()]])


def entry(s, x, y, dx, dy):
    s.items.append(['bus_entry', ['at', m(x), m(y)], ['size', dx, dy], ['stroke', ['width', 0], ['type', 'default']], ['uuid', U()]])


# ---------------------------------------------------------------- POWER
s = power
s.frame(m(12.7), m(15), m(200), m(97), 'DC input and protection')
YL = m(40)
j2 = s.place('Connector_Generic:Conn_01x02', 'J2', 'POWER2', m(22), YL, mirror='y')
l1 = two(s, 'Device:L', 'L1', 'white SMD', m(45), YL, True)
d4 = two(s, 'Device:D_Schottky', 'D4', 'SS510', m(90), YL, True, flip=True)
l2 = two(s, 'Device:L', 'L2', '"701"', m(108), YL, True)
link(s, j2, '1', l1, '1', 'VIN_RAW', 'I')
link(s, l1, '2', d4, '2', 'VIN_F', 'I')
link(s, d4, '1', l2, '1', 'VIN_P', 'I')
p = j2.p('2'); s.wire([p, (m(30), p[1]), (m(30), m(62))], 'I'); s.power('GND', m(30), m(62)); s.mark(j2, '2', 'GND', 'I')
for i, rv in enumerate(['RV1', 'RV2', 'RV3']):
    x = m(52 + 12.7 * i)
    v = two(s, 'Device:Varistor', rv, 'MOV?', x, m(53), False)
    s.wire([(x, YL), v.p('1')], 'U'); s.mark(v, '1', 'VIN_F', 'U')
    gnd(s, v.p('2'), 'U', drop=m(62) - v.p('2')[1]); s.mark(v, '2', 'GND', 'U')
for i, (r, v, lib) in enumerate([('C1', '1206', 'Device:C'), ('C2', '1206', 'Device:C'), ('C3', '1206', 'Device:C'), ('C4', '47u 63V', 'Device:C_Polarized')]):
    x = m(122 + 12.7 * i)
    c = two(s, lib, r, v, x, m(53), False)
    s.wire([(x, YL), c.p('1')], 'I'); s.mark(c, '1', '+48V', 'I')
    gnd(s, c.p('2'), 'I', drop=m(62) - c.p('2')[1]); s.mark(c, '2', 'GND', 'I')
s.wire([l2.p('2'), (m(175), YL)], 'I'); s.mark(l2, '2', '+48V', 'I')
s.power('+48V', m(175), YL); s.power('PWR_FLAG', m(175), YL, lib_name='PWR_FLAG', rot=180)
d1 = two(s, 'Device:D_Schottky', 'D1', 'SS510', m(40), m(80), True); s.stub(d1, '1', 'TBD_D1_K', 'U'); s.stub(d1, '2', 'TBD_D1_A', 'U')
d5 = two(s, 'Device:D_Schottky', 'D5', 'SS510', m(80), m(80), True); s.stub(d5, '1', 'TBD_D5_K', 'U'); s.stub(d5, '2', 'TBD_D5_A', 'U')
s.text('D1 and D5 sit next to the input; their nets are not traced.', m(15), m(88), size=1.27, italic=True)
s.textbox('Input\n- Assumed 48-57 V (C4 is rated 63 V). J2 polarity not checked.\n'
          '- RV1-RV3: blue disc parts, silk "RV". Drawn as varistors to GND;\n  they could be Y-capacitors to chassis.\n'
          '- L1 is a white SMD part (fuse or inductor).\n- D4 is assumed to be the reverse-polarity diode.', m(210), m(15), m(95), m(30))

s.frame(m(12.7), m(105), m(285), m(195), '3.3 V buck: PU1 SCT2622 (4.2-60 V in, 2 A, non-synchronous)')
pu1 = s.place('lxr:SCT2622', 'PU1', 'SCT2622', m(110), m(145), node=sct2622_symbol(), ref_at=(m(102.87), m(137.16)), val_at=(m(113.03), m(137.16)))
s.power('+48V', m(85), m(125))
s.route((m(85), m(125)), pu1.p('2'), 'I', hfirst=False); s.mark(pu1, '2', '+48V', 'I')
r7 = two(s, 'Device:R', 'R7', '0603', m(65), m(137), False)
r8 = two(s, 'Device:R', 'R8', '31k6 "49C"', m(65), m(157), False)
s.power('+48V', m(65), m(125)); s.wire([(m(65), m(125)), r7.p('1')], 'I'); s.mark(r7, '1', '+48V', 'I')
link(s, r7, '2', r8, '1', 'BUCK_EN', 'I')
yen = pu1.p('3')[1]
s.wire([(m(65), yen), pu1.p('3')], 'I'); s.mark(pu1, '3', 'BUCK_EN', 'I')
gnd(s, r8.p('2'), 'I', drop=m(178) - r8.p('2')[1]); s.mark(r8, '2', 'GND', 'I')
pr1 = two(s, 'Device:R', 'PR1', '73k2 "86C"', m(90), m(165), False)
s.route(pu1.p('4'), pr1.p('1'), 'I', hfirst=True); s.mark(pu1, '4', 'BUCK_RT', 'I'); s.mark(pr1, '1', 'BUCK_RT', 'I')
gnd(s, pr1.p('2'), 'I', drop=m(178) - pr1.p('2')[1]); s.mark(pr1, '2', 'GND', 'I')
gnd(s, pu1.p('7'), 'I', drop=m(178) - pu1.p('7')[1]); s.mark(pu1, '7', 'GND', 'I')
p9 = pu1.p('9'); yj = p9[1] + G * 2
s.wire([p9, (p9[0], yj), (pu1.p('7')[0], yj)], 'I'); s.mark(pu1, '9', 'GND', 'I')
pc6 = two(s, 'Device:C', 'PC6', 'boot', m(135), m(130), True)
ysw = pu1.p('8')[1]
s.route(pu1.p('1'), pc6.p('1'), 'I', hfirst=False); s.mark(pu1, '1', 'BUCK_BST', 'I'); s.mark(pc6, '1', 'BUCK_BST', 'I')
xn = m(145)
s.wire([pc6.p('2'), (xn, pc6.p('2')[1]), (xn, ysw)], 'I'); s.mark(pc6, '2', 'BUCK_SW', 'I')
pl3 = two(s, 'Device:L', 'PL3', '10u "100"', m(165), ysw, True)
s.wire([pu1.p('8'), pl3.p('1')], 'V'); s.mark(pu1, '8', 'BUCK_SW', 'V'); s.mark(pl3, '1', 'BUCK_SW', 'V')
d40 = two(s, 'Device:D_Schottky', 'D40', 'Schottky', xn, m(162), False)
s.wire([(xn, ysw), d40.p('1')], 'I'); s.mark(d40, '1', 'BUCK_SW', 'I')
gnd(s, d40.p('2'), 'I', drop=m(178) - d40.p('2')[1]); s.mark(d40, '2', 'GND', 'I')
for x, (r, v, lib) in zip([m(185), m(200), m(212)], [('TC1', '220u 16V', 'Device:C_Polarized'), ('C23', '1206', 'Device:C'), ('C24', '1206', 'Device:C')]):
    c = two(s, lib, r, v, x, m(162), False)
    s.wire([(x, ysw), c.p('1')], 'I'); s.mark(c, '1', '+3V3', 'I')
    gnd(s, c.p('2'), 'I', drop=m(178) - c.p('2')[1]); s.mark(c, '2', 'GND', 'I')
pr2 = two(s, 'Device:R', 'PR2', '200k "30D"', m(228), m(157), False)
pr3 = two(s, 'Device:R', 'PR3', '300k "304"', m(228), m(170), False)
s.wire([(m(228), ysw), pr2.p('1')], 'I'); s.mark(pr2, '1', '+3V3', 'I')
link(s, pr2, '2', pr3, '1', 'BUCK_FB', 'I')
gnd(s, pr3.p('2'), 'I', drop=m(183) - pr3.p('2')[1]); s.mark(pr3, '2', 'GND', 'I')
yfb = m(163.83)
s.wire([(pr2.p('2')[0], yfb), (m(235), yfb)], 'I'); s.label('BUCK_FB', (m(235), yfb), (1, 0))
s.stub(pu1, '5', 'BUCK_FB', 'I', length=m(7.62))
s.wire([pl3.p('2'), (m(250), ysw)], 'V'); s.mark(pl3, '2', '+3V3', 'V')
s.power('+3V3', m(250), ysw); s.power('PWR_FLAG', m(250), ysw, lib_name='PWR_FLAG', rot=180)
pc2 = two(s, 'Device:C', 'PC2', 'MLCC', m(262), m(187), True); s.stub(pc2, '1', 'TBD_PC2_1', 'U'); s.stub(pc2, '2', 'TBD_PC2_2', 'U')
r11 = two(s, 'Device:R', 'R11', '20k5 "31C"', m(262), m(175), True); s.stub(r11, '1', 'TBD_R11_1', 'U'); s.stub(r11, '2', 'TBD_R11_2', 'U')
s.textbox('3.3 V buck\n- PU1 marking "2622 SCT 6DC" = SCT2622. Pin functions are from its datasheet;\n  pin numbers are assumed.\n'
          '- Values are decoded EIA-96 codes (49C = 31.6k, 86C = 73.2k, 30D = 200k).\n'
          '- Which resistors form the FB divider is not checked: measure TC1 (expect 3.3 V).\n'
          '- PC2 and R11 sit next to PU1; nets not traced.\n\n'
          'The 1.15 V core rail (+1V15) is made by U4\'s internal regulator through L3\n(sheet "Switch IC YT9215SCH").', m(210), m(45), m(110))

# ---------------------------------------------------------------- SWITCH (A2 594 x 420)
s = switch
u4node, u4units = u4_symbol()
s.use('lxr:YT9215SCH', u4node)
# U4C control
s.frame(m(12.7), m(15), m(280), m(270), 'U4C: clock, reset, regulator, management, GPIO and LEDs')
uC = s.place('lxr:YT9215SCH', 'U4', 'YT9215SCH', m(170), m(140), unit=3, node=u4node)
# crystal block (top-left)
y6 = two(s, 'Device:Crystal', 'Y6', '25 MHz', m(90), m(80), True, flip=True)
c44 = two(s, 'Device:C', 'C44', '0402', m(80), m(90), False)
c43 = two(s, 'Device:C', 'C43', '0402', m(100), m(90), False)
s.wire([y6.p('2'), (m(80), y6.p('2')[1]), c44.p('1')], 'V'); s.mark(y6, '2', 'XTALI', 'V'); s.mark(c44, '1', 'XTALI', 'V')
s.wire([y6.p('1'), (m(100), y6.p('1')[1]), c43.p('1')], 'V'); s.mark(y6, '1', 'XTALO', 'V'); s.mark(c43, '1', 'XTALO', 'V')
s.wire([(m(80), m(80)), (m(80), m(72.39)), (m(114.3), m(72.39))], 'V'); s.route((m(114.3), m(72.39)), uC.p('88'), 'V', hfirst=False); s.mark(uC, '88', 'XTALI', 'V')
s.route((m(100), m(80)), uC.p('87'), 'V', xm=m(106.68)); s.mark(uC, '87', 'XTALO', 'V')
for c in (c43, c44):
    gnd(s, c.p('2'), 'V'); s.mark(c, '2', 'GND', 'V')
s.stub(uC, '89', 'NRESET', 'U', length=m(10))
s.stub(uC, '12', 'RBIAS', 'I', length=m(10))
s.pin_power(uC, '60', '+3V3', 'I', length=m(25.4))
l3 = two(s, 'Device:L', 'L3', '4u7 "4R7"', m(95), uC.p('63')[1], True)
s.wire([uC.p('63'), l3.p('2')], 'V'); s.mark(uC, '63', 'SWR_LX', 'V'); s.mark(l3, '2', 'SWR_LX', 'V')
xl = m(105)
s.wire([uC.p('64'), (xl, uC.p('64')[1]), (xl, uC.p('63')[1])], 'V'); s.mark(uC, '64', 'SWR_LX', 'V')
s.wire([l3.p('1'), (m(85), l3.p('1')[1])], 'V'); s.mark(l3, '1', '+1V15', 'V')
s.power('+1V15', m(85), l3.p('1')[1], lib_name='+1V1'); s.power('PWR_FLAG', m(85), l3.p('1')[1], lib_name='PWR_FLAG', rot=180)
s.textbox('RBIAS: 2.49 kOhm 1 % to GND per datasheet. The\nresistor and the reset RC are not located yet.', m(15), m(100), m(60), m(10))
# EEPROM
u10 = s.place('Memory_EEPROM:24LC08', 'U10', 'HK24C08', m(55), m(150), ref_at=(m(55) - 10.16, m(150) - 8.89), val_at=(m(55) + 2.54, m(150) - 8.89), center=set())
s.route(u10.p('6'), uC.p('91'), 'I', xm=m(100)); s.mark(u10, '6', 'I2C_SCL', 'I'); s.mark(uC, '91', 'I2C_SCL', 'I')
s.route(u10.p('5'), uC.p('92'), 'I', xm=m(102.54)); s.mark(u10, '5', 'I2C_SDA', 'I'); s.mark(uC, '92', 'I2C_SDA', 'I')
xa = u10.p('1')[0] - m(5.08)
for n in ('1', '2', '3'):
    p = u10.p(n); s.wire([p, (xa, p[1])], 'I'); s.mark(u10, n, 'GND', 'I')
s.wire([(xa, u10.p('1')[1]), (xa, u10.p('3')[1])], 'I'); gnd(s, (xa, u10.p('3')[1]), 'I', drop=m(5.08))
s.pin_power(u10, '8', '+3V3', 'I'); s.pin_power(u10, '4', 'GND', 'I')
s.stub(u10, '7', 'TBD_U10_WP', 'U', length=m(5.08))
s.textbox('U10 (bottom side). R14, R16, R19, R29, R30 and C15\nnext to it: probably pull-ups, WP and decoupling.', m(15), m(168), m(60), m(10))
# SPI flash footprint
u6 = s.place('Memory_Flash:W25Q32JVSS', 'U6', 'W25Q32 (DNP)', m(60), m(215), dnp=True, mirror='y', ref_at=(m(48), m(201)), val_at=(m(48), m(229)), center=set())
fl = [('49', 'R93', 'SPF0_SCK', 'FL_SCK', '6'), ('50', 'R92', 'SPF0_SI', 'FL_SI', '5'), ('54', 'R89', 'SPF0_SO', 'FL_SO', '2'),
      ('55', 'R44', 'SPF0_CS', 'FL_CS', '1')]
for i, (n, rr, n1, n2, fp) in enumerate(fl):
    p = uC.p(n)
    r = two(s, 'Device:R', rr, '0402', m(110), p[1], True, ref_at=(m(116.84), p[1] - 1.0), val_at=(m(125.73), p[1] - 1.0), center=set())
    s.wire([r.p('2'), p], 'V'); s.mark(r, '2', n1, 'V'); s.mark(uC, n, n1, 'V')
    q = u6.p(fp)
    xv = m(85 + 2.54 * i)
    s.wire([r.p('1'), (xv, p[1]), (xv, q[1]), q], 'U')
    s.mark(r, '1', n2, 'U'); s.mark(u6, fp, n2, 'U')
s.pin_power(u6, '8', '+3V3', 'U'); s.pin_power(u6, '4', 'GND', 'U')
s.stub(u6, '3', 'TBD_U6_WP', 'U', length=m(5.08)); s.stub(u6, '7', 'TBD_U6_HOLD', 'U', length=m(5.08))
s.textbox('U6: empty SOP-8 footprint on the bottom, assumed SPI NOR\nflash (25-series pinout). R40, R94, R96, R98, R100, R102,\nR109 sit next to it. '
          'R44/R89/R92/R93 to U4 pins 55/54/50/49\nare seen on the top side.', m(15), m(240), m(70))
for n in ('46', '47', '90'):
    s.nc(uC.p(n)); s.mark(uC, n, '(no trace seen)', 'V')
for n in ('93', '44', '48', '51', '52', '53', '56', '57'):
    s.stub(uC, n, 'TBD_U4_%s' % n, 'U', length=m(7.62))
s.text('X on pins 46, 47, 90 and 79: no trace leaves\nthe pad in the photos.', m(120), m(195), size=1.27, italic=True)
LEDMAP = {'85': 'LED_P0', '80': 'LED_P1', '77': 'LED_P2', '75': 'LED_P3', '71': 'LED_P4', '67': 'LED_P9'}
for n in ('85', '84', '83', '80', '81', '79', '77', '78', '76', '75', '73', '74', '71', '72', '70', '67'):
    if n in LEDMAP:
        s.stub(uC, n, LEDMAP[n], 'I', length=m(15.24), kind='hier', shape='output')
    elif n == '79':
        s.nc(uC.p('79')); s.mark(uC, '79', '(no trace seen)', 'V')
    else:
        s.stub(uC, n, 'TBD_U4_%s' % n, 'U', length=m(7.62))
for n in ('14', '15', '116'):
    s.nc(uC.p(n)); s.mark(uC, n, '(NC)', 'I')
s.textbox('Straps share LED pins: EN_SPIF 75, DIS_MCU 76, DISAUTOLOAD 77,\nEN_PHY 83, EEPROM_MOD 71, DIS_SPIS 70. LEDx0 goes to the LED\n'
          'sheet (inferred). The other LED/strap pins have pull resistors\nR2-R5, R103, R110-R114 nearby (not traced).', m(195), m(215), m(80), m(16))
# U4A MDI
s.frame(m(290), m(15), m(450), m(270), 'U4A: copper ports (MDI)')
uA = s.place('lxr:YT9215SCH', 'U4', 'YT9215SCH', m(330), m(130), unit=1, node=u4node)
MDIPINS = {0: [95, 96, 97, 98, 100, 101, 102, 103], 1: [105, 106, 107, 108, 110, 111, 112, 113],
           2: [119, 120, 121, 122, 124, 125, 126, 127], 3: [1, 2, 3, 4, 6, 7, 8, 9], 4: [19, 20, 21, 22, 24, 25, 26, 27]}
for p in range(5):
    ends = [s.stub(uA, n, 'P%d_MDI%d' % (p, k), 'I', length=m(20.32), near=True) for k, n in enumerate(MDIPINS[p])]
    bx = ends[0][0] + m(2.54)
    for e in ends:
        entry(s, e[0], e[1], G, -G)
    bus(s, [(bx, ends[0][1] - G * 2), (bx, ends[-1][1] - G)])
    bus(s, [(bx, ends[0][1] - G * 2), (bx + m(10.16), ends[0][1] - G * 2)])
    s.label('P%d_MDI[0..7]' % p, (bx + m(10.16), ends[0][1] - G * 2), (1, 0), kind='hier')
s.textbox('Port mapping (inferred from placement)\nP0 -> DXFRM4 -> J1 port 1\nP1 -> DXFRM3 -> J1 port 2\nP2 -> DXFRM2 -> J1 port 3\n'
          'P3 -> DXFRM5 -> J1 port 4\nP4 -> DXFRM6 -> J3 uplink\nMDIn: 0..7 = A+ A- B+ B- C+ C- D+ D-', m(295), m(200), m(60), m(30))
# U4B SerDes
s.frame(m(460), m(15), m(560), m(110), 'U4B: SerDes')
uB = s.place('lxr:YT9215SCH', 'U4', 'YT9215SCH', m(485), m(55), unit=2, node=u4node)
for n, net in (('39', 'SDS0_TXP'), ('38', 'SDS0_TXN'), ('41', 'SDS0_RXP'), ('42', 'SDS0_RXN')):
    s.stub(uB, n, net, 'U', length=m(15.24), kind='hier', shape='output' if 'TX' in net else 'input')
for n, net in (('32', 'SDS1_TXP'), ('31', 'SDS1_TXN'), ('34', 'SDS1_RXP'), ('35', 'SDS1_RXN')):
    s.stub(uB, n, net, 'U', length=m(7.62))
s.textbox('Which SerDes feeds the SFP (U12) is not traced;\nSerDes 0 is assumed. SerDes 1 nets end here.', m(465), m(85), m(60), m(10))
# U4D power
s.frame(m(460), m(120), m(560), m(262), 'U4D: supply pins')
uD = s.place('lxr:YT9215SCH', 'U4', 'YT9215SCH', m(510), m(170), unit=4, node=u4node)
lp = u4units[3]['left']
_r = u4units[3]['right']; _k = _r.index(None)
rp, bp = _r[:_k], _r[_k + 1:]
xa = uD.p(lp[0][0])[0] - m(5.08)
for pe in lp:
    q = uD.p(pe[0]); s.wire([q, (xa, q[1])], 'I'); s.mark(uD, pe[0], '+3V3', 'I')
s.wire([(xa, uD.p(lp[0][0])[1] - m(5.08)), (xa, uD.p(lp[-1][0])[1])], 'I'); s.power('+3V3', xa, uD.p(lp[0][0])[1] - m(5.08))
xb = uD.p(rp[0][0])[0] + m(5.08)
for pe in rp:
    q = uD.p(pe[0]); s.wire([q, (xb, q[1])], 'I'); s.mark(uD, pe[0], '+1V15', 'I')
s.wire([(xb, uD.p(rp[0][0])[1] - m(5.08)), (xb, uD.p(rp[-1][0])[1])], 'I'); s.power('+1V15', xb, uD.p(rp[0][0])[1] - m(5.08), lib_name='+1V1')
for pe in bp:
    q = uD.p(pe[0]); s.wire([q, (xb, q[1])], 'I'); s.mark(uD, pe[0], 'GND', 'I')
s.wire([(xb, uD.p(bp[0][0])[1]), (xb, uD.p(bp[-1][0])[1])], 'I'); gnd(s, (xb, uD.p(bp[-1][0])[1]), 'I', drop=m(5.08))
s.textbox('Supplies (datasheet): AVDDH, DVDDIO, SVDDH, HV_SWR = 3.3 V;\nAVDDL, DVDDL, SVDDL, PLLVDDL = 1.15 V (1.08-1.32 V).\n\n'
          'About 30 0402 decoupling capacitors surround U4 (C19, C21,\nC22, C25, C26, C30, C45, C48, C49, C92-C97, C100, C105,\nC111-C113, C119, C122-C126, ...). '
          'Their rails are not traced,\nso they are not drawn.\n\nEPAD (pin 129) is GND; a screw through the board clamps the\nheatsink onto it.',
          m(465), m(220), m(90))

# ---------------------------------------------------------------- PORT BLOCK
gnode = g2401_symbol()


def port_block(s, p, xfrm, jref, jval, eds, x0, y0, poe_base, title, w=185, h=104.14):
    s.frame(x0, y0, x0 + w, y0 + h, title)
    yb = y0 + m(12.7)
    s.label('P%d_MDI[0..7]' % p, (x0 + m(22.86), yb), (-1, 0), kind='hier')
    bx = x0 + m(27.94)
    t = s.place('lxr:G2401PR', xfrm, 'G2401PR', x0 + m(80), y0 + m(45), node=gnode)
    td = [('2', 0), ('3', 1), ('5', 2), ('6', 3), ('8', 4), ('9', 5), ('11', 6), ('12', 7)]
    ylast = t.p('12')[1]
    bus(s, [(x0 + m(22.86), yb), (bx, yb), (bx, ylast - G)])
    for pin, k in td:
        q = t.p(pin)
        entry(s, bx, q[1] - G, G, G)
        s.wire([(bx + G, q[1]), q], 'I')
        s.label('P%d_MDI%d' % (p, k), (bx + G * 2, q[1]), (1, 0))
        s.mark(t, pin, 'P%d_MDI%d' % (p, k), 'I')
    xt = t.p('1')[0] - m(5.08)
    for pin in ('1', '4', '7', '10'):
        q = t.p(pin); s.wire([q, (xt, q[1])], 'U'); s.mark(t, pin, 'P%d_TCT' % p, 'U')
    s.wire([(xt, t.p('1')[1]), (xt, t.p('10')[1] + m(5.08))], 'U')
    s.label('P%d_TCT' % p, (xt, t.p('10')[1] + m(5.08)), (0, 1))
    j = s.place('Connector:RJ45_Shielded', jref, jval, x0 + m(170), y0 + m(45), mirror='y',
                ref_at=(x0 + m(177.8), y0 + m(25.4)), val_at=(x0 + m(177.8), y0 + m(27.94)), center=set())
    for tp, jp in [('23', '1'), ('22', '2'), ('20', '3'), ('19', '6'), ('17', '4'), ('16', '5'), ('14', '7'), ('13', '8')]:
        s.stub(t, tp, 'P%d_L%s' % (p, jp), 'V', length=m(10.16))
        s.stub(j, jp, 'P%d_L%s' % (p, jp), 'V', length=m(10.16))
    sh = j.p('SH'); s.wire([sh, (sh[0], sh[1] + G)], 'U'); s.power('Earth_Protective', sh[0], sh[1] + G, lib_name='Earth_Protective')
    s.mark(j, 'SH', 'CHASSIS', 'U')
    for pin, net in (('24', 'POE%d' % poe_base), ('21', 'POE%d' % (poe_base + 1)), ('18', 'P%d_CT45' % p), ('15', 'P%d_CT78' % p)):
        s.stub(t, pin, net, 'U', length=m(10.16))
    for k, ed in enumerate(eds):
        ex, ey = x0 + m(45 + 75 * k), y0 + m(82.55)
        e = s.place('Power_Protection:SRV05-4', ed, '"05U"', ex, ey, ref_at=(ex + m(5.08), ey - m(15.24)), val_at=(ex + m(5.08), ey - m(12.7)), center=set())
        for pin, mi in zip(('1', '3', '4', '6'), ([0, 1, 2, 3] if k == 0 else [4, 5, 6, 7])):
            s.stub(e, pin, 'P%d_MDI%d' % (p, mi), 'I', length=m(5.08))
        s.pin_power(e, '2', 'GND', 'I'); s.stub(e, '5', 'TBD_P%d_ESD_VP' % p, 'U', length=m(2.54))


s = eth
PORTS = [(0, 'DXFRM4', 'J1 port 1 (PoE)', ('ED1', 'ED10'), 1), (1, 'DXFRM3', 'J1 port 2 (PoE)', ('ED2', 'ED3'), 3),
         (2, 'DXFRM2', 'J1 port 3 (PoE)', ('ED4', 'ED5'), 5), (3, 'DXFRM5', 'J1 port 4 (PoE)', ('ED6', 'ED7'), 7)]
for i, (p, xf, jv, eds, pb) in enumerate(PORTS):
    x0 = m(12.7 + (i % 2) * 187.96)
    y0 = m(12.7 + (i // 2) * 106.68)
    port_block(s, p, xf, 'J1%s' % 'ABCD'[i], 'RJ45 ' + jv, eds, x0, y0, pb,
               'Port %d: U4 P%d -> %s -> J1 port %d' % (i + 1, p, xf, i + 1))
# PoE bus to the module sheet
yb = m(236.22)
s.label('POE[1..8]', (m(105), yb), (1, 0), kind='hier')
bus(s, [(m(12.7), yb), (m(105), yb)])
for k in range(8):
    x = m(17.78 + 10.16 * k)
    entry(s, x, yb, G, -G)
    s.wire([(x + G, yb - G), (x + G, yb - m(5.08))], 'U')
    s.label('POE%d' % (k + 1), (x + G, yb - m(5.08)), (0, -1))
s.textbox('Notes: PoE assumed on the centre taps of pairs 1-2 / 3-6 (POE odd/even) -> header PIN1 (PoE module sheet). '
          'Pairs 4-5 / 7-8 centre taps (Pn_CT45/CT78) assumed to go to Bob-Smith terminations on the bottom. '
          'Bottom parts under J1 not yet assigned: 12x SMB "CP06C" (D6, D8-D18), 1206 caps C16, C38, C55, C56, C60-C62, C65, C71, C75, C98, ..., '
          '0603 resistors R15, R32, R67, R71-R76, R82-R84. J1 is one 1x4 RJ45 block, drawn as J1A-J1D. G2401PR pinout assumed. '
          '"05U" arrays drawn with the SRV05-4 pinout (assumed).', m(12.7), m(241.3), m(165), size=1.1)

# ---------------------------------------------------------------- UPLINK + SFP
s = upl
port_block(s, 4, 'DXFRM6', 'J3', 'RJ45 uplink (no PoE)', ('ED8', 'ED9'), m(12.7), m(15), 9, 'Port 5 (uplink): U4 P4 -> DXFRM6 -> J3')
s.frame(m(220), m(15), m(330), m(135), 'SFP: U12')
sfp = s.place('Interface_Optical:SFP', 'U12', 'SFP host connector', m(275), m(70))
for n, net, sh in (('18', 'SDS0_TXP', 'input'), ('19', 'SDS0_TXN', 'input'), ('13', 'SDS0_RXP', 'output'), ('12', 'SDS0_RXN', 'output')):
    s.stub(sfp, n, net, 'U', length=m(12.7), kind='hier', shape=sh)
for n, net in (('2', 'TBD_SFP_TXFAULT'), ('8', 'TBD_SFP_LOS'), ('3', 'TBD_SFP_TXDIS'), ('4', 'TBD_SFP_SDA'), ('5', 'TBD_SFP_SCL'),
               ('6', 'TBD_SFP_MODDEF0'), ('7', 'TBD_SFP_RS')):
    s.stub(sfp, n, net, 'U', length=m(5.08))
a15, a16 = sfp.p('15'), sfp.p('16'); yt = min(a15[1], a16[1]) - m(5.08)
s.wire([a15, (a15[0], yt)], 'U'); s.wire([a16, (a16[0], yt)], 'U'); s.wire([(a15[0], yt), (a16[0], yt)], 'U')
s.power('+3V3', min(a15[0], a16[0]), yt); s.mark(sfp, '15', '+3V3', 'U'); s.mark(sfp, '16', '+3V3', 'U')
for n in ('9', '11', '14', '17', '20'):
    s.mark(sfp, n, 'GND', 'U')
b1, b10 = sfp.p('1'), sfp.p('10'); yg = max(b1[1], b10[1]) + m(2.54)
s.wire([b1, (b1[0], yg)], 'U'); s.wire([b10, (b10[0], yg)], 'U'); s.wire([(b1[0], yg), (b10[0], yg)], 'U')
s.power('GND', max(b1[0], b10[0]), yg); s.mark(sfp, '1', 'GND', 'U'); s.mark(sfp, '10', 'GND', 'U')
s.mark(sfp, 'CAGE', 'CHASSIS', 'U')
c = sfp.p('CAGE'); ye = c[1] + m(7.62); xe = c[0] - m(7.62)
s.wire([c, (c[0], ye), (xe, ye)], 'U'); s.power('Earth_Protective', xe, ye, lib_name='Earth_Protective')
s.textbox('U12 is a 20-pin SFP edge connector; one board has the cage fitted.\nAC-coupling caps, I2C and status pins are not traced.', m(225), m(110), m(100))
s.textbox('The uplink has no PoE: POE9/POE10 are placeholders for its pair 1-2 / 3-6 centre taps (not traced).', m(12.7), m(124), m(195))

# ---------------------------------------------------------------- POE MODULE
s = poe
s.frame(m(12.7), m(15), m(75), m(120), 'Mainboard header PIN1')
pin1 = s.place('Connector_Generic:Conn_01x08', 'J4', 'PIN1 header', m(58), m(55), fields={'Silk': 'PIN1'})
XB = m(38.1)
s.label('POE[1..8]', (m(35.56), m(35.56)), (-1, 0), kind='hier')
bus(s, [(m(35.56), m(35.56)), (XB, m(35.56)), (XB, pin1.p('8')[1] - G)])
for k in range(8):
    q = pin1.p(str(k + 1))
    entry(s, XB, q[1] - G, G, G)
    s.wire([(XB + G, q[1]), q], 'U'); s.label('POE%d' % (k + 1), (XB + 2 * G, q[1]), (1, 0)); s.mark(pin1, str(k + 1), 'POE%d' % (k + 1), 'U')
s.textbox('Silk "PIN1": 8-pin row along J1.\nAssumed to carry the 4 ports\' PoE\ncentre-tap feeds. Needs a\ncontinuity check to J1.', m(17.78), m(90), m(52))
s.frame(m(80), m(15), m(284), m(155), 'PoE PSE module (separate PCB)')
pse = s.place('lxr:PSE_2184A', 'U101', '2184A', m(115), m(70), node=pse_symbol(), fields={'Silk': 'U1 (module)'})
s.pin_power(pse, '?1', '+48V', 'U'); s.stub(pse, '?2', 'TBD_PSE_VDD', 'U', length=m(7.62))
s.stub(pse, '?3', 'TBD_PSE_IO1', 'U', length=m(7.62)); s.stub(pse, '?4', 'TBD_PSE_IO2', 'U', length=m(7.62)); s.pin_power(pse, '?5', 'GND', 'U')
chans = [('R108', 'R8', 'R103', 'R3', 'D101', 'D1'), ('R112', 'R12', 'R109', 'R9', 'D103', 'D3'),
         ('R113', 'R13', 'R110', 'R10', 'D105', 'D5'), ('R114', 'R14', 'R111', 'R11', 'D107', 'D7')]
for ch, (rs, rss, rd, rds, dd, dds) in enumerate(chans, 1):
    po = pse.p('?%d0' % ch); se = pse.p('?%d1' % ch)
    rdp = two(s, 'Device:R', rd, '33R', m(170), po[1], True, fields={'Silk': rds + ' (module)'},
              ref_at=(m(166), po[1] - 1.0), val_at=(m(174), po[1] - 1.0))
    s.wire([po, rdp.p('1')], 'U'); s.mark(pse, '?%d0' % ch, 'POE_OUT%d' % ch, 'U'); s.mark(rdp, '1', 'POE_OUT%d' % ch, 'U')
    s.label('POE_OUT%d' % ch, (m(140), po[1]), (1, 0))
    s.stub(rdp, '2', 'TBD_MOD_%s' % rds, 'U', length=m(5.08))
    rsp = two(s, 'Device:R', rs, '0R25', m(150), se[1], True, fields={'Silk': rss + ' (module)'},
              ref_at=(m(146), se[1] + 2.4), val_at=(m(154), se[1] + 2.4))
    s.wire([se, rsp.p('1')], 'U'); s.mark(pse, '?%d1' % ch, 'POE_SNS%d' % ch, 'U'); s.mark(rsp, '1', 'POE_SNS%d' % ch, 'U')
    s.stub(rsp, '2', 'POE_RTN', 'U', length=m(5.08))
    dv = two(s, 'Device:D_TVS', dd, 'TVS "RGS"', m(240), m(45 + 15.24 * (ch - 1)), True, fields={'Silk': dds + ' (module)'})
    s.stub(dv, '1', 'POE_OUT%d' % ch, 'U', length=m(7.62)); s.stub(dv, '2', 'TBD_TVS%d' % ch, 'U', length=m(7.62))
s.textbox('- U1 (QFN-48) marked "2184A 533AQ1H": maker not identified (IP804AR is the\n  closest public 4-port PSE in QFN-48 7x7).\n'
          '- Per channel: 0.25 Ohm "R250" sense (R8, R12, R13, R14), 33 Ohm "330" (R3, R9,\n  R10, R11), SMB TVS "RGS" (D1, D3, D5, D7; one more next to C7).\n'
          '- The module silk reuses mainboard reference numbers, so its parts are\n  renumbered here (R1xx, D1xx, U101); the "Silk" field keeps the silk name.\n'
          '- The topology is a guess. How the module gets 48 V and GND is unknown.', m(82), m(130), m(120), m(30), size=1.1)

# ---------------------------------------------------------------- LEDS
s = leds
s.frame(m(12.7), m(15), m(175), m(170), 'Port LED array (silk columns FX and POW, rows 1-6)')
rws = [('LED_P0', 'RJ7', 'RJ8'), ('LED_P1', 'RJ9', 'RJ10'), ('LED_P2', 'RJ11', 'RJ12'), ('LED_P3', 'RJ13', 'RJ14'),
       ('LED_P4', 'RJ15', 'RJ16'), ('LED_P9', 'RJ17', 'RJ18')]
s.text('FX column', m(30), m(22), size=1.6, bold=True); s.text('POW column', m(110), m(22), size=1.6, bold=True)
for i, (net, rf, rp) in enumerate(rws):
    y = m(35.56 + 17.78 * i)
    for col, (xr, rr, refn, val, onet, conf2) in enumerate([(m(30), rf, 101 + i, 'FX %d' % (i + 1), net, 'I'),
                                                           (m(110), rp, 111 + i, 'POW %d' % (i + 1), 'TBD_POW%d' % (i + 1), 'U')]):
        s.power('+3V3', xr - m(7.62), y - m(5.08))
        r = two(s, 'Device:R', rr, '0603', xr, y, True)
        s.wire([(xr - m(7.62), y - m(5.08)), (xr - m(7.62), y), r.p('1')], 'U'); s.mark(r, '1', '+3V3', 'U')
        d = two(s, 'Device:LED', 'LED%d' % refn, val, xr + m(15.24), y, True, flip=True)
        s.wire([r.p('2'), d.p('2')], 'U'); s.mark(r, '2', 'LED%d_A' % refn, 'U'); s.mark(d, '2', 'LED%d_A' % refn, 'U')
        e = (d.p('1')[0] + m(10.16), y)
        s.wire([d.p('1'), e], conf2); s.mark(d, '1', onet, conf2)
        if col == 0:
            s.label(net, e, (1, 0), kind='hier', shape='input')
        else:
            s.label(onet, e, (1, 0))
s.textbox('- The array LEDs have no visible reference designators: LED101-106 (FX) and\n  LED111-116 (POW) are numbering for this schematic.\n'
          '- Active-low drive from U4 and the RJ-resistor pairing are inferred. Row 6 is\n  assumed to be the SFP (U4 P9LED0, pin 67).\n'
          '- The POW LEDs are probably driven by the PoE module (not traced).', m(12.7), m(140), m(110), m(25), size=1.1)
s.frame(m(185), m(15), m(284), m(130), 'LED6 header (DNP), LED7, LED8')
hd = s.place('Connector_Generic:Conn_02x03_Odd_Even', 'J5', 'LED6 (DNP)', m(235), m(40), dnp=True, fields={'Silk': 'LED6'})
for n in '123456':
    s.stub(hd, n, 'TBD_LED6_%s' % n, 'U', length=m(5.08))
for i, lr in enumerate(('LED7', 'LED8')):
    d = two(s, 'Device:LED', lr, '0603', m(225), m(70 + 12.7 * i), True)
    s.stub(d, '1', 'TBD_%s_K' % lr, 'U', length=m(5.08)); s.stub(d, '2', 'TBD_%s_A' % lr, 'U', length=m(5.08))
r68 = two(s, 'Device:R', 'R68', '0603', m(235), m(110), True)
s.stub(r68, '1', 'TBD_R68_1', 'U', length=m(5.08)); s.stub(r68, '2', 'TBD_R68_2', 'U', length=m(5.08))

# ---------------------------------------------------------------- ROOT
s = root
s.text('LX-IS601F V2.0 switch board: reverse-engineered schematic', m(15), m(15), size=3.5, bold=True)
s.text('Two boards photographed 2026-11-17. YT9215SCH 5-port GbE switch + SFP, with a 4-port PoE PSE plug-in module.', m(15), m(22), size=1.8)
pp = s.subsheet(power, m(20), m(45), m(55), m(20), [])
sw = s.subsheet(switch, m(105), m(45), m(55), m(55),
                [('P0_MDI[0..7]', 'R', 'bidirectional'), ('P1_MDI[0..7]', 'R', 'bidirectional'), ('P2_MDI[0..7]', 'R', 'bidirectional'),
                 ('P3_MDI[0..7]', 'R', 'bidirectional'), ('P4_MDI[0..7]', 'R', 'bidirectional'), ('SDS0_TXP', 'R', 'output'),
                 ('SDS0_TXN', 'R', 'output'), ('SDS0_RXP', 'R', 'input'), ('SDS0_RXN', 'R', 'input'),
                 ('LED_P0', 'R', 'output'), ('LED_P1', 'R', 'output'), ('LED_P2', 'R', 'output'), ('LED_P3', 'R', 'output'),
                 ('LED_P4', 'R', 'output'), ('LED_P9', 'R', 'output')])
ep = s.subsheet(eth, m(240), m(45), m(60), m(18),
                [('P0_MDI[0..7]', 'L', 'bidirectional'), ('P1_MDI[0..7]', 'L', 'bidirectional'), ('P2_MDI[0..7]', 'L', 'bidirectional'),
                 ('P3_MDI[0..7]', 'L', 'bidirectional'), ('POE[1..8]', 'R', 'bidirectional')])
up = s.subsheet(upl, m(240), m(75), m(60), m(18),
                [('P4_MDI[0..7]', 'L', 'bidirectional'), ('SDS0_TXP', 'L', 'input'), ('SDS0_TXN', 'L', 'input'),
                 ('SDS0_RXP', 'L', 'output'), ('SDS0_RXN', 'L', 'output')])
ld = s.subsheet(leds, m(240), m(105), m(60), m(20),
                [('LED_P0', 'L', 'input'), ('LED_P1', 'L', 'input'), ('LED_P2', 'L', 'input'), ('LED_P3', 'L', 'input'),
                 ('LED_P4', 'L', 'input'), ('LED_P9', 'L', 'input')])
pm = s.subsheet(poe, m(330), m(45), m(60), m(12), [('POE[1..8]', 'L', 'bidirectional')])
for (x, y, t) in [(m(22), m(50), 'J2 input, protection,\nSCT2622 buck to +3V3'),
                  (m(108), m(90), 'YT9215SCH (4 units),\n25 MHz crystal, EEPROM U10,\nempty flash footprint U6'),
                  (m(255), m(56), 'DXFRM2-5, J1, ED1-ED7, ED10'),
                  (m(255), m(87), 'DXFRM6, J3, ED8-9, SFP U12'),
                  (m(255), m(118), '12 LEDs, LED6 header'),
                  (m(345), m(52), 'PIN1 header, PSE module')]:
    s.text(t, x, y, size=1.27, italic=True, color=(90, 90, 90))


def rw(a, b, xm, kind):
    pts = [a, (xm, a[1]), (xm, b[1]), b] if a[1] != b[1] else [a, b]
    for u, v in zip(pts, pts[1:]):
        if u != v:
            s.items.append([kind, ['pts', ['xy', m(u[0]), m(u[1])], ['xy', m(v[0]), m(v[1])]], ['stroke', ['width', 0], ['type', 'default']], ['uuid', U()]])


for k in range(4):
    rw(sw['P%d_MDI[0..7]' % k], ep['P%d_MDI[0..7]' % k], m(200 + 5.08 * k), 'bus')
rw(sw['P4_MDI[0..7]'], up['P4_MDI[0..7]'], m(233.68), 'bus')
for k, n in enumerate(('SDS0_TXP', 'SDS0_TXN', 'SDS0_RXP', 'SDS0_RXN')):
    rw(sw[n], up[n], m(231.14 - 2.54 * k), 'wire')
for k, n in enumerate(['LED_P0', 'LED_P1', 'LED_P2', 'LED_P3', 'LED_P4', 'LED_P9']):
    rw(sw[n], ld[n], m(180 + 2.54 * (5 - k)), 'wire')
a, b = ep['POE[1..8]'], pm['POE[1..8]']
rw(a, b, m(315), 'bus')
s.textbox(LEGEND, m(15), m(150), m(120), m(35), size=1.5)
s.textbox('How to read this schematic\n'
          '- One sheet per function. Power nets (+48V, +3V3, +1V15, GND) are global power ports.\n'
          '- Net names starting TBD_ are placeholders for pins whose destination is not traced yet.\n'
          '- Values come from part markings (EIA-96 codes decoded); unmarked parts show the package only.\n'
          '- Pinouts of G2401PR, the "05U" ESD arrays, SCT2622 and the PoE module chip are assumed.\n'
          '- Generated by gen_schematic.py; edit that, not the .kicad_sch files.\n'
          '- lx-is601f-nets.csv lists every pin with its net and confidence code.', m(145), m(150), m(130), m(35), size=1.5)
s.text('Sources: photos in the project album; Motorcomm YT9215SCH datasheet V1.03; SCT2622 datasheet; KiCad 7 standard libraries.', m(15), m(195), size=1.4, italic=True)


# ======================================================================
# write files, CSV, netlist check
# ======================================================================
ROOTU = root.uuid
open(os.path.join(HERE, root.fname), 'w').write(root.render(ROOTU, '/' + ROOTU))
for ch in ALL[1:]:
    open(os.path.join(HERE, ch.fname), 'w').write(ch.render(ROOTU, '/' + ROOTU + '/' + ch.uuid))
for sh in ALL:
    rep = sh.margin_report
    print('margin check %-24s %s' % (sh.fname, 'ok' if not rep else '%d items too close: %s' % (len(rep), rep[:6])))

rows = []
for sh in ALL:
    for ref, pin, net, conf in sh.pins_used:
        rows.append((net, ref, pin, conf, sh.title))
seen = {}
for r in rows:
    seen[(r[1], r[2])] = r
rows = sorted(seen.values(), key=lambda r: (r[0], r[1], r[2]))
with open(os.path.join(HERE, 'lx-is601f-nets.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['net', 'ref', 'pin', 'confidence', 'sheet'])
    w.writerows(rows)
cnt = collections.Counter(r[3] for r in rows)
print('pins', len(rows), dict(cnt))

# netlist check
try:
    out = '/tmp/lx-is601f-check.net'
    subprocess.run(['kicad-cli', 'sch', 'export', 'netlist', '-o', out, os.path.join(HERE, root.fname)],
                   check=True, capture_output=True)
    from kisch import parse, find
    nl = parse(open(out).read())[0]
    actual = {}
    for net in find(find(nl, 'nets')[0], 'net'):
        name = find(net, 'name')[0][1]
        for node in find(net, 'node'):
            actual[(str(find(node, 'ref')[0][1]), str(find(node, 'pin')[0][1]))] = str(name)
    model = {(r[1], r[2]): r[0] for r in rows}
    # group check: every model net must map to exactly one KiCad net and vice versa
    m2k = collections.defaultdict(set); k2m = collections.defaultdict(set)
    for key, mn in model.items():
        if mn.startswith('('):
            continue
        kn = actual.get(key)
        m2k[mn].add(kn); k2m[kn].add(mn)
    bad = {m: k for m, k in m2k.items() if len(k) != 1 or None in k}
    bad2 = {k: m for k, m in k2m.items() if len(m) != 1}
    print('netlist check: %d model nets, %d split/missing, %d merged' % (len(m2k), len(bad), len(bad2)))
    for m, k in list(bad.items())[:20]:
        print('  SPLIT', m, k)
    for k, m in list(bad2.items())[:20]:
        print('  MERGED', k, m)
except FileNotFoundError:
    print('kicad-cli not found; skipped netlist check')
