#!/usr/bin/env python3
"""Part list of the discrete PoE front end: the one place that names every part.

Used by schematic/gen_schematic.py (values on the schematic) and bom.py (the BOM tables).
The simulation keeps its own numeric values in sim/frontend.py; gen_schematic.py checks that
the two agree.

Each entry: reference -> (block, value, package, part number, LCSC number).
Blocks: input, hotswap, class, mark, twoevent.
"""

def _r(block, value, lcsc, pkg="0603"):
    return (block, value, pkg, "Chip resistor 1 %", lcsc)

PARTS = {
    # input: bridges, surge clamp, detection signature
    "BR1": ("input", "ABS210", "ABS", "ABS210", "C2892567"),
    "BR2": ("input", "ABS210", "ABS", "ABS210", "C2892567"),
    "D1": ("input", "SMAJ58A", "SMA", "SMAJ58A", "C2980408"),
    "R1": _r("input", "24.9 kΩ", "C2930420", "1206"),
    "C1": ("input", "100 nF 100 V", "0805", "CL21B104KCFNNNE", "C28233"),
    # hot swap
    "D6": ("hotswap", "24 V", "SOD-123", "BZT52C24", "C19077416"),
    "R27": _r("hotswap", "1 MΩ", "C17514", "0805"),
    "R28": _r("hotswap", "2 MΩ", "C22976"),
    "D7": ("hotswap", "12 V", "SOD-123", "BZT52C12", "C19077410"),
    "C4": ("hotswap", "330 nF 25 V", "0603", "0603B334K250NT", "C1615"),
    "C5": ("hotswap", "6.8 nF 100 V", "0603", "0603B682K101NT", "C81355"),
    "R31": _r("hotswap", "100 Ω", "C22775"),
    "Q13": ("hotswap", "15N10", "TO-252", "15N10", "C359106"),
    # class window switch and class current sink
    "Q3": ("class", "BSS123", "SOT-23", "BSS123", "C427379"),
    "R5": _r("class", "1 MΩ", "C17514", "0805"),
    "R6": _r("class", "1 MΩ", "C22935"),
    "D3": ("class", "22 V", "SOD-123", "BZT52C22", "C22375295"),
    "R7": _r("class", "100 kΩ", "C25803"),
    "R8": _r("class", "100 kΩ", "C25803"),
    "Q4": ("class", "MMBT3904", "SOT-23", "MMBT3904", "C84104"),
    "D2": ("class", "10 V 2 %", "SOD-123", "BZT52B10", "C22395568"),
    "R2": _r("class", "4.7 kΩ", "C23162"),
    "U1": ("class", "LR432B", "SOT-23", "LR432BTLT1G", "C411185"),
    "R29": _r("class", "1 kΩ", "C21190"),
    "R32": _r("class", "47 kΩ", "C105579"),
    "C7": ("class", "4.7 nF 50 V", "0603", "0603B472K500NT", "C53987"),
    "Q1": ("class", "MMBT3904", "SOT-23", "MMBT3904", "C84104"),
    "Q2": ("class", "BCX53-16", "SOT-89", "BCX53-16", "C41375135"),
    "R3": _r("class", "10 kΩ", "C25804"),
    "R4": _r("class", "See class table", None),
    # mark latch
    "R9": _r("mark", "220 kΩ", "C22961"),
    "R10": _r("mark", "220 kΩ", "C22961"),
    "Q5": ("mark", "MMBT3904", "SOT-23", "MMBT3904", "C84104"),
    "R11": _r("mark", "22 kΩ", "C31850"),
    "R12": _r("mark", "47 kΩ", "C105579"),
    "Q6": ("mark", "PMBS3906", "SOT-23", "PMBS3906,215", "C8669"),
    "R13": _r("mark", "10 kΩ", "C25804"),
    "R14": _r("mark", "270 kΩ", "C22965"),
    # two-event detector and T2P output
    "R15": _r("twoevent", "100 kΩ", "C25803"),
    "R16": _r("twoevent", "470 kΩ", "C23178"),
    "Q7": ("twoevent", "MMBT3904", "SOT-23", "MMBT3904", "C84104"),
    "R17": _r("twoevent", "10 kΩ", "C25804"),
    "D4": ("twoevent", "BAT54W", "SOD-123", "BAT54W", "C7502705"),
    "C2": ("twoevent", "220 nF 25 V", "0603", "CL10B224KA8NNNC", "C21120"),
    "R18": _r("twoevent", "220 kΩ", "C22961"),
    "D8": ("twoevent", "BAT54W", "SOD-123", "BAT54W", "C7502705"),
    "R19": _r("twoevent", "1 MΩ", "C22935"),
    "R30": _r("twoevent", "220 kΩ", "C22961"),
    "Q8": ("twoevent", "MMBT3904", "SOT-23", "MMBT3904", "C84104"),
    "R20": _r("twoevent", "47 kΩ", "C105579"),
    "R21": _r("twoevent", "47 kΩ", "C105579"),
    "Q9": ("twoevent", "PMBS3906", "SOT-23", "PMBS3906,215", "C8669"),
    "R22": _r("twoevent", "68 kΩ", "C23231"),
    "D5": ("twoevent", "BAT54W", "SOD-123", "BAT54W", "C7502705"),
    "Q10": ("twoevent", "BSS123", "SOT-23", "BSS123", "C427379"),
    "C3": ("twoevent", "220 nF 25 V", "0603", "CL10B224KA8NNNC", "C21120"),
    "R23": _r("twoevent", "10 MΩ", "C7250"),
    "Q11": ("twoevent", "BSS123", "SOT-23", "BSS123", "C427379"),
    "R24": _r("twoevent", "220 kΩ", "C22961"),
    "R25": _r("twoevent", "470 kΩ", "C23178"),
    "Q12": ("twoevent", "PMBS3906", "SOT-23", "PMBS3906,215", "C8669"),
    "R26": _r("twoevent", "100 kΩ", "C25803"),
}

# Class programming resistor R4: class -> (value in ohms, LCSC number). "4T" is Class 4 with the
# mark latch and the two-event detector fitted (their current adds to the class current).
R4 = {
    "1": (140.0, "C22876"),
    "2": (73.2, "C218138"),
    "3": (47.5, "C23062"),
    "4": (31.6, "C273790"),
    "4T": (35.7, "C158925"),
}

# Parts that are not part of the front end but appear in the cost comparison.
OTHER = {
    "C6": ("converter", "47 µF 100 V", "8 mm can", "RV100V47M8X10", "C48935391"),
    "TMI7303B": ("alternative", "802.3at PD controller", "DFN-10", "TMI7303B", "C29779845"),
    "TPS2378": ("alternative", "802.3at PD controller", "SO-8", "TPS2378DDAR", "C337500"),
    "TLV431A": ("alternative", "1.24 V shunt reference", "SOT-23", "TLV431ASN1T1G", "C127592"),
    "MB10F": ("alternative", "1 A bridge", "MBF", "MB10F", "C52023840"),
}

BLOCKS = {
    "input": "Input",
    "hotswap": "Hot swap",
    "class": "Class sink",
    "mark": "Mark latch",
    "twoevent": "Two-event detector",
}
