#!/usr/bin/env python3
"""Bill of materials of both options: writes the CSV files and the tables of the note.

Run it from any folder. It rewrites bom-option-a.csv, bom-option-b.csv and every block of
../block-diagram-and-bom.md that sits between a BEGIN and an END marker.
"""
import csv
import pathlib
import re

HERE = pathlib.Path(__file__).resolve().parent
NOTE = HERE.parent / "block-diagram-and-bom.md"

LCSC = "LCSC"
JLC = "JLCPCB"
EST = "Estimate"

# id: (part, maker, package, value, rating, catalogue number, unit price in USD, price source, price tier)
PARTS = {
    "sw": ("YT9215SC", "Motorcomm", "LQFP-128", "–", "–", "C51037433", 2.8893, LCSC, "900"),
    "flash": ("P25Q40SH-SSH-IT", "Puya", "SOP-8", "4 Mbit", "–", "C2836860", 0.1001, LCSC, "2,500"),
    "xtal": ("X322525MOB4SI", "YXC", "3.2 × 2.5 mm", "25 MHz", "–", "C9006", 0.0505, LCSC, "3,000"),
    "rj45": ("R-RJ45R08P-A004", "Ckmtw", "Through-hole", "–", "–", "C385834", 0.1049, LCSC, "992"),
    "xfmr": ("G2415S", "CND-tek", "SMD 24-pin", "350 µH", "–", "C3003219", 0.3006, LCSC, "850"),
    "bridge": ("MB10S-50MIL", "MDD", "MBS", "–", "1 A", "C2488", 0.0145, LCSC, "3,000"),
    "tvs": ("SMAJ58A", "Goodwork", "SMA", "–", "58 V", "C2980408", 0.0186, LCSC, "2,000"),
    "elec": ("ERM1KM220E12OT", "Aishi", "6.3 × 12 mm", "22 µF", "100 V", "C106608", 0.0250, LCSC, "1,000"),
    "hsfet": ("NCE0130KA", "NCE", "TO-252", "–", "100 V", "C502817", 0.3143, LCSC, "2,500"),
    "zener": ("Not selected", "Not selected", "SOD-123", "Set by the PoE design", "–", "", 0.0100, EST, "–"),
    "zgate": ("BZT52C15", "Goodwork", "SOD-123", "15 V", "–", "C2932746", 0.0099, LCSC, "3,000"),
    "npn": ("MMBT5551", "JSCJ", "SOT-23", "–", "160 V", "C2145", 0.0096, LCSC, "3,000"),
    "buck5": ("RT6365GSP", "Richtek", "SOP-8-EP", "5 A", "60 V", "C3024482", 0.5319, LCSC, "1,000"),
    "diode": ("SS56", "MDD", "SMA", "5 A", "60 V", "C65009", 0.0353, LCSC, "1,000"),
    "l10": ("MWSA1005S-100MT", "Sunlord", "11.5 × 10 mm", "10 µH", "8 A", "C17700185", 0.1862, JLC, "2,500"),
    "c2u2hv": ("CS3225X7R225K101NRK", "Samwha", "1210", "2.2 µF", "100 V", "C2900749", 0.0658, LCSC, "2,000"),
    "c22u": ("CL31A226KAHNNNE", "Samsung", "1206", "22 µF", "25 V", "C12891", 0.0646, LCSC, "2,000"),
    "buck33": ("MT2492", "Aerosemi", "SOT-23-6", "2 A", "–", "C89358", 0.0361, LCSC, "1,000"),
    "l4u7": ("SWPA4030S4R7NT", "Sunlord", "4 × 4 mm", "4.7 µH", "2 A", "C193025", 0.0411, JLC, "2,000"),
    "l2u2": ("SWPA4018S2R2MT", "Sunlord", "4 × 4 mm", "2.2 µH", "–", "C50543", 0.0357, JLC, "3,000"),
    "bead": ("BLM18KG221SN1D", "Murata", "0603", "220 Ω", "2.2 A", "C88980", 0.0291, LCSC, "4,000"),
    "pfet": ("AO4407A", "AOS", "SOIC-8", "12 A", "30 V", "C16072", 0.1683, LCSC, "3,000"),
    "dtc": ("DTC143ZCA", "JSCJ", "SOT-23", "4.7 kΩ", "50 V", "C15236", 0.0142, LCSC, "3,000"),
    "cable": ("USB-C plug on a cable", "Not selected", "Soldered wires", "–", "5 A", "", 0.4000, EST, "–"),
    "fusb": ("FUSB302BMPX", "onsemi", "WQFN-14", "–", "–", "C132291", 0.4080, LCSC, "1,000"),
    "buf": ("74AUP1G126GW-TP", "Tech Public", "SOT-353", "–", "–", "C51886129", 0.0304, LCSC, "3,000"),
    "and": ("SN74AUP1G08DCKR", "UMW", "SC-70-5", "–", "–", "C7394036", 0.0240, LCSC, "3,000"),
    "fcmp": ("TP1942-SR", "3PEAK", "SOIC-8", "68 ns", "–", "C248572", 0.1742, LCSC, "2,500"),
    "scmp": ("LM393DR2G", "onsemi", "SOIC-8", "1.3 µs", "–", "C7955", 0.0323, LCSC, "2,500"),
    "bav": ("BAV99", "R+O", "SOT-23", "–", "70 V", "C7420336", 0.0080, LCSC, "3,000"),
    "r4k7": ("0402WGF4701TCE", "Uni-Royal", "0402", "4.7 kΩ", "–", "C25900", 0.0013, LCSC, "1,000"),
    "r10k": ("0402WGF1002TCE", "Uni-Royal", "0402", "10 kΩ", "–", "C25744", 0.0011, LCSC, "1,000"),
    "r75": ("0402WGF750JTCE", "Uni-Royal", "0402", "75 Ω", "–", "C25133", 0.0010, LCSC, "1,000"),
    "r1k": ("0402WGF1001TCE", "Uni-Royal", "0402", "1 kΩ", "–", "C11702", 0.0011, LCSC, "1,000"),
    "r12k": ("0402WGF1202TCE", "Uni-Royal", "0402", "12 kΩ", "–", "C25752", 0.0010, LCSC, "1,000"),
    "r7k5": ("0402WGF7501TCE", "Uni-Royal", "0402", "7.5 kΩ", "–", "C25918", 0.0017, LCSC, "1,000"),
    "r47": ("0402WGF470JTCE", "Uni-Royal", "0402", "47 Ω", "–", "C25118", 0.0009, LCSC, "1,000"),
    "r18k": ("0402WGF1802TCE", "Uni-Royal", "0402", "18 kΩ", "–", "C25762", 0.0011, LCSC, "1,000"),
    "r2k": ("0402WGF2001TCE", "Uni-Royal", "0402", "2 kΩ", "–", "C4109", 0.0015, LCSC, "1,000"),
    "r2k49": ("RC0402FR-072K49L", "Yageo", "0402", "2.49 kΩ", "–", "C145071", 0.0016, LCSC, "1,000"),
    "r24k9": ("Not selected", "Not selected", "1206", "24.9 kΩ", "–", "", 0.0030, EST, "–"),
    "rgen": ("Not selected", "Not selected", "0402", "Set at schematic", "–", "", 0.0011, EST, "–"),
    "cgen": ("Not selected", "Not selected", "0402", "Set at schematic", "–", "", 0.0020, EST, "–"),
    "csig": ("Not selected", "Not selected", "0805", "100 nF", "100 V", "", 0.0100, EST, "–"),
    "c100n": ("CL05B104KO5NNNC", "Samsung", "0402", "100 nF", "16 V", "C1525", 0.0018, LCSC, "1,000"),
    "c100n50": ("CL05B104KB54PNC", "Samsung", "0402", "100 nF", "50 V", "C307331", 0.0064, LCSC, "1,000"),
    "c1u": ("CL05A105KA5NQNC", "Samsung", "0402", "1 µF", "25 V", "C52923", 0.0042, LCSC, "1,000"),
    "c10u": ("CL10A106KP8NNNC", "Samsung", "0603", "10 µF", "10 V", "C19702", 0.0107, LCSC, "4,000"),
    "c18p": ("0402CG180J500NT", "FH", "0402", "18 pF", "50 V", "C1549", 0.0014, LCSC, "1,000"),
    "c1n2kv": ("1206B102K202NT", "FH", "1206", "1 nF", "2 kV", "C9196", 0.0105, LCSC, "3,000"),
}

# Parts whose catalogue number is a JLCPCB number with no LCSC product page.
JLC_ONLY = {"C17700185", "C193025", "C50543"}

ETH, SW, POE, B5, B33, USB, CCC, CCB, CCM = (
    "Ethernet", "Switch", "PoE front end", "5 V converter", "3.3 V converter",
    "USB-C power", "CC interface: PD transceiver", "CC interface: GPIO bit-bang", "CC interface: port 9 MAC")
BLOCKS = (ETH, SW, POE, B5, B33, USB, CCC, CCB, CCM)
ANCHOR = {ETH: "block-ethernet", SW: "block-switch", POE: "block-poe", B5: "block-5v", B33: "block-3v3",
          USB: "block-usb", CCC: "block-cc-transceiver", CCB: "block-cc-bit-bang", CCM: "block-cc-mac"}
BASE, CHIP, BANG, MAC = "Always", "PD transceiver", "GPIO bit-bang", "Port 9 MAC"
BUILD_BLOCK = {CHIP: CCC, BANG: CCB, MAC: CCM}

# (block, function, part id, quantity in option A, quantity in option B, build)
ROWS = [
    (ETH, "RJ45 jack", "rj45", 2, 3, BASE),
    (ETH, "LAN transformer", "xfmr", 2, 3, BASE),
    (ETH, "Line termination resistor", "r75", 8, 12, BASE),
    (ETH, "Line termination capacitor", "c1n2kv", 5, 6, BASE),
    (ETH, "Chip-side centre-tap capacitor", "c100n", 8, 12, BASE),
    (SW, "Switch IC with CPU", "sw", 1, 1, BASE),
    (SW, "Crystal", "xtal", 1, 1, BASE),
    (SW, "Crystal load capacitor", "c18p", 2, 2, BASE),
    (SW, "Firmware flash", "flash", 1, 1, BASE),
    (SW, "Bias resistor", "r2k49", 1, 1, BASE),
    (SW, "Flash chip-select pull-up", "r10k", 1, 1, BASE),
    (SW, "Supply pin capacitor", "c100n", 30, 30, BASE),
    (SW, "Supply bulk capacitor", "c10u", 4, 4, BASE),
    (SW, "Analogue supply bead", "bead", 2, 2, BASE),
    (SW, "Core regulator inductor", "l2u2", 1, 1, BASE),
    (SW, "Core regulator capacitor", "c10u", 2, 2, BASE),
    (SW, "Strap resistor", "r4k7", 6, 6, BASE),
    (SW, "Reset resistor", "r10k", 1, 1, BASE),
    (SW, "Reset capacitor", "c1u", 1, 1, BASE),
    (POE, "Polarity bridge", "bridge", 2, 2, BASE),
    (POE, "Surge clamp", "tvs", 1, 1, BASE),
    (POE, "Signature resistor", "r24k9", 1, 1, BASE),
    (POE, "Signature capacitor", "csig", 1, 1, BASE),
    (POE, "Class sink transistor", "npn", 2, 2, BASE),
    (POE, "Class sink window zener", "zener", 1, 1, BASE),
    (POE, "Class sink resistor", "rgen", 3, 3, BASE),
    (POE, "Hot-swap MOSFET", "hsfet", 1, 1, BASE),
    (POE, "Gate clamp zener", "zgate", 1, 1, BASE),
    (POE, "Turn-on threshold resistor", "rgen", 2, 2, BASE),
    (POE, "Gate capacitor", "c100n50", 1, 1, BASE),
    (B5, "Converter IC", "buck5", 1, 1, BASE),
    (B5, "Catch diode", "diode", 1, 1, BASE),
    (B5, "Inductor", "l10", 1, 1, BASE),
    (B5, "Input bulk capacitor", "elec", 1, 1, BASE),
    (B5, "Input capacitor", "c2u2hv", 2, 2, BASE),
    (B5, "Output capacitor", "c22u", 2, 2, BASE),
    (B5, "Bootstrap capacitor", "c100n", 1, 1, BASE),
    (B5, "Feedback resistor", "rgen", 2, 2, BASE),
    (B5, "Frequency resistor", "rgen", 1, 1, BASE),
    (B5, "Compensation resistor", "rgen", 1, 1, BASE),
    (B5, "Compensation capacitor", "cgen", 2, 2, BASE),
    (B33, "Converter IC", "buck33", 1, 1, BASE),
    (B33, "Inductor", "l4u7", 1, 1, BASE),
    (B33, "Feedback top resistor", "r18k", 1, 1, BASE),
    (B33, "Feedback bottom resistor", "r2k", 2, 2, BASE),
    (B33, "Input capacitor", "c10u", 1, 1, BASE),
    (B33, "Output capacitor", "c10u", 2, 2, BASE),
    (B33, "Bootstrap capacitor", "c100n", 1, 1, BASE),
    (USB, "VBUS switch MOSFET", "pfet", 1, 2, BASE),
    (USB, "VBUS switch driver", "dtc", 1, 2, BASE),
    (USB, "VBUS gate pull-up", "r10k", 1, 2, BASE),
    (USB, "VBUS bleed resistor", "r1k", 1, 2, BASE),
    (USB, "VBUS capacitor", "c1u", 1, 2, BASE),
    (USB, "Captive cable", "cable", 1, 2, BASE),
    (CCC, "PD transceiver", "fusb", 1, 2, CHIP),
    (CCC, "I²C pull-up", "r4k7", 2, 4, CHIP),
    (CCC, "Supply pin capacitor", "c100n", 1, 2, CHIP),
    (CCC, "Flash pin group strap", "r4k7", 0, 1, CHIP),
    (CCB, "BMC driver buffer", "buf", 1, 2, BANG),
    (CCB, "Receiver capacitor", "cgen", 1, 2, BANG),
    (CCB, "Driver series resistor", "r47", 1, 2, BANG),
    (CCB, "Fast dual comparator", "fcmp", 1, 2, BANG),
    (CCB, "Threshold divider resistor", "rgen", 4, 8, BANG),
    (CCB, "CC series resistor", "r1k", 1, 2, BANG),
    (CCB, "CC clamp diode", "bav", 1, 2, BANG),
    (CCB, "Rp for 1.5 A", "r12k", 1, 2, BANG),
    (CCB, "Rp step to 3 A", "r7k5", 1, 2, BANG),
    (CCB, "Slow dual comparator", "scmp", 1, 1, BANG),
    (CCB, "VBUS threshold resistor", "rgen", 2, 4, BANG),
    (CCB, "Comparator output pull-up", "r10k", 1, 2, BANG),
    (CCB, "Buffer enable pull-down", "r10k", 1, 2, BANG),
    (CCB, "Supply pin capacitor", "c100n", 3, 5, BANG),
    (CCM, "BMC driver buffer", "buf", 1, 0, MAC),
    (CCM, "Buffer reset gate", "and", 1, 0, MAC),
    (CCM, "Receiver capacitor", "cgen", 1, 0, MAC),
    (CCM, "Driver series resistor", "r47", 1, 0, MAC),
    (CCM, "Fast dual comparator", "fcmp", 1, 0, MAC),
    (CCM, "Threshold divider resistor", "rgen", 4, 0, MAC),
    (CCM, "CC series resistor", "r1k", 1, 0, MAC),
    (CCM, "CC clamp diode", "bav", 1, 0, MAC),
    (CCM, "Rp for 1.5 A", "r12k", 1, 0, MAC),
    (CCM, "Rp step to 3 A", "r7k5", 1, 0, MAC),
    (CCM, "Slow dual comparator", "scmp", 1, 0, MAC),
    (CCM, "VBUS threshold resistor", "rgen", 2, 0, MAC),
    (CCM, "Comparator output pull-up", "r10k", 1, 0, MAC),
    (CCM, "Receive tie resistor", "r4k7", 3, 0, MAC),
    (CCM, "Clock strap resistor", "r4k7", 1, 0, MAC),
    (CCM, "Gate pull-down", "r10k", 1, 0, MAC),
    (CCM, "Supply pin capacitor", "c100n", 4, 0, MAC),
]

# Estimates that are not parts of the bill of materials.
PCB_USD = {"a": 0.40, "b": 0.50}
ASSEMBLY_USD = {"a": 1.10, "b": 1.30}


def number_link(num):
    if not num:
        return "–"
    if num in JLC_ONLY:
        return "[%s](https://jlcpcb.com/partdetail/%s)" % (num, num)
    return "[%s](https://www.lcsc.com/product-detail/%s.html)" % (num, num)


def rows_of(option, builds):
    col = 3 if option == "a" else 4
    return [r for r in ROWS if r[col] and r[5] in builds]


def summary(option, builds):
    rows = rows_of(option, builds)
    col = 3 if option == "a" else 4
    cost = sum(r[col] * PARTS[r[2]][6] for r in rows)
    placements = sum(r[col] for r in rows)
    items = len({r[2] for r in rows})
    return cost, placements, items


def bom_table(option, builds):
    col = 3 if option == "a" else 4
    out = ["| Block | Function | Part | Maker | Package | Value | Rating | Catalogue number | Quantity | Unit price | "
           "Price source | Price tier | Line cost |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | ---: | ---: | --- | ---: | ---: |"]
    for block, function, pid, *_ in rows_of(option, builds):
        part, maker, package, value, rating, num, price, basis, tier = PARTS[pid]
        qty = dict(a=_[0], b=_[1])[option]
        out.append("| [%s](#%s) | %s | %s | %s | %s | %s | %s | %s | %d | $%.4f | %s | %s | $%.4f |"
                   % (block, ANCHOR[block], function, part, maker, package, value, rating, number_link(num), qty, price,
                      basis, tier, qty * price))
    return "\n".join(out)


def block_table():
    out = ["| Block | Option A cost | Option A placements | Option B cost | Option B placements |",
           "| --- | ---: | ---: | ---: | ---: |"]
    for block in BLOCKS:
        cells = []
        for option, col in (("a", 3), ("b", 4)):
            rows = [r for r in ROWS if r[0] == block and r[col]]
            if rows:
                cells.append("$%.2f | %d" % (sum(r[col] * PARTS[r[2]][6] for r in rows), sum(r[col] for r in rows)))
            else:
                cells.append("– | –")
        out.append("| [%s](#%s) | %s |" % (block, ANCHOR[block], " | ".join(cells)))
    return "\n".join(out)


def totals_table():
    out = ["| Option | CC interface | Parts cost | Placements | Line items | PCB estimate | Assembly estimate | Total |",
           "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for option, name in (("a", "[A](#option-a)"), ("b", "[B](#option-b)")):
        for build in (CHIP, BANG, MAC):
            label = "[%s](#%s)" % (build, ANCHOR[BUILD_BLOCK[build]])
            if not rows_of(option, (build,)):
                out.append("| %s | %s | – | – | – | – | – | – |" % (name, label))
                continue
            cost, placements, items = summary(option, (BASE, build))
            out.append("| %s | %s | $%.2f | %d | %d | $%.2f | $%.2f | $%.2f |"
                       % (name, label, cost, placements, items, PCB_USD[option], ASSEMBLY_USD[option],
                          cost + PCB_USD[option] + ASSEMBLY_USD[option]))
    return "\n".join(out)


def write_csv(option):
    col = 3 if option == "a" else 4
    path = HERE / ("bom-option-%s.csv" % option)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["block", "function", "part", "maker", "package", "value", "rating", "catalogue_number", "quantity",
                    "unit_usd", "price_source", "price_tier", "line_usd", "build"])
        for r in ROWS:
            if not r[col]:
                continue
            part, maker, package, value, rating, num, price, basis, tier = PARTS[r[2]]
            w.writerow([r[0], r[1], part, maker, package, value, rating, num, r[col], "%.4f" % price, basis, tier,
                        "%.4f" % (r[col] * price), r[5]])


def main():
    blocks = {"totals": totals_table(), "blocks": block_table()}
    for option in "ab":
        blocks["bom-%s-base" % option] = bom_table(option, (BASE,))
        for build, key in ((CHIP, "transceiver"), (BANG, "bit-bang"), (MAC, "mac")):
            if rows_of(option, (build,)):
                blocks["bom-%s-%s" % (option, key)] = bom_table(option, (build,))
    text = NOTE.read_text(encoding="utf-8")
    for name, table in blocks.items():
        pattern = r"(<!-- BEGIN %s -->\n).*?(<!-- END %s -->)" % (name, name)
        text, n = re.subn(pattern, lambda m: m.group(1) + table + "\n" + m.group(2), text, flags=re.S)
        if n != 1:
            raise SystemExit("marker %s found %d times" % (name, n))
    NOTE.write_text(text, encoding="utf-8")
    write_csv("a")
    write_csv("b")
    print(totals_table())
    print(block_table())


if __name__ == "__main__":
    main()
