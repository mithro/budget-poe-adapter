#!/usr/bin/env python3
"""Bill of materials of the discrete PoE front end.

    python3 bom.py --fetch     read price, stock and datasheet link of every part from lcsc.com into bom.json
    python3 bom.py             rewrite the generated tables of README.md (between the HTML comment markers)
                               from parts.py, bom.json, datasheets.json and sim/results.md

Prices are the LCSC price for 1,000 pieces: the last price break at or below that quantity.
"""
import json
import re, os, sys, time, urllib.request
from parts import PARTS, R4, OTHER, BLOCKS

HERE = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(HERE, "bom.json")
API = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode="
QTY = 1000


def fetch():
    codes = sorted({v[4] for v in PARTS.values() if v[4]} | {v[1] for v in R4.values()} | {v[4] for v in OTHER.values()})
    out = {}
    for c in codes:
        req = urllib.request.Request(API + c, headers={"User-Agent": "Mozilla/5.0"})
        d = json.load(urllib.request.urlopen(req, timeout=40))["result"]
        out[c] = dict(part=d["productModel"], maker=d["brandNameEn"], package=d["encapStandard"], stock=d["stockNumber"],
                      datasheet=d.get("pdfUrl"), prices=[[p["ladder"], p["usdPrice"]] for p in d["productPriceList"]])
        time.sleep(0.3)
    json.dump(out, open(SNAP, "w"), indent=1, sort_keys=True)
    print("wrote", SNAP, len(out), "parts")


def price(snap, code, qty=QTY):
    best = snap[code]["prices"][0][1]
    for ladder, usd in snap[code]["prices"]:
        if ladder <= qty:
            best = usd
    return best


def link(code):
    return f"[{code}](https://www.lcsc.com/product-detail/{code}.html)"


def refkey(r):
    head = r.rstrip("0123456789")
    return head, int(r[len(head):])


def parts_of(block):
    return sorted((r for r, v in PARTS.items() if v[0] == block), key=refkey)


def block_cost(block, snap):
    """(number of parts, cost in USD) of one block; R4 is priced as its value for Class 4 with two-event detection."""
    refs = parts_of(block)
    return len(refs), sum(price(snap, PARTS[r][4] or R4["4T"][1]) for r in refs)


def datasheet(code, sheets, snap=None):
    f = sheets.get(code)
    if f:
        return f"[PDF](../../datasheets/components/{f})"
    return f"[LCSC]({snap[code]['datasheet']})" if snap else "–"


def bom_table(snap, sheets):
    out = ["| Reference | Block | Value | Rating | Package | Part | Maker | LCSC | Datasheet | Price (USD) |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for block, title in BLOCKS.items():
        for ref in parts_of(block):
            _, value, pkg, _, code = PARTS[ref]
            anchor = f'<a id="{ref.lower()}"></a>{ref}'
            if code is None:
                out.append(f"| {anchor} | [{title}](#{block}-block) | [Class table](#class-resistor-r4) | – | {pkg} | – | – | – | – | {price(snap, R4['4T'][1]):.4f} |")
                continue
            p = snap[code]
            words = value.split(" ")
            value, rating = " ".join(words[:2]), " ".join(words[2:]) or "–"
            out.append(f"| {anchor} | [{title}](#{block}-block) | {value} | {rating} | {pkg} | {p['part']} | {p['maker']} | {link(code)} | "
                       f"{datasheet(code, sheets, snap)} | {price(snap, code):.4f} |")
    return "\n".join(out)


def r4_table(snap, sheets):
    names = {"1": "Class 1", "2": "Class 2", "3": "Class 3", "4": "Class 4", "4T": "Class 4 with the mark latch and two-event detector"}
    out = ["| Variant | R4 (Ω) | Part | Maker | LCSC | Datasheet | Price (USD) |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for k, (ohm, code) in R4.items():
        p = snap[code]
        out.append(f"| {names[k]} | {ohm:g} | {p['part']} | {p['maker']} | {link(code)} | {datasheet(code, sheets, snap)} | {price(snap, code):.4f} |")
    return "\n".join(out)


def cost_table(snap):
    out = ["| Block | Parts | Cost (USD) |", "| --- | --- | --- |"]
    for block, title in BLOCKS.items():
        n, c = block_cost(block, snap)
        out.append(f"| [{title}](#{block}-block) | {n} | {c:.3f} |")
    return "\n".join(out)


VARIANTS = [
    ("Class 0", ("input", "hotswap")),
    ("fixed class with a class sink", ("input", "hotswap", "class")),
    ("Class 4 with two-event detection", ("input", "hotswap", "class", "mark", "twoevent")),
]


def ic_variant(snap):
    """Input block, the TMI7303B, its class resistor and the pull-up of its T2P output."""
    n, c = block_cost("input", snap)
    return n + 3, c + price(snap, OTHER["TMI7303B"][4]) + price(snap, R4["4"][1]) + price(snap, "C25803")


def variant_table(snap):
    out = ["| Variant | Parts | Cost (USD) |", "| --- | --- | --- |"]
    for name, blocks in VARIANTS:
        n = sum(block_cost(b, snap)[0] for b in blocks)
        c = sum(block_cost(b, snap)[1] for b in blocks)
        out.append(f"| Discrete: {name} | {n} | {c:.2f} |")
    n, c = ic_variant(snap)
    out.append(f"| PD controller IC: [TMI7303B](#tmi7303b) with two-event detection | {n} | {c:.2f} |")
    return "\n".join(out)


def other_table(snap, sheets):
    out = ["| Part | Role | Package | Maker | LCSC | Datasheet | Price (USD) | Price quantity |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for key, (role, value, pkg, part, code) in OTHER.items():
        p = snap[code]
        q = max((l for l, _ in p["prices"] if l <= QTY), default=p["prices"][0][0])
        out.append(f'| <a id="{key.lower()}"></a>{p["part"]} | {value} | {pkg} | {p["maker"]} | {link(code)} | {datasheet(code, sheets, snap)} | {price(snap, code):.4f} | {q} |')
    return "\n".join(out)


SKIP = re.compile(r"(!?\[[^\]]*\]\([^)]*\)|<a id=[^>]*></a>\w*|`[^`]*`)")
REF = re.compile(r"\b(?:BR|R|C|D|Q|U)\d+\b(?![.-]\d)")


def autolink(text):
    """Link every reference designator in the prose to its row of the part tables."""
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', text))
    out, generated, code = [], False, False
    for line in text.split("\n"):
        if line.startswith("```"):
            code = not code
        if re.match(r"<!-- (bom|r4|other):begin", line):
            generated = True
        elif re.match(r"<!-- (bom|r4|other):end", line):
            generated = False
        if generated or code or line.startswith(("#", "![")):
            out.append(line)
            continue
        bits = SKIP.split(line)
        for i in range(0, len(bits), 2):
            bits[i] = REF.sub(lambda m: "[%s](#%s)" % (m.group(0), m.group(0).lower())
                              if m.group(0).lower() in anchors else m.group(0), bits[i])
        out.append("".join(bits))
    return "\n".join(out)


def write(readme):
    snap = json.load(open(SNAP))
    sheets = json.load(open(os.path.join(HERE, "datasheets.json")))
    text = open(readme, encoding="utf-8").read()
    parts = {"bom": bom_table(snap, sheets), "r4": r4_table(snap, sheets), "cost": cost_table(snap),
             "variants": variant_table(snap), "other": other_table(snap, sheets),
             "results": None}
    res = open(os.path.join(HERE, "sim", "results.md"), encoding="utf-8").read().strip().split("\n\n")
    res = [t for t in res if t.startswith("|")]
    for i, t in enumerate(res):
        parts["results%d" % (i + 1)] = t
    del parts["results"]
    for key, body in parts.items():
        a, b = f"<!-- {key}:begin -->", f"<!-- {key}:end -->"
        if a not in text:
            raise SystemExit("marker missing: " + a)
        text = text[:text.index(a) + len(a)] + "\n" + body + "\n" + text[text.index(b):]
    open(readme, "w", encoding="utf-8").write(autolink(text))


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch()
    else:
        write(os.path.join(HERE, "README.md"))
