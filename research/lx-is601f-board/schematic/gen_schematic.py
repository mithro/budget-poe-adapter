#!/usr/bin/env python3
"""Generate the LX-IS601F V2.0 reverse-engineered schematic (KiCad 7 .kicad_sch)
and a net table (CSV) from one data model.

Confidence codes (also used as wire styles in the schematic):
  C  confirmed: traced on both sides of the board, or measured with a meter
  V  visible: trace or pad adjacency seen on one side of the photos only
  I  inferred: from the chip datasheet, the part marking or usual practice
  U  unknown: pin exists, destination not yet traced

Run:  python3 gen_schematic.py   (writes lx-is601f.kicad_sch and lx-is601f-nets.csv
next to this script; export with kicad-cli sch export pdf/svg).
"""
import csv, os, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
U = lambda: str(uuid.uuid4())
ROOT = U()

STYLE = {  # wire stroke for each confidence level
    'C': '(stroke (width 0.35) (type solid) (color 0 160 0 1))',
    'V': '(stroke (width 0.35) (type solid) (color 0 90 220 1))',
    'I': '(stroke (width 0.3) (type dash) (color 230 120 0 1))',
    'U': '(stroke (width 0.3) (type dot) (color 210 0 0 1))',
}

parts = []   # dicts: ref, value, sym, x, y, pins[(num,name,side,net,conf)], note, fp
nets = {}    # net -> list of (ref,pin,conf)


def part(ref, value, x, y, left, right, note='', w=None, top=None):
    """left/right: lists of (num, name, net, conf) or None for a gap."""
    parts.append(dict(ref=ref, value=value, x=x, y=y, left=left, right=right,
                      note=note, w=w))


def two(ref, value, x, y, n1, n2, conf1='I', conf2=None, note=''):
    """Two-terminal part drawn as a small box with pin 1 left, pin 2 right."""
    part(ref, value, x, y, [('1', '', n1, conf1)], [('2', '', n2, conf2 or conf1)],
         note=note, w=7.62)


# ---------------------------------------------------------------- power input
X, Y = 30, 40
part('J2', 'POWER2 2-pin 2.54 (XH?)', X, Y,
     [], [('1', 'V+', 'VIN_RAW', 'I'), ('2', 'V-', 'GND', 'I')],
     note='DC input, likely 48-57 V. Polarity not checked.')
two('L1', 'L1 (white SMD, fuse or inductor?)', X + 45, Y - 10, 'VIN_RAW', 'VIN_F', 'I')
two('D4', 'SS510 (LGE)', X + 45, Y + 5, 'VIN_F', 'VIN_P', 'I', note='Series reverse-polarity diode? (inferred)')
two('D1', 'SS510 (LGE)', X + 45, Y + 20, 'VIN_RAW', 'TBD_D1_K', 'U')
two('D5', 'SS510 (LGE)', X + 45, Y + 35, 'TBD_D5_A', 'TBD_D5_K', 'U')
for i, ref in enumerate(['RV1', 'RV2', 'RV3']):
    two(ref, 'blue disc, varistor/Y-cap?', X + 90, Y - 10 + 15 * i, 'VIN_F' if i == 0 else 'TBD_' + ref, 'GND' if i == 0 else 'TBD_' + ref + '_2', 'U')
two('L2', '"701" power inductor/CMC', X + 135, Y - 10, 'VIN_P', 'VIN48', 'I')
two('C1', '1206 MLCC', X + 135, Y + 5, 'VIN48', 'GND', 'I')
two('C2', '1206 MLCC', X + 135, Y + 20, 'VIN48', 'GND', 'I')
two('C3', '1206 MLCC', X + 135, Y + 35, 'VIN48', 'GND', 'I')
two('C4', '47uF 63V alu (YX)', X + 135, Y + 50, 'VIN48', 'GND', 'I')

# ---------------------------------------------------------------- 3.3 V buck
X, Y = 40, 135
part('PU1', 'SCT2622 (mark "2622 SCT 6DC") 60V 2A buck', X, Y,
     [('2', 'VIN', 'VIN48', 'I'), ('3', 'EN', 'BUCK_EN', 'I'), ('4', 'RT', 'BUCK_RT', 'I'),
      ('5', 'FB', 'BUCK_FB', 'I')],
     [('1', 'BOOT', 'BUCK_BST', 'I'), ('8', 'SW', 'BUCK_SW', 'I'), ('6', 'COMP', 'BUCK_COMP', 'I'),
      ('7', 'GND', 'GND', 'I'), ('9', 'EPAD', 'GND', 'I')],
     note='Pin NUMBERS not verified (no datasheet pin table found); pin functions from SCT2622 datasheet text.', w=25.4)
two('PC6', 'MLCC (boot cap?)', X + 50, Y - 12, 'BUCK_BST', 'BUCK_SW', 'I')
two('PL3', '10uH "100"', X + 50, Y + 3, 'BUCK_SW', '+3V3', 'V')
two('D40', 'Schottky (catch)', X + 50, Y + 18, 'GND', 'BUCK_SW', 'I')
two('PR2', '"30D" = 200k', X + 95, Y - 12, '+3V3', 'BUCK_FB', 'I')
two('PR3', '"304" = 300k', X + 95, Y + 3, 'BUCK_FB', 'GND', 'I', note='Divider pair not verified; 3.3 V needs Vref*(1+PR2/PR3)')
two('PR1', '"86C" = 73.2k', X + 95, Y + 18, 'BUCK_RT', 'GND', 'I')
two('R7', '0603', X + 95, Y + 33, 'VIN48', 'BUCK_EN', 'I')
two('R8', '"49C" = 31.6k', X + 95, Y + 48, 'BUCK_EN', 'GND', 'I')
two('PC2', 'MLCC (comp?)', X + 140, Y - 12, 'BUCK_COMP', 'TBD_PC2', 'I')
two('R11', '"31C" (comp?)', X + 140, Y + 3, 'TBD_PC2', 'GND', 'I')
two('TC1', '220uF 16V alu (YX)', X + 140, Y + 18, '+3V3', 'GND', 'I')
two('C23', '1206 MLCC', X + 140, Y + 33, '+3V3', 'GND', 'I')
two('C24', '1206 MLCC', X + 140, Y + 48, '+3V3', 'GND', 'I')

# ---------------------------------------------------------------- U4 YT9215SCH
U4X, U4Y = 330, 125
MDI = {3: range(1, 10), 4: range(19, 28), 0: range(95, 104), 1: range(105, 114), 2: range(119, 128)}
mdi_names = ['MDIAP', 'MDIAN', 'MDIBP', 'MDIBN', None, 'MDICP', 'MDICN', 'MDIDP', 'MDIDN']
pin = {}
for p, rng in MDI.items():
    for k, n in enumerate(rng):
        nm = mdi_names[k]
        if nm is None:
            pin[n] = ('AVDDL', '+1V15', 'I')
        else:
            pin[n] = ('P%d%s' % (p, nm), 'P%d_%s' % (p, nm[3:]), 'I')
for n in (10, 16, 18, 28, 86, 94, 104, 114, 118, 128):
    pin[n] = ('AVDDH', '+3V3', 'I')
pin[13] = ('AVDDL', '+1V15', 'I')
for n in (17, 58, 69):
    pin[n] = ('DVDDL', '+1V15', 'I')
for n in (45, 59):
    pin[n] = ('DVDDIO_1', '+3V3', 'I')
for n in (68, 82):
    pin[n] = ('DVDDIO', '+3V3', 'I')
pin.update({
    11: ('AGND', 'GND', 'I'), 12: ('RBIAS', 'RBIAS', 'I'), 14: ('NC', None, 'I'), 15: ('NC', None, 'I'),
    29: ('SVDDH', '+3V3', 'I'), 30: ('SGND_1', 'GND', 'I'), 31: ('HSON_1', 'SDS1_TXN', 'I'),
    32: ('HSOP_1', 'SDS1_TXP', 'I'), 33: ('SVDDL_1', '+1V15', 'I'), 34: ('HSIP_1', 'SDS1_RXP', 'I'),
    35: ('HSIN_1', 'SDS1_RXN', 'I'), 36: ('SGND_1', 'GND', 'I'), 37: ('SGND_0', 'GND', 'I'),
    38: ('HSON_0', 'SDS0_TXN', 'U'), 39: ('HSOP_0', 'SDS0_TXP', 'U'), 40: ('SVDDL_0', '+1V15', 'I'),
    41: ('HSIP_0', 'SDS0_RXP', 'U'), 42: ('HSIN_0', 'SDS0_RXN', 'U'), 43: ('SGND_0', 'GND', 'I'),
    44: ('GPIO5/INTERRUPT', 'TBD_U4_44', 'U'), 46: ('GPIO6/UART0_RX', 'U4_46_NOTRACE', 'V'),
    47: ('GPIO7/UART0_TX', 'U4_47_NOTRACE', 'V'), 48: ('GPIO8', 'TBD_U4_48', 'U'),
    49: ('GPIO9/SPF0_SCK/SPF_MUX_SEL', 'SPF0_SCK', 'V'), 50: ('GPIO10/SPF0_SI', 'SPF0_SI', 'V'),
    51: ('GPIO11/SWITCH_ID_0', 'TBD_U4_51', 'U'), 52: ('GPIO12', 'TBD_U4_52', 'U'), 53: ('GPIO13', 'TBD_U4_53', 'U'),
    54: ('GPIO14/SPF0_SO', 'SPF0_SO', 'V'), 55: ('GPIO15/SPF0_CS', 'SPF0_CS', 'V'),
    56: ('GPIO16', 'TBD_U4_56', 'U'), 57: ('GPIO17', 'TBD_U4_57', 'U'),
    60: ('EN_SWR', '+3V3', 'I'), 61: ('GND_SWR', 'GND', 'I'), 62: ('GND_SWR', 'GND', 'I'),
    63: ('LX', 'SWR_LX', 'V'), 64: ('LX', 'SWR_LX', 'V'), 65: ('HV_SWR', '+3V3', 'I'), 66: ('HV_SWR', '+3V3', 'I'),
    67: ('GPIO31/P9LED0', 'LED_P9_0', 'U'),
    70: ('GPIO32/UART1_RX/P4LED2/DIS_SPIS', 'U4_70', 'U'), 71: ('GPIO33/P4LED0/EEPROM_MOD', 'LED_P4_0', 'I'),
    72: ('GPIO34/P4LED1', 'U4_72', 'U'), 73: ('GPIO35/P3LED1', 'U4_73', 'U'), 74: ('GPIO36/P3LED2/EN_PWRLIGHT', 'U4_74', 'U'),
    75: ('GPIO37/P3LED0/EN_SPIF', 'LED_P3_0', 'I'), 76: ('GPIO38/UART1_TX/P2LED2/DIS_MCU', 'U4_76', 'U'),
    77: ('GPIO39/P2LED0/DISAUTOLOAD', 'LED_P2_0', 'I'), 78: ('GPIO40/SPF1_SO/P2LED1', 'U4_78', 'U'),
    79: ('GPIO41/SPF1_SI/P1LED2', 'U4_79_NOTRACE', 'V'), 80: ('GPIO42/P1LED0', 'LED_P1_0', 'I'),
    81: ('GPIO43/SPF1_CS/P1LED1', 'U4_81', 'U'), 83: ('GPIO44/SPF1_SCK/P0LED2/EN_PHY', 'U4_83', 'U'),
    84: ('GPIO45/LED_DA/P0LED1', 'U4_84', 'U'), 85: ('GPIO46/LED_CK/P0LED0', 'LED_P0_0', 'I'),
    87: ('XTALO', 'XTALO', 'V'), 88: ('XTALI', 'XTALI', 'V'), 89: ('nRESET', 'NRESET', 'U'),
    90: ('GPIO47/SSPI_CS', 'U4_90_NOTRACE', 'V'), 91: ('GPIO48/SCL/MDC', 'I2C_SCL', 'I'),
    92: ('GPIO49/SDA/MDIO', 'I2C_SDA', 'I'), 93: ('GPIO50/SSPI_SO', 'TBD_U4_93', 'U'),
    115: ('PLLVDDL', '+1V15', 'I'), 116: ('NC', None, 'I'), 117: ('PLLGND', 'GND', 'I'), 129: ('EPAD', 'GND', 'I'),
})
assert sorted(pin) == list(range(1, 130)), set(range(1, 130)) - set(pin)
left = [(str(n),) + pin[n] for n in range(1, 65)]
right = [(str(n),) + pin[n] for n in range(65, 130)]
part('U4', 'YT9215SCH (LQFP-128 + EPAD)', U4X, U4Y, left, right, w=50.8,
     note='Pin functions from YT9215SCH datasheet V1.03. MDI/power/strap nets inferred unless marked V.')

# core rail, crystal, rbias
X, Y = 470, 40
two('L3', '4.7uH "4R7"', X, Y, 'SWR_LX', '+1V15', 'V', note='Internal SWR output inductor')
two('Y6', '25.000 MHz 3225', X, Y + 15, 'XTALI', 'XTALO', 'V')
two('C43', '0402 load cap', X, Y + 30, 'XTALO', 'GND', 'V')
two('C44', '0402 load cap', X, Y + 45, 'XTALI', 'GND', 'V')
two('R_RBIAS', '2.49k 1% (ref TBD)', X, Y + 60, 'RBIAS', 'GND', 'I')
two('C_RST', 'reset RC (refs TBD)', X, Y + 75, 'NRESET', 'GND', 'U')

# SPF0 resistors and the empty flash footprint on the bottom
X, Y = 470, 150
two('R93', '0402', X, Y, 'SPF0_SCK', 'FL_SCK', 'V')
two('R92', '0402', X, Y + 15, 'SPF0_SI', 'FL_SI', 'V')
two('R89', '0402', X, Y + 30, 'SPF0_SO', 'FL_SO', 'V')
two('R44', '0402', X, Y + 45, 'SPF0_CS', 'FL_CS', 'V')
part('U6', 'DNP: SOP-8/WSON-8 SPI flash footprint (bottom)', X + 60, Y + 20,
     [('1', 'CS#', 'FL_CS', 'U'), ('2', 'DO', 'FL_SO', 'U'), ('3', 'WP#', 'TBD_U6_3', 'U'), ('4', 'GND', 'GND', 'U')],
     [('8', 'VCC', '+3V3', 'U'), ('7', 'HOLD#', 'TBD_U6_7', 'U'), ('6', 'CLK', 'FL_SCK', 'U'), ('5', 'DI', 'FL_SI', 'U')],
     note='Unpopulated. Assumed 25-series pinout. R40/R94/R96/R98/R100/R102/R109 sit beside it.', w=20.32)

# EEPROM on the bottom
X, Y = 470, 240
part('U10', 'HK24C08 (HK 24C08 2S3746HA) I2C EEPROM, bottom', X + 30, Y,
     [('1', 'A0', 'GND', 'I'), ('2', 'A1', 'GND', 'I'), ('3', 'A2', 'GND', 'I'), ('4', 'GND', 'GND', 'I')],
     [('8', 'VCC', '+3V3', 'I'), ('7', 'WP', 'TBD_U10_WP', 'U'), ('6', 'SCL', 'I2C_SCL', 'I'), ('5', 'SDA', 'I2C_SDA', 'I')],
     note='Standard 24Cxx pinout. R14/R16/R19/R29/R30 and C15 nearby: pull-ups/address straps (inferred).', w=20.32)

# ---------------------------------------------------------------- ports
# magnetics: assumed common 24-pin 1-port GbE pinout (chip side 1-12, line side 13-24)
PORTMAP = [  # (chip port, magnetics, rj45 ref, rj45 pos, ESD refs, poe?)
    (0, 'DXFRM4', 'J1A', 'J1 port 1 (PoE)', ('ED1', 'ED10'), True),
    (1, 'DXFRM3', 'J1B', 'J1 port 2 (PoE)', ('ED2', 'ED3'), True),
    (2, 'DXFRM2', 'J1C', 'J1 port 3 (PoE)', ('ED4', 'ED5'), True),
    (3, 'DXFRM5', 'J1D', 'J1 port 4 (PoE)', ('ED6', 'ED7'), True),
    (4, 'DXFRM6', 'J3', 'uplink RJ45 (no PoE)', ('ED8', 'ED9'), False),
]
for k, (p, xf, jref, jdesc, eds, poe) in enumerate(PORTMAP):
    X, Y = 30 + 125 * k, 360
    P = 'P%d_' % p
    L = 'L%d_' % p
    part(xf, 'United-tek G2401PR (port P%d?)' % p, X + 30, Y,
         [('2', 'TD1+', P + 'AP', 'I'), ('3', 'TD1-', P + 'AN', 'I'), ('1', 'TCT1', P + 'TCT', 'U'),
          ('5', 'TD2+', P + 'BP', 'I'), ('6', 'TD2-', P + 'BN', 'I'), ('4', 'TCT2', P + 'TCT', 'U'),
          ('8', 'TD3+', P + 'CP', 'I'), ('9', 'TD3-', P + 'CN', 'I'), ('7', 'TCT3', P + 'TCT', 'U'),
          ('11', 'TD4+', P + 'DP', 'I'), ('12', 'TD4-', P + 'DN', 'I'), ('10', 'TCT4', P + 'TCT', 'U')],
         [('23', 'MX1+', L + '1', 'V'), ('22', 'MX1-', L + '2', 'V'), ('24', 'MCT1', L + 'CT1', 'U'),
          ('20', 'MX2+', L + '3', 'V'), ('19', 'MX2-', L + '6', 'V'), ('21', 'MCT2', L + 'CT2', 'U'),
          ('17', 'MX3+', L + '4', 'V'), ('16', 'MX3-', L + '5', 'V'), ('18', 'MCT3', L + 'CT3', 'U'),
          ('14', 'MX4+', L + '7', 'V'), ('13', 'MX4-', L + '8', 'V'), ('15', 'MCT4', L + 'CT4', 'U')],
         note='Pinout assumed (no G2401PR datasheet found). Port-to-chip mapping inferred from placement.', w=20.32)
    part(jref, 'RJ45 ' + jdesc, X + 30, Y + 75,
         [('1', '1', L + '1', 'I'), ('2', '2', L + '2', 'I'), ('3', '3', L + '3', 'I'), ('6', '6', L + '6', 'I')],
         [('4', '4', L + '4', 'I'), ('5', '5', L + '5', 'I'), ('7', '7', L + '7', 'I'), ('8', '8', L + '8', 'I'),
          ('SH', 'SHIELD', 'CHASSIS', 'U')], w=15.24)
    for j, ed in enumerate(eds):
        pairs = [('A', 'B'), ('C', 'D')][j]
        part(ed, '"05U" SOT-23-6 ESD array', X + 30, Y + 120 + 30 * j,
             [('1', 'IO1', P + pairs[0] + 'P', 'I'), ('3', 'IO2', P + pairs[0] + 'N', 'I'), ('2', 'GND', 'GND', 'I')],
             [('6', 'IO4', P + pairs[1] + 'P', 'I'), ('4', 'IO3', P + pairs[1] + 'N', 'I'), ('5', 'VCC', 'TBD_ESD_VCC', 'U')],
             note='Pinout assumed (ULC0524P-style). Which pairs each array guards is inferred.', w=15.24)

# SFP connector (U12) on SerDes 0
X, Y = 660, 360
part('U12', 'SFP 20-pin host connector (+ cage on some boards)', X, Y,
     [('18', 'TD+', 'SDS0_TXP', 'U'), ('19', 'TD-', 'SDS0_TXN', 'U'), ('13', 'RD+', 'SDS0_RXP', 'U'),
      ('12', 'RD-', 'SDS0_RXN', 'U'), ('15', 'VCCR', '+3V3', 'U'), ('16', 'VCCT', '+3V3', 'U')],
     [('4', 'MOD-DEF2/SDA', 'TBD_SFP_SDA', 'U'), ('5', 'MOD-DEF1/SCL', 'TBD_SFP_SCL', 'U'),
      ('6', 'MOD-DEF0', 'TBD_SFP_PRES', 'U'), ('8', 'LOS', 'TBD_SFP_LOS', 'U'), ('3', 'TX_DIS', 'TBD_SFP_TXDIS', 'U'),
      ('2', 'TX_FAULT', 'TBD_SFP_TXF', 'U'), ('10', 'VEET', 'GND', 'U')],
     note='Which SerDes (0 or 1) feeds the SFP is not traced; AC-coupling caps not yet found.', w=30.48)

# ---------------------------------------------------------------- PoE daughterboard
X, Y = 660, 40
part('PIN1', '8-pin 2.54 header: mainboard <-> PoE module', X, Y,
     [('1', '1', 'TBD_PIN1_1', 'U'), ('2', '2', 'TBD_PIN1_2', 'U'), ('3', '3', 'TBD_PIN1_3', 'U'), ('4', '4', 'TBD_PIN1_4', 'U')],
     [('5', '5', 'TBD_PIN1_5', 'U'), ('6', '6', 'TBD_PIN1_6', 'U'), ('7', '7', 'TBD_PIN1_7', 'U'), ('8', '8', 'TBD_PIN1_8', 'U')],
     note='Header row runs along J1. Probably port center-tap feeds; needs continuity check.', w=20.32)
part('U1', '"2184A 533AQ1H" QFN-48 4-port PSE controller (PoE module)', X, Y + 70,
     [('?a', 'VIN', 'VIN48', 'U'), ('?b', 'GND', 'GND', 'U'), ('?c', 'SENSE1', 'POE_SNS1', 'U'), ('?d', 'SENSE2', 'POE_SNS2', 'U'),
      ('?e', 'SENSE3', 'POE_SNS3', 'U'), ('?f', 'SENSE4', 'POE_SNS4', 'U')],
     [('?g', 'PORT1', 'POE_OUT1', 'U'), ('?h', 'PORT2', 'POE_OUT2', 'U'), ('?i', 'PORT3', 'POE_OUT3', 'U'),
      ('?j', 'PORT4', 'POE_OUT4', 'U')],
     note='Part not identified (IP804AR-class?). Functional pins only; numbers unknown.', w=30.48)
for i, (rs, rd, d) in enumerate([('R8', 'R3', 'D1'), ('R12', 'R9', 'D3'), ('R13', 'R10', 'D5'), ('R14', 'R11', 'D7')]):
    two('PM_' + rs, '0R25 sense "R250" (module %s)' % rs, X + 70, Y + 115 + 15 * i, 'POE_SNS%d' % (i + 1), 'GND', 'U')
    two('PM_' + rd, '33R "330" (module %s)' % rd, X + 110, Y + 115 + 15 * i, 'POE_OUT%d' % (i + 1), 'TBD_PM_%s' % rd, 'U')
    two('PM_' + d, 'TVS "RGS" SMB (module %s)' % d, X + 150, Y + 115 + 15 * i, 'POE_OUT%d' % (i + 1), 'VIN48', 'U')

# ---------------------------------------------------------------- LEDs
X, Y = 620, 250
for i in range(6):
    two('LED_FX%d' % (i + 1), 'FX LED row %d (0603)' % (i + 1), X, Y + 10 * i, '+3V3', 'LEDFX_%d' % (i + 1), 'U')
    two('LED_POW%d' % (i + 1), 'POW LED row %d (0603)' % (i + 1), X + 45, Y + 10 * i, '+3V3', 'LEDPOW_%d' % (i + 1), 'U')

# ------------------------------------------------------------------ writer

def sym_def(p):
    nl = len(p['left']); nr = len(p['right'])
    w = p['w'] or 25.4
    h = max(nl, nr, 1) * 2.54 + 2.54
    name = 'lxr:' + p['ref']
    out = ['(symbol "%s" (in_bom yes) (on_board yes)' % name,
           '(property "Reference" "%s" (at 0 %.2f 0) (effects (font (size 1.27 1.27))))' % (p['ref'], h / 2 + 2.54),
           '(property "Value" "%s" (at 0 %.2f 0) (effects (font (size 1.27 1.27))))' % (p['ref'], -h / 2 - 2.54),
           '(property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '(property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           '(symbol "%s_0_1" (rectangle (start %.2f %.2f) (end %.2f %.2f) (stroke (width 0.254) (type default)) (fill (type background))))'
           % (p['ref'], -w / 2, h / 2, w / 2, -h / 2),
           '(symbol "%s_1_1"' % p['ref']]
    pins = []
    for side, lst in (('L', p['left']), ('R', p['right'])):
        for i, pp in enumerate(lst):
            num, nm = pp[0], pp[1]
            y = h / 2 - 2.54 - 2.54 * i
            x = -w / 2 - 2.54 if side == 'L' else w / 2 + 2.54
            ang = 0 if side == 'L' else 180
            out.append('(pin passive line (at %.2f %.2f %d) (length 2.54) (name "%s" (effects (font (size 1.0 1.0)))) (number "%s" (effects (font (size 1.0 1.0)))))'
                       % (x, y, ang, nm or '~', num))
            pins.append((side, x, y, pp))
    out.append('))')
    return '\n'.join(out), pins, h


def esc(s):
    return s.replace('"', "'")


lib, body, rows = [], [], []
for p in parts:
    d, pins, h = sym_def(p)
    lib.append(d)
    X0, Y0 = p['x'], p['y']
    inst = ['(symbol (lib_id "lxr:%s") (at %.2f %.2f 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (uuid %s)' % (p['ref'], X0, Y0, U()),
            '(property "Reference" "%s" (at %.2f %.2f 0) (effects (font (size 1.5 1.5) bold)))' % (p['ref'], X0, Y0 - h / 2 - 1.5),
            '(property "Value" "%s" (at %.2f %.2f 0) (effects (font (size 1.1 1.1))))' % (esc(p['value']), X0, Y0 + h / 2 + 1.5),
            '(property "Footprint" "" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))' % (X0, Y0),
            '(property "Datasheet" "" (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) hide))' % (X0, Y0)]
    for side, x, y, pp in pins:
        inst.append('(pin "%s" (uuid %s))' % (pp[0], U()))
    inst.append('(instances (project "lx-is601f" (path "/%s" (reference "%s") (unit 1)))))' % (ROOT, p['ref']))
    body.append('\n'.join(inst))
    if p['note']:
        body.append('(text "%s" (at %.2f %.2f 0) (effects (font (size 1.0 1.0) italic) (justify left bottom)) (uuid %s))'
                    % (esc(p['note']), X0 - (p['w'] or 25.4) / 2, Y0 + h / 2 + 4.5, U()))
    for side, x, y, pp in pins:
        num, nm, net, conf = pp
        px, py = X0 + x, Y0 - y
        if net is None:
            body.append('(no_connect (at %.2f %.2f) (uuid %s))' % (px, py, U()))
            rows.append((p['ref'], num, nm, '(NC)', conf))
            continue
        ex = px - 5.08 if side == 'L' else px + 5.08
        body.append('(wire (pts (xy %.2f %.2f) (xy %.2f %.2f)) %s (uuid %s))' % (px, py, ex, py, STYLE[conf], U()))
        body.append('(label "%s" (at %.2f %.2f %d) (effects (font (size 1.0 1.0)) (justify %s bottom)) (uuid %s))'
                    % (net, ex, py, 0 if side == 'R' else 180, 'left' if side == 'R' else 'right', U()))
        rows.append((p['ref'], num, nm, net, conf))
        nets.setdefault(net, []).append((p['ref'], num, conf))

legend = ('Wire style = confidence.  Green solid: C confirmed (both sides / meter).  Blue solid: V seen on one side in photos.  '
          'Orange dashed: I inferred from datasheet/marking/usual practice.  Red dotted: U unknown, not yet traced.  '
          'Labels starting TBD_ are placeholders for untraced nets.')
title = ('(title_block (title "LX-IS601F V2.0 reverse-engineered, pass 1") (date "2026-11-17") (rev "0.1")'
         ' (comment 1 "Traced from photos only. Nothing is yet confirmed on both sides; see lx-is601f-nets.csv")'
         ' (comment 2 "Main IC: Motorcomm YT9215SCH. PoE: 4-port PSE module on PIN1 header."))')
sch = ['(kicad_sch (version 20230121) (generator eeschema)', '(uuid %s)' % ROOT, '(paper "A1")', title,
       '(lib_symbols', '\n'.join(lib), ')',
       '(text "%s" (at 20 20 0) (effects (font (size 2 2) bold) (justify left bottom)) (uuid %s))' % (legend, U()),
       '(text "POWER INPUT" (at 25 25 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid %s))' % U(),
       '(text "3.3 V BUCK (PU1)" (at 25 115 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid %s))' % U(),
       '(text "SWITCH U4" (at 300 35 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid %s))' % U(),
       '(text "PORTS: magnetics, RJ45, ESD" (at 25 330 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid %s))' % U(),
       '(text "PoE MODULE (daughterboard)" (at 640 25 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid %s))' % U(),
       '(text "PORT LEDs (FX / POW columns, rows 1-6)" (at 600 240 0) (effects (font (size 2.5 2.5) bold) (justify left bottom)) (uuid %s))' % U(),
       '\n'.join(body),
       '(sheet_instances (path "/" (page "1")))', ')']
open(os.path.join(HERE, 'lx-is601f.kicad_sch'), 'w').write('\n'.join(sch))
with open(os.path.join(HERE, 'lx-is601f-nets.csv'), 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['net', 'ref', 'pin', 'pin_name', 'confidence'])
    for r in sorted(rows, key=lambda r: (r[3], r[0], r[1])):
        w.writerow([r[3], r[0], r[1], r[2], r[4]])
print('parts', len(parts), 'pins', len(rows), 'nets', len(nets))
from collections import Counter
print(Counter(r[4] for r in rows))
