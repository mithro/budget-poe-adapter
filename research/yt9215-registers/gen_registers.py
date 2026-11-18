#!/usr/bin/env python3
"""Generate the YT921x register map documents.

Inputs are a checkout of the Linux yt921x DSA driver directory
(drivers/net/dsa/motorcomm plus net/dsa/tag_yt921x.c copied alongside) and a
checkout of the Motorcomm vendor switch SDK.

  gen_registers.py --linux DIR --linux-sha SHA --sdk DIR --sdk-sha SHA

Outputs, written next to this script:
  linux-driver-registers.md   registers, fields and values from the Linux driver
  vendor-sdk-registers.md     every table in the vendor SDK table list
  registers.csv, fields.csv, values.csv, vendor-sdk-registers.csv,
  vendor-sdk-fields.csv       the same data as CSV
"""
import argparse
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HEADERS = ["chip.h", "mdio_bus.h", "mib.h", "leds.h", "tc.h"]

# (block title, anchor text, list of register-name regexes)
BLOCKS = [
    ("Global and chip identification", [
        r"RST$", r"FUNC$", r"CHIP_ID$", r"CHIP_MODE$", r"SYS_CLK$",
        r"IO_LEVEL$", r"MAC_ADDR_", r"PON_STRAP_", r"SENSOR$", r"TEMP$",
        r"EDATA_"]),
    ("CPU port and tagging", [r"EXT_CPU_PORT$", r"CPU_TAG_TPID$", r"CPU_COPY$"]),
    ("Port, MAC and external interface control", [
        r"PORTn_CTRL$", r"PORTn_STATUS$", r"MACn_FRAME$", r"SERDES_CTRL$",
        r"SERDESn$", r"XMII_CTRL$", r"XMIIn$", r"MDIO_POLLINGn$"]),
    ("MDIO master buses (PHY access)", [r"_MBUS_"]),
    ("EEE", [r"EEE"]),
    ("MIB counters", [r"MIB"]),
    ("LEDs", [r"LED"]),
    ("VLAN", [
        r"PVID_SEL$", r"PORTn_EGR$", r"TPID_EGRn$", r"TPID_IGRn$",
        r"PORTn_IGR_TPID$", r"VLAN"]),
    ("QoS priority mapping", [r"IPM_", r"PORTn_QOS$", r"PORTn_PRIO_ORD$"]),
    ("Spanning tree, isolation and learning", [
        r"PORTn_ISOLATION$", r"STPn$", r"PORTn_LEARN$", r"AGEING$"]),
    ("FDB (address table)", [r"FDB_"]),
    ("Flooding and unknown-destination handling", [r"FILTER_", r"ACT_UNK_"]),
    ("Link aggregation", [r"LAG_"]),
    ("ACL", [r"ACL", r"UDFn_CTRL$"]),
    ("Meters and ingress policing", [r"PORTn_RATE$", r"METER"]),
    ("Egress shaping", [r"SHAPE"]),
    ("Mirroring", [r"MIRROR$"]),
]

ACL_KEY_TYPES = ["MAC_xA0", "MAC_DA1_SA1", "VLAN", "VTAG", "IPV4", "IPV6_xA1",
                 "IPV6_xA2", "IPV6_xA3", "IPV6", "MISC", "L4", "UDF",
                 "ETHERTYPE"]

DEF_RE = re.compile(r"^#define( +)(\w+)(\([^)]*\))?\s+(.*?)\s*(?:/\*\s*(.*?)\s*\*/)?\s*$")


def cint(s):
    return int(s, 0)


def strip_parens(expr):
    """(port) -> port, tidy spacing."""
    prev = None
    while prev != expr:
        prev = expr
        expr = re.sub(r"\((\w+)\)", r"\1", expr)
    return expr.strip()


def parse_bits(body):
    """Return (kind, hi, lo, text). kind is 'const' or 'expr' or None."""
    m = re.fullmatch(r"BIT\((\d+)\)", body)
    if m:
        n = int(m.group(1))
        return "const", n, n, str(n)
    m = re.fullmatch(r"GENMASK(?:_ULL)?\((\d+), (\d+)\)", body)
    if m:
        hi, lo = int(m.group(1)), int(m.group(2))
        return "const", hi, lo, f"{hi}:{lo}"
    m = re.fullmatch(r"BIT\((.+)\)", body)
    if m:
        return "expr", None, None, "`" + strip_parens(m.group(1)) + "`"
    m = re.fullmatch(r"GENMASK(?:_ULL)?\((.+), (.+)\)", body)
    if m:
        return ("expr", None, None,
                "`" + strip_parens(m.group(1)) + "` : `" + strip_parens(m.group(2)) + "`")
    m = re.fullmatch(r"\(7 << \((.+)\)\)", body)
    if m:
        lo = strip_parens(m.group(1))
        return "expr", None, None, f"`{lo} + 2` : `{lo}`"
    return None, None, None, None


def parse_addr(body):
    """Return (base, formula) for a register address macro body."""
    m = re.match(r"\(?(0x[0-9a-fA-F]+)", body)
    base = cint(m.group(1))
    formula = strip_parens(body)
    if formula.startswith("(") and formula.endswith(")"):
        formula = formula[1:-1]
    return base, formula


def word_of(name):
    """Word letters for multi-word registers, from the driver's naming."""
    m = re.search(r"_(?:CTRL|ACT|KEY|BIN)([abc]{1,2})_", name)
    if m:
        return m.group(1)
    return ""


def parse_linux(ldir):
    regs, fields, values, mibs, consts = [], [], [], [], []
    for hdr in HEADERS:
        cur_reg = None
        cur_field = None
        in_mib = False
        with open(os.path.join(ldir, hdr)) as f:
            lines = f.read().split("\n")
        for lineno, line in enumerate(lines, 1):
            m = DEF_RE.match(line)
            if not m:
                continue
            level = len(m.group(1))
            name, args, body, note = m.group(2), m.group(3) or "", m.group(4), m.group(5) or ""
            if name.startswith("_") or not body:
                continue
            src = (hdr, lineno)
            short = re.sub(r"^YT921[0-9X]_", "", name)
            if level == 1:
                in_mib = name == "YT921X_MIBn_DATAm"
                if re.match(r"\(?0x[0-9a-fA-F]{5,6}\b", body):
                    base, formula = parse_addr(body)
                    cur_reg = dict(name=short, cname=name, args=args, base=base,
                                   formula=formula if args else "", note=note,
                                   src=src)
                    regs.append(cur_reg)
                    cur_field = None
                elif in_mib:
                    pass
                else:
                    cur_reg = None
                    cur_field = None
                    if re.fullmatch(r"-?\d+|0x[0-9a-fA-F]+", body):
                        consts.append(dict(name=name, value=body, note=note, src=src))
                continue
            if level == 2 and in_mib:
                mibs.append(dict(name=short.replace("MIB_DATA_", ""), cname=name,
                                 offset=cint(body), src=src))
                continue
            if cur_reg is None:
                continue
            if level == 2:
                kind, hi, lo, text = parse_bits(body)
                if kind is None:
                    continue
                fname = re.sub(r"_M$", "", short)
                fname = re.sub(r"_M(\(.*\))$", r"\1", fname + args) if args else fname
                cur_field = dict(reg=cur_reg, name=fname, cname=name, kind=kind,
                                 hi=hi, lo=lo, bits=text, word=word_of(name),
                                 note=note, src=src,
                                 variant=(name[:6] if not name.startswith("YT921X") else ""))
                fields.append(cur_field)
                continue
            if level == 3 and cur_field is not None:
                if "FIELD_PREP" in body or re.search(r"\(x\) <<", body):
                    continue
                m2 = re.fullmatch(r"\w+\((?:\w+, )?(\d+|0x[0-9a-fA-F]+)\)", body)
                if m2:
                    val = m2.group(1)
                elif re.fullmatch(r"\d+|0x[0-9a-fA-F]+", body):
                    val = body
                else:
                    continue
                values.append(dict(field=cur_field, name=short + args, cname=name,
                                   value=val, note=note, src=src,
                                   variant=(name[:6] if not name.startswith("YT921X") else "")))
    # MIB counter sizes from mib.c
    sizes = {}
    with open(os.path.join(ldir, "mib.c")) as f:
        for line in f:
            m = re.search(r"MIB_DESC\((\d), (\w+),", line)
            if m:
                sizes[m.group(2)] = int(m.group(1))
    for mib in mibs:
        mib["words"] = sizes.get(mib["cname"], 1)
    return regs, fields, values, mibs, consts


def parse_sdk(sdir):
    tdir = os.path.join(sdir, "switch_sdk/core/fal/tiger")
    fieldsets = {}
    cur = None
    with open(os.path.join(tdir, "fal_tiger_struct.c")) as f:
        for lineno, line in enumerate(f, 1):
            m = re.match(r"const field_id_t (\w+)\[\]", line)
            if m:
                cur = m.group(1)
                fieldsets[cur] = dict(line=lineno, fields=[])
                continue
            m = re.match(r"\s*\{(\w+)f,(\d+),(\d+),(\d+)\}", line)
            if m and cur:
                fieldsets[cur]["fields"].append(dict(
                    cname=m.group(1), width=int(m.group(2)),
                    word=int(m.group(3)), bit=int(m.group(4)), line=lineno))
    tables = []
    with open(os.path.join(tdir, "fal_tiger_index.c")) as f:
        txt = f.read().split("\n")
    i = 0
    ent = {}
    for lineno, line in enumerate(txt, 1):
        m = re.search(r"/\* (Asic Base Address|offset|bytes|Entry Number|Fields_num|fields_id) \*/ (\w+),", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if key == "Asic Base Address":
            ent = dict(line=lineno, base=cint(val))
        elif key == "offset":
            ent["stride"] = cint(val)
        elif key == "bytes":
            ent["bytes"] = cint(val)
        elif key == "Entry Number":
            ent["entries"] = cint(val)
        elif key == "fields_id":
            fs = fieldsets[val]
            name = re.sub(r"m_field$", "", val).upper()
            ent["name"] = name
            ent["struct_line"] = fs["line"]
            flds = []
            for fl in fs["fields"]:
                fn = fl["cname"]
                if fn.upper().startswith(name + "_"):
                    fn = fn[len(name) + 1:]
                flds.append(dict(name=fn, width=fl["width"], word=fl["word"],
                                 bit=fl["bit"], line=fl["line"],
                                 lo=32 * fl["word"] + fl["bit"],
                                 hi=32 * fl["word"] + fl["bit"] + fl["width"] - 1))
            ent["fields"] = flds
            tables.append(ent)
    modules = []
    with open(os.path.join(tdir, "fal_tiger_mem.h")) as f:
        for line in f:
            m = re.match(r"\s*#define MODULE_(\w+)\s+(0x[0-9A-Fa-f]+)\s*$", line)
            if m and cint(m.group(2)) >= 0x10000:
                modules.append((cint(m.group(2)), m.group(1)))
    modules.sort()
    return tables, modules


def sdk_lookup(tables, addr):
    for t in tables:
        if t["base"] <= addr < t["base"] + t["stride"] * t["entries"]:
            return t
    return None


def sdk_literal(sdir, addr):
    """Name of an SDK source file that uses the address as a literal."""
    pat = re.compile(r"0x0*%x\b" % addr, re.I)
    hits = []
    for root, _, files in os.walk(os.path.join(sdir, "switch_sdk")):
        for fn in files:
            if fn.endswith((".c", ".h")):
                with open(os.path.join(root, fn), errors="replace") as f:
                    if pat.search(f.read()):
                        hits.append(fn)
    hits.sort(key=lambda n: (not n.endswith(".h"), n))
    return hits[0] if hits else ""


WORD_INDEX = {"a": 0, "b": 1, "c": 2, "ab": 0, "bc": 1}


def match_field(fld, tables):
    """Compare one driver field with the vendor SDK table.

    Returns (status, SDK field names, SDK field bits)."""
    reg = fld["reg"]
    t = sdk_lookup(tables, reg["base"])
    if t is None:
        return "no SDK table", "", ""
    if fld["kind"] != "const":
        return "per-index field", "", ""
    word0 = ((reg["base"] - t["base"]) % t["stride"]) // 4
    word0 += WORD_INDEX.get(fld["word"], 0)
    lo, hi = 32 * word0 + fld["lo"], 32 * word0 + fld["hi"]
    if not t["fields"]:
        return "SDK lists no fields", "", ""
    over = [f for f in t["fields"] if f["lo"] <= hi and f["hi"] >= lo]
    if not over:
        return "not in SDK", "", ""

    def bits(f):
        return f"{f['bit'] + f['width'] - 1}:{f['bit']}" if f["width"] > 1 else str(f["bit"])
    sbits = bits(over[0]) if len(over) == 1 else ""
    names = []
    for f in sorted(over, key=lambda f: f["lo"]):
        n = re.sub(r"_[0-9]$", "", f["name"]) if len(over) > 1 else f["name"]
        if n not in names:
            names.append(n)
    if min(f["lo"] for f in over) == lo and max(f["hi"] for f in over) == hi:
        if len(names) == 1:
            return "same bits", names[0], sbits
        return "spans SDK fields", " ".join(names), sbits
    if len(over) == 1 and over[0]["lo"] <= lo and over[0]["hi"] >= hi and fld["hi"] - fld["lo"] < 2:
        return "part of SDK field", names[0], sbits
    return "different bits", " ".join(names), sbits


def md_table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(c) if c != "" else " " for c in r) + " |")
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--linux", required=True)
    ap.add_argument("--linux-sha", required=True)
    ap.add_argument("--sdk", required=True)
    ap.add_argument("--sdk-sha", required=True)
    a = ap.parse_args()

    lurl = f"https://github.com/torvalds/linux/blob/{a.linux_sha}/drivers/net/dsa/motorcomm/"
    surl = (f"https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk/blob/{a.sdk_sha}/"
            "switch_sdk/core/fal/tiger/")

    def lsrc(src):
        return f"[{src[0]}:{src[1]}]({lurl}{src[0]}#L{src[1]})"

    regs, fields, values, mibs, consts = parse_linux(a.linux)
    tables, modules = parse_sdk(a.sdk)

    # assign blocks
    for r in regs:
        r["block"] = None
        for title, pats in BLOCKS:
            if any(re.search(p, r["name"]) for p in pats):
                r["block"] = title
                break
        if r["block"] is None:
            sys.exit(f"register {r['name']} has no block")
        t = sdk_lookup(tables, r["base"])
        r["sdk"] = t
        r["sdkfile"] = "" if t else sdk_literal(a.sdk, r["base"])
    for f in fields:
        f["status"], f["sdkname"], f["sdkbits"] = match_field(f, tables)

    acl_layout = [f for f in fields if re.match(r"YT921X_ACL_(BIN|KEY)[ab]_(?!ORD|SPORT|REVERSE|TYPE)", f["cname"])]
    acl_ids = {id(f) for f in acl_layout}

    # ---------------- linux-driver-registers.md ----------------
    o = []
    o.append("# YT921x registers defined by the Linux driver\n")
    o.append("This file is generated by [gen_registers.py](gen_registers.py) from the upstream Linux "
             "`yt921x` DSA driver. The overview, access method and cross-checks are in "
             "[README.md](README.md).\n")
    o.append("Every row links to the line of the driver header that defines it. Register names drop the "
             "`YT921X_` prefix. The \"SDK table\" and \"SDK field\" columns give the name of the entry "
             "at the same address and bits in the vendor SDK table list, which is listed in full in "
             "[vendor-sdk-registers.md](vendor-sdk-registers.md).\n")
    o.append("## Column meanings\n")
    o.append(md_table(["Column", "Meaning"], [
        ["Address", "Address of the register, or of its first instance when it is indexed"],
        ["Address formula", "Address expression from the driver for indexed registers"],
        ["SDK entries", "Number of instances the vendor SDK lists for the table"],
        ["SDK entry bytes", "Size of one instance in the vendor SDK"],
        ["Other SDK file", "SDK source file that uses the address as a literal when no SDK table has it"],
        ["Word", "32-bit word of a multi-word register that holds the field"],
        ["Bits", "Bit position inside that word, high bit first"],
        ["SDK check", "Result of comparing the field with the vendor SDK field list"],
    ]))
    o.append("Multi-word registers are named with a lower-case word letter in the driver. Word `a` is at "
             "the register address, word `b` is 4 bytes above it and word `c` is 8 bytes above it. A "
             "field marked `ab` or `bc` crosses a word boundary, and its bit numbers count from bit 0 of "
             "the first word named.\n")
    o.append("## SDK check values\n")
    o.append(md_table(["Value", "Meaning"], [
        ["same bits", "One SDK field covers exactly the same bits"],
        ["spans SDK fields", "Several adjacent SDK fields together cover exactly the same bits"],
        ["part of SDK field", "The driver names one or two bits inside a wider SDK field"],
        ["different bits", "An SDK field overlaps the bits but its boundaries differ"],
        ["SDK lists no fields", "The SDK lists the register with an empty field list"],
        ["not in SDK", "The SDK lists the register but no field at these bits"],
        ["no SDK table", "The address is not in the SDK table list"],
        ["per-index field", "The bit position depends on a port or group index and is not compared"],
    ]))

    o.append("## Blocks\n")
    rows = []
    for title, _ in BLOCKS:
        rs = [r for r in regs if r["block"] == title]
        anchor = re.sub(r"[^a-z0-9 -]", "", title.lower()).replace(" ", "-")
        rows.append([f"[{title}](#{anchor})", len(rs), f"0x{min(r['base'] for r in rs):06x}",
                     f"0x{max(r['base'] for r in rs):06x}"])
    o.append(md_table(["Block", "Registers", "Lowest address", "Highest base address"], rows))

    for title, _ in BLOCKS:
        rs = sorted([r for r in regs if r["block"] == title], key=lambda r: r["base"])
        o.append(f"## {title}\n")
        o.append("### Registers\n")
        rows = []
        for r in rs:
            t = r["sdk"]
            rows.append([f"`{r['name']}`", f"0x{r['base']:06x}",
                         f"`{r['formula']}`" if r["formula"] else "",
                         f"`{t['name']}`" if t else "",
                         t["entries"] if t else "", t["bytes"] if t else "",
                         f"`{r['sdkfile']}`" if r["sdkfile"] else "",
                         r["note"], lsrc(r["src"])])
        o.append(md_table(["Register", "Address", "Address formula", "SDK table", "SDK entries",
                           "SDK entry bytes", "Other SDK file", "Driver comment", "Source"], rows))
        fs = [f for f in fields if f["reg"]["block"] == title and id(f) not in acl_ids]
        if fs:
            o.append("### Fields\n")
            rows = []
            for f in fs:
                rows.append([f"`{f['reg']['name']}`", f"`{f['name']}`", f["word"], f["bits"],
                             f["variant"], f["status"],
                             f"`{f['sdkname']}`" if f["sdkname"] else "", f["sdkbits"],
                             f["note"], lsrc(f["src"])])
            o.append(md_table(["Register", "Field", "Word", "Bits", "Chip family", "SDK check",
                               "SDK field", "SDK bits", "Driver comment", "Source"], rows))
        vs = [v for v in values if v["field"]["reg"]["block"] == title and id(v["field"]) not in acl_ids]
        if vs:
            o.append("### Field values\n")
            rows = []
            for v in vs:
                rows.append([f"`{v['field']['name']}`", f"`{v['name']}`", v["value"],
                             v["variant"], v["note"], lsrc(v["src"])])
            o.append(md_table(["Field", "Value name", "Value", "Chip family", "Driver comment",
                               "Source"], rows))
        if title == "MIB counters":
            o.append("### Counter offsets\n")
            o.append("Each port has one counter page at `MIBn_DATA0(port)`. The offset is added to the "
                     "page address. A counter of 2 words is 64 bits wide and its second word is at the "
                     "next offset.\n")
            rows = [[f"`{m['name']}`", f"0x{m['offset']:02x}", m["words"], lsrc(m["src"])] for m in mibs]
            o.append(md_table(["Counter", "Offset", "Words", "Source"], rows))
        if title == "ACL":
            o.append("### Key and mask layouts\n")
            o.append("`ACLn_KEYm` and `ACLn_MASKm` hold two words per entry. Bits 8:4 of word `b` select "
                     "the key type, and the rest of the two words is laid out per key type as below. "
                     "Fields named `KEYb` exist only in the key register. Fields named `BINa` or `BINb` "
                     "exist in both the key and the mask register.\n")
            rows = []
            for f in acl_layout:
                m = re.match(r"YT921X_ACL_(BIN|KEY)([ab])_(.*)", f["cname"])
                rest = re.sub(r"_M$", "", m.group(3))
                kt = next(k for k in ACL_KEY_TYPES if rest.startswith(k + "_") or rest == k)
                rows.append([f"`{kt}`", f"`{rest[len(kt) + 1:]}`", m.group(1), m.group(2), f["bits"],
                             lsrc(f["src"])])
            o.append(md_table(["Key layout", "Field", "Register kind", "Word", "Bits", "Source"], rows))
    with open(os.path.join(HERE, "linux-driver-registers.md"), "w") as f:
        f.write("\n".join(o))

    # ---------------- vendor-sdk-registers.md ----------------
    def module_of(addr):
        if addr == 0:
            return ""
        name = ""
        for base, n in modules:
            if base <= addr:
                name = n
        return name

    drv_by_table = {}
    for r in regs:
        if r["sdk"]:
            drv_by_table.setdefault(r["sdk"]["name"], []).append(r["name"])

    o = []
    o.append("# YT9215 registers in the vendor SDK table list\n")
    o.append("This file is generated by [gen_registers.py](gen_registers.py) from the machine-generated "
             "register table list in the Motorcomm YT9215 switch SDK. The overview is in "
             "[README.md](README.md).\n")
    o.append("The SDK list carries addresses, sizes and field positions but no descriptions, so the "
             "names are the only statement of meaning. The module name is the SDK module whose base "
             "address is the nearest one at or below the table address. Tables listed at address "
             "0x000000 are the ACL key and mask layouts for each key type. The SDK gives them no "
             "register address, so they have no module.\n")
    o.append("## Tables\n")
    rows = []
    for t in tables:
        rows.append([f"`{t['name']}`", f"0x{t['base']:06x}", t["entries"], t["bytes"], t["stride"],
                     module_of(t["base"]),
                     " ".join(f"`{n}`" for n in drv_by_table.get(t["name"], [])),
                     f"[index:{t['line']}]({surl}fal_tiger_index.c#L{t['line']})"])
    o.append(md_table(["SDK table", "Address", "Entries", "Entry bytes", "Entry stride", "SDK module",
                       "Linux driver name", "Source"], rows))
    o.append("## Fields\n")
    o.append("Word 0 is at the entry address and each following word is 4 bytes higher. Bits are given "
             "inside the word, high bit first.\n")
    rows = []
    for t in tables:
        for fl in t["fields"]:
            hi = fl["bit"] + fl["width"] - 1
            bits = f"{hi}:{fl['bit']}" if fl["width"] > 1 else str(fl["bit"])
            rows.append([f"`{t['name']}`", f"`{fl['name']}`", fl["word"], bits, fl["width"],
                         f"[struct:{fl['line']}]({surl}fal_tiger_struct.c#L{fl['line']})"])
    o.append(md_table(["SDK table", "Field", "Word", "Bits", "Width", "Source"], rows))
    with open(os.path.join(HERE, "vendor-sdk-registers.md"), "w") as f:
        f.write("\n".join(o))

    # ---------------- CSV ----------------
    def wcsv(name, header, rows):
        with open(os.path.join(HERE, name), "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(header)
            w.writerows(rows)

    wcsv("registers.csv",
         ["block", "register", "address", "address_formula", "sdk_table", "sdk_entries",
          "sdk_entry_bytes", "other_sdk_file", "comment", "source_file", "source_line"],
         [[r["block"], r["name"], f"0x{r['base']:06x}", r["formula"],
           r["sdk"]["name"] if r["sdk"] else "", r["sdk"]["entries"] if r["sdk"] else "",
           r["sdk"]["bytes"] if r["sdk"] else "", r["sdkfile"], r["note"], r["src"][0],
           r["src"][1]]
          for r in sorted(regs, key=lambda r: r["base"])])
    wcsv("fields.csv",
         ["register", "address", "field", "word", "bits", "chip_family", "sdk_check", "sdk_field",
          "sdk_bits", "comment", "source_file", "source_line"],
         [[f["reg"]["name"], f"0x{f['reg']['base']:06x}", f["name"], f["word"],
           f["bits"].replace("`", ""), f["variant"], f["status"], f["sdkname"], f["sdkbits"],
           f["note"],
           f["src"][0], f["src"][1]] for f in fields])
    wcsv("values.csv",
         ["register", "field", "value_name", "value", "chip_family", "comment", "source_file",
          "source_line"],
         [[v["field"]["reg"]["name"], v["field"]["name"], v["name"], v["value"], v["variant"],
           v["note"], v["src"][0], v["src"][1]] for v in values])
    wcsv("vendor-sdk-registers.csv",
         ["table", "address", "entries", "entry_bytes", "entry_stride", "module", "source_line"],
         [[t["name"], f"0x{t['base']:06x}", t["entries"], t["bytes"], t["stride"],
           module_of(t["base"]), t["line"]] for t in tables])
    wcsv("vendor-sdk-fields.csv",
         ["table", "field", "word", "low_bit", "width", "source_line"],
         [[t["name"], fl["name"], fl["word"], fl["bit"], fl["width"], fl["line"]]
          for t in tables for fl in t["fields"]])

    # ---------------- summary for the README ----------------
    from collections import Counter
    print("registers", len(regs), "fields", len(fields), "values", len(values), "mibs", len(mibs))
    print("sdk tables", len(tables), "sdk fields", sum(len(t["fields"]) for t in tables))
    print("regs without sdk table:", [r["name"] for r in regs if not r["sdk"]])
    print(Counter(f["status"] for f in fields))
    for f in fields:
        if f["status"] in ("different bits", "not in SDK"):
            print(" ", f["status"], f["reg"]["name"], f["name"], f["word"], f["bits"], f["sdkname"],
                  f["sdkbits"], f["src"])
    print("no table and no literal:", [r["name"] for r in regs if not r["sdk"] and not r["sdkfile"]])
    used = {r["sdk"]["name"] for r in regs if r["sdk"]}
    print("sdk tables not in driver:", len(tables) - len(used))


if __name__ == "__main__":
    main()
