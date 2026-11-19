#!/usr/bin/env python3
"""Build yt921x.yaml, the single machine-readable description of the YT921x
register map.

Machine facts (addresses, bit positions, enumerated values, source lines) are
read from a checkout of the Linux yt921x DSA driver and of the Motorcomm vendor
switch SDK.  Everything a person wrote (titles, descriptions, access types,
index ranges, block assignment) comes from overlay.yaml next to this script.

  extract.py --linux DIR --linux-sha SHA --sdk DIR --sdk-sha SHA

DIR for --linux holds the files of drivers/net/dsa/motorcomm plus
net/dsa/tag_yt921x.c in one flat directory.

Outputs, written one directory up:
  yt921x.yaml        registers, fields, values, counters, constants
  sdk-tables.yaml    every table of the vendor SDK table list
"""
import argparse
import itertools
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
HEADERS = ["chip.h", "mdio_bus.h", "mib.h", "leds.h", "tc.h"]
LINUX_PATHS = {
    "chip.h": "drivers/net/dsa/motorcomm/chip.h",
    "chip.c": "drivers/net/dsa/motorcomm/chip.c",
    "mdio_bus.h": "drivers/net/dsa/motorcomm/mdio_bus.h",
    "mdio_bus.c": "drivers/net/dsa/motorcomm/mdio_bus.c",
    "mib.h": "drivers/net/dsa/motorcomm/mib.h",
    "mib.c": "drivers/net/dsa/motorcomm/mib.c",
    "leds.h": "drivers/net/dsa/motorcomm/leds.h",
    "leds.c": "drivers/net/dsa/motorcomm/leds.c",
    "tc.h": "drivers/net/dsa/motorcomm/tc.h",
    "tc.c": "drivers/net/dsa/motorcomm/tc.c",
    "smi.c": "drivers/net/dsa/motorcomm/smi.c",
    "smi.h": "drivers/net/dsa/motorcomm/smi.h",
    "pcs-921x.c": "drivers/net/dsa/motorcomm/pcs-921x.c",
    "tag_yt921x.c": "net/dsa/tag_yt921x.c",
}

DEF_RE = re.compile(
    r"^#define( +)(\w+)(\([^)]*\))?\s+(.*?)\s*(?:/\*\s*(.*?)\s*\*/)?\s*$")
WORD_LETTER = {"a": 0, "b": 1, "c": 2, "ab": 0, "bc": 1}

# ACL key layouts, longest name first so that prefixes match correctly.
ACL_LAYOUTS = ["MAC_DA1_SA1", "MAC_xA0", "IPV6_xA1", "IPV6_xA2", "IPV6_xA3",
               "ETHERTYPE", "IPV4", "IPV6", "VLAN", "VTAG", "MISC", "L4", "UDF"]


class Hex(int):
    """An int that is written to YAML in hexadecimal."""


yaml.SafeDumper.ignore_aliases = lambda self, data: True

yaml.SafeDumper.add_representer(
    Hex, lambda d, v: d.represent_scalar("tag:yaml.org,2002:int", "0x%x" % v))


class Flow(list):
    """A list that is written to YAML in flow style."""


yaml.SafeDumper.add_representer(
    Flow, lambda d, v: d.represent_sequence("tag:yaml.org,2002:seq", v,
                                            flow_style=True))


# --------------------------------------------------------------------------
# C macro evaluation

def ctz(x):
    return (x & -x).bit_length() - 1


class Macros(dict):
    """Macro table that evaluates the driver's C macro bodies as Python."""

    def __init__(self):
        super().__init__()
        self.defs = {}
        self.base = {
            "BIT": lambda n: 1 << n,
            "GENMASK": lambda h, l: ((1 << (h + 1)) - 1) & ~((1 << l) - 1),
            "GENMASK_ULL": lambda h, l: ((1 << (h + 1)) - 1) & ~((1 << l) - 1),
            "FIELD_PREP": lambda m, x: (x << ctz(m)) & m,
        }

    def define(self, name, params, body):
        self.defs[name] = (params, body.replace("/", "//"))

    def __missing__(self, key):
        if key in self.base:
            return self.base[key]
        if key not in self.defs:
            raise KeyError(key)
        params, body = self.defs[key]
        if params is None:
            return eval(body, {"__builtins__": {}}, self)

        def call(*args):
            env = Scope(self, dict(zip(params, args)))
            return eval(body, {"__builtins__": {}}, env)
        return call


class Scope(dict):
    def __init__(self, parent, local):
        super().__init__(local)
        self.parent = parent

    def __missing__(self, key):
        return self.parent[key]


def mask_bits(mask):
    """(lsb, width) of a contiguous mask."""
    lsb = ctz(mask)
    width = (mask >> lsb).bit_length()
    assert mask == ((1 << width) - 1) << lsb, hex(mask)
    return lsb, width


# --------------------------------------------------------------------------
# Linux driver

def reg_id(short):
    """PORTn_CTRL -> PORT_CTRL, LAG_MEMBERnm -> LAG_MEMBER, MIBn_DATA0 -> MIB_DATA."""
    s = re.sub(r"(?<=[A-Z0-9])(nm|n|m)(?=_|$)", "", short)
    return {"MIB_DATA0": "MIB_DATA"}.get(s, s)


def norm(name):
    """Drop the index letters of the driver's macro names: BLOCKn -> BLOCK."""
    return re.sub(r"(?<=[A-Z0-9])(nm|n|m)(?=_|$)", "", name)


def ident(name):
    """Value names must be identifiers in every output: 1000BASEX -> V1000BASEX."""
    return "V" + name if name[0].isdigit() else name


def common_prefix_strip(name, ref):
    a, b = name.split("_"), ref.split("_")
    i = 0
    while i < len(a) - 1 and i < len(b) and a[i] == b[i]:
        i += 1
    return "_".join(a[i:])


def field_name(short, rid, prefix):
    """Field name inside its register, and the word letter if it has one."""
    for p in ([prefix] if prefix else []) + [rid]:
        m = re.match(r"%s(ab|bc|a|b|c)?_(.+)$" % re.escape(p), short)
        if m:
            return m.group(2), m.group(1) or ""
    toks = rid.split("_")
    cands = ["_".join(toks[:k]) for k in range(len(toks) - 1, 0, -1)]
    cands += ["_".join(toks[k:]) for k in range(1, len(toks))]
    for p in cands:
        if short.startswith(p + "_"):
            return short[len(p) + 1:], ""
    return short, ""


def parse_enums(text, hdr):
    out = {}
    for m in re.finditer(r"enum (yt921x_\w+) \{(.*?)\};", text, re.S):
        name = m.group(1)[len("yt921x_"):]
        line0 = text[:m.start()].count("\n") + 1
        members, val = [], 0
        body = re.sub(r"/\*.*?\*/", lambda c: "\n" * c.group(0).count("\n"),
                      m.group(2), flags=re.S)
        for off, ln in enumerate(body.split("\n")):
            mm = re.match(r"\s*(YT921X_\w+)(?:\s*=\s*(\w+))?,?\s*$", ln)
            if not mm:
                continue
            if mm.group(2):
                val = int(mm.group(2), 0)
            members.append(dict(cname=mm.group(1), value=val,
                                src=[hdr, line0 + off]))
            val += 1
        # strip the common prefix of the member names
        toks = [x["cname"].split("_") for x in members]
        k = 0
        while all(len(t) > k + 1 for t in toks) and len({t[k] for t in toks}) == 1:
            k += 1
        for x, t in zip(members, toks):
            x["name"] = "_".join(t[k:])
        members = [x for x in members if x["name"] not in ("NUM", "INVALID")
                   or name == "fdb_entry_status"]
        out[name] = dict(members=members, src=[hdr, line0])
    return out


FUNCS = {}
USES = {}


def enum_linux(member):
    lx = dict(macro=member["cname"], src=member["src"])
    lx["used"] = first_use(lx, ())
    return lx


def first_use(lx, funcs, *more):
    """Record where the driver first uses an item, trying its macro and then the others.

    A use inside one of ``funcs`` (the functions that touch the register of a field) is
    preferred, because a macro can be shared by the fields of several registers.
    """
    names = [lx["macro"].split("(")[0]]
    names.append(re.sub(r"_M$", "", names[0]))
    found = [u for n in names + [x.split("(")[0] for x in more if x] for u in USES.get(n, [])]
    lx.pop("use", None)
    if not found:
        return False
    near = [u for u in found if u[1] and u[1] in funcs]
    lx["use"] = Flow((near or found)[0])
    return True


def parse_linux(ldir, overlay):
    macros = Macros()
    regs, consts, mibs, enums = [], [], [], {}
    ranges = overlay.get("ranges", {})
    prefixes = overlay.get("field_prefix", {})
    default_range = overlay.get("default_ranges", {})
    aliases = overlay.get("aliases", {})
    csrc = {}
    for fn in sorted(os.listdir(ldir)):
        if fn.endswith(".c"):
            with open(os.path.join(ldir, fn)) as f:
                csrc[fn] = f.read()

    funcs = {}   # function name -> [file, line of its definition]
    owner = {}   # file -> function that contains each line
    for fn, text in csrc.items():
        cur, cand, own = None, None, []
        for no, line in enumerate(text.split("\n"), 1):
            mo = re.match(r"(?:[A-Za-z_][\w\s\*]*?[\s\*])?([A-Za-z_]\w*)\(", line)
            if mo and not line.rstrip().endswith(";"):
                cand = (mo.group(1), no)
            if line.startswith("{") and cand:
                cur = cand[0]
                funcs.setdefault(cur, [fn, cand[1]])
            own.append(cur)
            if line.startswith("}"):
                cur = cand = None
        owner[fn] = own
    FUNCS.update(funcs)

    def used(cname):
        """True when a driver source file (not a header) uses the macro."""
        name = cname.split("(")[0]
        if name not in USES:
            pat = re.compile(r"\b%s\b" % re.escape(name))
            USES[name] = [[fn, owner[fn][no - 1] or "", no]
                          for fn, text in csrc.items()
                          for no, line in enumerate(text.split("\n"), 1) if pat.search(line)]
        return bool(USES[name])

    for hdr in HEADERS:
        with open(os.path.join(ldir, hdr)) as f:
            text = f.read()
        enums.update(parse_enums(text, hdr))
        for line in text.split("\n"):
            m = DEF_RE.match(line)
            if m and m.group(4):
                params = None
                if m.group(3):
                    params = [p.strip() for p in m.group(3)[1:-1].split(",")]
                macros.define(m.group(2), params, m.group(4))

    def rng(key, var):
        r = ranges.get(key, {}).get(var) or default_range.get(var)
        if r is None:
            sys.exit(f"no index range for {key} argument {var}; add it to overlay.yaml")
        return r

    for hdr in HEADERS:
        cur_reg = cur_field = None
        in_mib = False
        with open(os.path.join(ldir, hdr)) as f:
            lines = f.read().split("\n")
        for lineno, line in enumerate(lines, 1):
            m = DEF_RE.match(line)
            if not m:
                continue
            level = len(m.group(1))
            name, args, body, note = m.group(2), m.group(3), m.group(4), m.group(5) or ""
            if name.startswith("_") or not body:
                continue
            params = [p.strip() for p in args[1:-1].split(",")] if args else []
            src = [hdr, lineno]
            chip = "" if name.startswith("YT921X") else name[:6].lower()
            short = re.sub(r"^YT921[0-9X]_", "", name)
            for a, b in aliases.items():
                if level > 1 and short.startswith(a):
                    short = b + short[len(a):]
            if level == 1:
                in_mib = name == "YT921X_MIBn_DATAm"
                if in_mib:
                    continue
                if re.match(r"\(?0x[0-9a-fA-F]{5,6}\b", body):
                    rid = reg_id(short)
                    dims = []
                    f = macros[name]
                    if params:
                        rs = [rng(rid, p) for p in params]
                        firsts = [r["first"] * r.get("scale", 1) for r in rs]
                        base = f(*firsts)
                        for i, (p, r) in enumerate(zip(params, rs)):
                            stride = 0
                            if r["count"] > 1:
                                a = list(firsts)
                                a[i] += r.get("scale", 1)
                                stride = f(*a) - base
                            dims.append(dict(var=r.get("name", p), first=r["first"],
                                             count=r["count"], stride=stride))
                        for idx in itertools.product(*[range(r["count"]) for r in rs]):
                            a = [(r["first"] + i) * r.get("scale", 1)
                                 for r, i in zip(rs, idx)]
                            want = base + sum(d["stride"] * i for d, i in zip(dims, idx))
                            assert f(*a) == want, (name, idx)
                    else:
                        base = f
                    cur_reg = dict(id=rid, address=Hex(base), dims=dims,
                                   linux=dict(macro=name + (args or ""), src=src,
                                              used=used(name)),
                                   note=note, fields=[])
                    regs.append(cur_reg)
                    cur_field = None
                else:
                    cur_reg = cur_field = None
                    if not params and re.fullmatch(r"-?\d+|0x[0-9a-fA-F]+", body):
                        consts.append(dict(name=short if not chip else short + "_" + chip.upper(),
                                           value=int(body, 0), cname=name,
                                           src=src, note=note))
                continue
            if level == 2 and in_mib:
                mibs.append(dict(name=short.replace("MIB_DATA_", ""), cname=name,
                                 offset=Hex(int(body, 0)), src=src))
                continue
            if cur_reg is None:
                continue
            rid = cur_reg["id"]
            if level == 2:
                if not re.match(r"BIT\(|GENMASK|\(7 <<", body):
                    continue
                base_short = re.sub(r"_M$", "", short)
                fname, letter = field_name(base_short, rid, prefixes.get(rid))
                woff = 32 * WORD_LETTER.get(letter, 0)
                fld = dict(name=norm(fname), linux=dict(macro=name + (args or ""), src=src,
                                                  used=used(name) or used(re.sub(r"_M$", "", name))),
                           note=note, values=[])
                if chip:
                    fld["chip"] = chip
                if params:
                    key = f"{rid}.{norm(fname)}"
                    rs = [rng(key, p) for p in params]
                    f = macros[name]
                    elems = {}
                    for idx in itertools.product(*[range(r["count"]) for r in rs]):
                        a = [r["first"] + i for r, i in zip(rs, idx)]
                        elems[idx] = mask_bits(f(*a))
                    zero = tuple(0 for _ in rs)
                    lsb0, w = elems[zero]
                    adims = []
                    for i, (p, r) in enumerate(zip(params, rs)):
                        step = 0
                        if r["count"] > 1:
                            one = tuple(1 if j == i else 0 for j in range(len(rs)))
                            step = elems[one][0] - lsb0
                        adims.append(dict(var=r.get("name", p), first=r["first"],
                                          count=r["count"], step=step))
                    for idx, (l, ww) in elems.items():
                        assert ww == w and l == lsb0 + sum(
                            d["step"] * i for d, i in zip(adims, idx)), (name, idx)
                    lo = min(l for l, _ in elems.values())
                    hi = max(l + w - 1 for l, _ in elems.values())
                    fld.update(lsb=woff + lo, width=hi - lo + 1,
                               array=dict(dims=adims, lsb=woff + lsb0, width=w))
                    # per-bit accessor for an already listed mask field?
                    for other in cur_reg["fields"]:
                        if ("array" not in other and other.get("chip", "") == chip
                                and other["lsb"] <= fld["lsb"]
                                and other["lsb"] + other["width"] >= fld["lsb"] + fld["width"]):
                            other["array"] = fld["array"]
                            other["linux"]["used"] = other["linux"]["used"] or used(name)
                            other["array"]["macro"] = name + args
                            other["array"]["src"] = src
                            fld = None
                            break
                    if fld is None:
                        continue
                else:
                    lsb, w = mask_bits(macros[name])
                    fld.update(lsb=woff + lsb, width=w)
                cur_field = fld
                cur_reg["fields"].append(fld)
                continue
            if level == 3 and cur_field is not None:
                if "FIELD_PREP" in body or re.search(r"\(x\) <<", body):
                    continue
                m2 = re.fullmatch(r"\w+\((?:\w+, )?(\d+|0x[0-9a-fA-F]+)\)", body)
                if m2:
                    val = int(m2.group(1), 0)
                elif re.fullmatch(r"\d+|0x[0-9a-fA-F]+", body):
                    val = int(body, 0)
                else:
                    continue
                fshort = re.sub(r"^YT921[0-9X]_", "",
                                cur_field["linux"]["macro"].split("(")[0])
                fshort = re.sub(r"_M$", "", fshort)
                for a, b in aliases.items():
                    if fshort.startswith(a):
                        fshort = b + fshort[len(a):]
                vname = common_prefix_strip(norm(short), norm(fshort))
                v = dict(name=vname, value=val,
                         linux=dict(macro=name + (args or ""), src=src,
                                    used=used(name)), note=note)
                if chip:
                    v["chip"] = chip
                cur_field["values"].append(v)
                if v["linux"]["used"]:
                    cur_field["linux"]["used"] = True

    # MIB counter sizes
    sizes = {}
    with open(os.path.join(ldir, "mib.c")) as f:
        for line in f:
            m = re.search(r"MIB_DESC\((\d), (\w+),", line)
            if m:
                sizes[m.group(2)] = int(m.group(1))
    for mib in mibs:
        mib["words"] = sizes.get(mib["cname"], 1)
    for e in enums.values():
        for mem in e["members"]:
            used(mem["cname"])
    return regs, consts, mibs, enums


# --------------------------------------------------------------------------
# Vendor SDK

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
    ent = {}
    for lineno, line in enumerate(txt, 1):
        m = re.search(r"/\* (Asic Base Address|offset|bytes|Entry Number|Fields_num|fields_id) \*/ (\w+),", line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if key == "Asic Base Address":
            ent = dict(line=lineno, base=int(val, 0))
        elif key == "offset":
            ent["stride"] = int(val, 0)
        elif key == "bytes":
            ent["bytes"] = int(val, 0)
        elif key == "Entry Number":
            ent["entries"] = int(val, 0)
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
                flds.append(dict(name=fn, width=fl["width"], line=fl["line"],
                                 lsb=32 * fl["word"] + fl["bit"]))
            ent["fields"] = flds
            tables.append(ent)
    modules = []
    with open(os.path.join(tdir, "fal_tiger_mem.h")) as f:
        for line in f:
            m = re.match(r"\s*#define MODULE_(\w+)\s+(0x[0-9A-Fa-f]+)\s*$", line)
            if m and int(m.group(2), 0) >= 0x10000:
                modules.append((int(m.group(2), 0), m.group(1)))
    modules.sort()
    return tables, modules


def sdk_lookup(tables, addr):
    for t in tables:
        if t["base"] and t["base"] <= addr < t["base"] + t["stride"] * t["entries"]:
            return t
    return None


def sdk_literal(sdir, addr):
    """SDK source line that uses the address as a literal: [path, line] or None."""
    pat = re.compile(r"0x0*%x\b" % addr, re.I)
    hits = []
    for root, _, files in os.walk(os.path.join(sdir, "switch_sdk")):
        for fn in sorted(files):
            if fn.endswith((".c", ".h")):
                with open(os.path.join(root, fn), errors="replace") as f:
                    for lineno, line in enumerate(f, 1):
                        if pat.search(line):
                            rel = os.path.relpath(os.path.join(root, fn), sdir)
                            hits.append((fn, rel, lineno))
                            break
    hits.sort(key=lambda h: (not h[0].endswith(".h"), h[0]))
    return [hits[0][1], hits[0][2]] if hits else None


def match_field(reg, fld, t):
    """Compare one field with the SDK table: (status, [SDK field names])."""
    if t is None:
        return "no SDK table", []
    if not t["fields"]:
        return "SDK lists no fields", []
    word0 = ((reg["address"] - t["base"]) % t["stride"]) // 4
    lo = 32 * word0 + fld["lsb"]
    hi = lo + fld["width"] - 1
    arr = fld.get("array")
    if arr and any(d["step"] > arr["width"] for d in arr["dims"]):
        # The elements are separated by other bits: compare element 0.
        lo = 32 * word0 + arr["lsb"]
        hi = lo + arr["width"] - 1
    over = sorted((f for f in t["fields"]
                   if f["lsb"] <= hi and f["lsb"] + f["width"] - 1 >= lo),
                  key=lambda f: f["lsb"])
    if not over:
        return "not in SDK", []
    names = [f["name"] for f in over]
    slo = min(f["lsb"] for f in over)
    shi = max(f["lsb"] + f["width"] - 1 for f in over)
    if slo == lo and shi == hi:
        return ("same bits" if len(over) == 1 else "spans SDK fields"), names
    if len(over) == 1 and slo <= lo and shi >= hi:
        return "part of SDK field", names
    return "different bits", names


# --------------------------------------------------------------------------

def strip_layout(name):
    """ACL key field name -> (layout, field name, key_only)."""
    m = re.match(r"ACL_(KEY|BIN)(a|b)_(.+)$", name)
    kind, letter, rest = m.groups()
    for lay in ACL_LAYOUTS:
        if rest.startswith(lay + "_"):
            return lay, rest[len(lay) + 1:], letter, kind == "KEY"
    return "", rest, letter, kind == "KEY"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--linux", required=True)
    ap.add_argument("--linux-sha", required=True)
    ap.add_argument("--sdk", required=True)
    ap.add_argument("--sdk-sha", required=True)
    args = ap.parse_args()

    with open(os.path.join(HERE, "overlay.yaml")) as f:
        overlay = yaml.safe_load(f)

    regs, consts, mibs, enums = parse_linux(args.linux, overlay)
    tables, modules = parse_sdk(args.sdk)
    byid = {r["id"]: r for r in regs}
    assert len(byid) == len(regs), "duplicate register id"

    # ---- ACL key layouts: fields listed after ACL_MASK in the header
    key, mask = byid["ACL_KEY"], byid["ACL_MASK"]
    layouts = {}
    for fld in mask.pop("fields"):
        short = re.sub(r"^YT921X_|_M$", "", fld["linux"]["macro"].split("(")[0])
        lay, fname, letter, key_only = strip_layout(short)
        fld["name"] = norm(fname)
        # bit position was computed without the word letter
        fld["lsb"] = fld["lsb"] % 32 + 32 * WORD_LETTER[letter]
        if key_only:
            fld["key_only"] = True
        layouts.setdefault(lay, []).append(fld)
    key["layouts"] = layouts
    mask["fields"] = []

    # ---- inherit shared field lists
    import copy
    for rid, spec in overlay.get("inherit", {}).items():
        src = byid[spec["from"]]
        got = []
        for fld in src["fields"]:
            if "only" in spec and fld["name"] not in [norm(x) for x in spec["only"]]:
                continue
            if fld["name"] in spec.get("except", []):
                continue
            got.append(copy.deepcopy(fld))
        byid[rid]["fields"] = byid[rid]["fields"] + got
        if "layouts" in src:
            byid[rid]["layouts"] = {
                k: [copy.deepcopy(f) for f in v if not f.get("key_only")]
                for k, v in src["layouts"].items()}

    # ---- overlay: descriptions and hand-written facts
    oreg = overlay["registers"]
    missing = []
    out_regs = []
    for r in regs:
        o = oreg.get(r["id"])
        if o is None:
            missing.append(r["id"])
            continue
        r["block"] = o["block"]
        r["title"] = o["title"]
        r["desc"] = o["desc"].strip()
        r["access"] = o.get("access", "rw")
        r["words"] = o.get("words", 1)
        if "reset" in o:
            r["reset"] = Hex(o["reset"])
        for k in ("chips", "inferred"):
            if k in o:
                r[k] = o[k]
        ofl = {norm(k): v for k, v in o.get("fields", {}).items()}
        for name, extra in o.get("add_fields", {}).items():
            r["fields"].append(dict(name=name, lsb=extra["lsb"], width=extra["width"],
                                    values=[], note=""))
            ofl = dict(ofl)
            ofl[name] = extra

        def finish(fld, where, lay=None):
            key = fld["name"] if lay is None else f"{lay or 'COMMON'}/{fld['name']}"
            fo = ofl.get(key)
            if fo is None and lay is not None:
                fo = ofl.get(fld["name"])
            if fo is None:
                missing.append(f"{r['id']}.{key}")
                fo = {}
            fld["desc"] = (fo.get("desc") or "").strip()
            fld["access"] = fo.get("access", r["access"])
            if "linux" not in fld:
                fld["inferred"] = True
            for k in ("enum", "reset", "group", "unit", "inferred"):
                if k in fo:
                    fld[k] = fo[k]
            vdesc = fo.get("values", {})
            for v in fld.get("values", []):
                if v["name"] == "DEFAULT":
                    fld["reset"] = v["value"]
                v["desc"] = vdesc.get(v["name"], "")
                v["name"] = ident(v["name"])
                v.pop("note", None)
            fld["values"] = [v for v in fld.get("values", []) if v["name"] != "DEFAULT"]
            if not fld["values"]:
                fld.pop("values")
            fld.pop("note", None)

        for fld in r["fields"]:
            finish(fld, r)
        for lay, fl in r.get("layouts", {}).items():
            for fld in fl:
                finish(fld, r, lay)
        r["fields"].sort(key=lambda f: (-f["lsb"], f.get("chip", "")))
        for fl in r.get("layouts", {}).values():
            fl.sort(key=lambda f: -f["lsb"])
        if "layouts" in r:
            lo = overlay["acl_layouts"]
            r["layouts"] = [dict(name=k or "COMMON", title=lo[k or "COMMON"]["title"],
                                 types=Flow(lo[k or "COMMON"]["types"]),
                                 fields=v)
                            for k, v in r["layouts"].items()]
            common = [x for x in r["layouts"] if x["name"] == "COMMON"]
            r["layouts"] = [x for x in r["layouts"] if x["name"] != "COMMON"]
            # IPV6 fields are part of every IPV6_xAn layout
            ipv6 = next(x for x in r["layouts"] if x["name"] == "IPV6")
            for x in r["layouts"]:
                if x["name"].startswith("IPV6_"):
                    x["fields"] = sorted(x["fields"] + copy.deepcopy(ipv6["fields"]),
                                         key=lambda f: -f["lsb"])
            ipv6["name"] = "IPV6_xA0"
            for x in r["layouts"]:
                key = "IPV6" if x["name"] == "IPV6_xA0" else x["name"]
                x["linux_name"] = key
                for f in x["fields"]:
                    f["name"] = lo[key].get("rename", {}).get(f["name"], f["name"])
            if common:
                r["fields"] = sorted(r["fields"] + common[0]["fields"],
                                     key=lambda f: -f["lsb"])
            order = [x for x in overlay["acl_layouts"] if x != "COMMON"]
            r["layouts"].sort(key=lambda x: order.index(x["linux_name"]))
            for x in r["layouts"]:
                x["name"] = lo[x.pop("linux_name")].get("name", x["name"])

        # ---- where the driver uses each item
        allf = r["fields"] + [f for l in r.get("layouts", []) for f in l["fields"]]
        r["linux"]["used"] = first_use(r["linux"], ())
        rname = r["linux"]["macro"].split("(")[0]
        rfuncs = {u[1] for u in USES.get(rname, [])}
        for fld in allf:
            lx = fld.get("linux")
            if not lx:
                continue
            vals = [v["linux"]["macro"] for v in fld.get("values", []) if v.get("linux")]
            arr = (fld.get("array") or {}).get("macro")
            # a field counts as used only in a register the driver touches
            lx["used"] = first_use(lx, rfuncs, arr, *vals) and r["linux"]["used"]
            if not lx["used"]:
                lx.pop("use", None)
        if len(allf) == 1 and not allf[0].get("linux", {}).get("used") \
                and "inferred" not in ofl.get(allf[0]["name"], {}):
            # the only field of a register shares the evidence of the register
            keep = allf[0].get("linux") or dict(macro="", src=None)
            keep["used"] = r["linux"]["used"]
            if r["linux"].get("use"):
                keep["use"] = r["linux"]["use"]
            if not keep["src"]:
                keep = dict(r["linux"])
                keep.pop("macro"); keep = dict(macro="", **keep)
            allf[0]["linux"] = keep
            if not r.get("inferred"):
                allf[0].pop("inferred", None)
        if len(allf) == 1 and r.get("inferred"):
            allf[0]["inferred"] = True

        # ---- vendor SDK cross-check
        t = sdk_lookup(tables, r["address"])
        if t:
            r["sdk"] = dict(table=t["name"], entries=t["entries"], bytes=t["bytes"],
                            src=["switch_sdk/core/fal/tiger/fal_tiger_index.c", t["line"]])
        else:
            lit = sdk_literal(args.sdk, r["address"])
            if lit:
                r["sdk"] = dict(literal=True, src=lit)
        for fld in r["fields"] + [f for l in r.get("layouts", []) for f in l["fields"]]:
            status, names = match_field(r, fld, t)
            fld["sdk"] = dict(status=status)
            if names:
                fld["sdk"]["fields"] = Flow(names)
        r.pop("note", None)
        out_regs.append(r)

    unknown = set(oreg) - set(byid)
    if missing or unknown:
        for x in missing:
            print("overlay.yaml has no entry for", x, file=sys.stderr)
        for x in unknown:
            print("overlay.yaml names unknown register", x, file=sys.stderr)
        if not os.environ.get("YT_DRAFT"):
            sys.exit(1)

    # ---- order registers by block order then address
    border = [b["id"] for b in overlay["blocks"]]
    out_regs.sort(key=lambda r: (border.index(r["block"]), r["address"]))

    # ---- enums and counters
    oen = overlay.get("enums", {})
    out_enums = []
    for name, e in enums.items():
        if name not in oen:
            continue
        od = oen[name]
        out_enums.append(dict(
            name=name, title=od["title"], desc=od["desc"].strip(),
            linux=dict(macro="enum yt921x_" + name, src=e["src"]),
            values=[dict(name=ident(m["name"]), value=m["value"],
                         desc=od.get("values", {}).get(m["name"], ""),
                         linux=enum_linux(m))
                    for m in e["members"]]))
    omib = overlay["counters"]
    out_mibs = []
    for mib in mibs:
        if mib["name"] not in omib:
            sys.exit("overlay.yaml has no counter description for " + mib["name"])
        out_mibs.append(dict(name=mib["name"], offset=mib["offset"], words=mib["words"],
                             desc=omib[mib["name"]],
                             linux=dict(macro=mib["cname"], src=mib["src"])))
    ocon = overlay["constants"]
    out_consts = []
    for c in consts:
        if c["name"] in ocon:
            out_consts.append(dict(name=c["name"], value=c["value"],
                                   desc=ocon[c["name"]],
                                   linux=dict(macro=c["cname"], src=c["src"])))

    doc = dict(
        schema=1,
        device=overlay["device"],
        sources=dict(
            linux=dict(repo="https://github.com/torvalds/linux", commit=args.linux_sha,
                       paths=LINUX_PATHS),
            sdk=dict(repo="https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk",
                     commit=args.sdk_sha)),
        linux_functions={k: Flow(v) for k, v in sorted(FUNCS.items())},
        chips=overlay["chips"],
        regions=[dict(name=x["name"], base=Hex(x["base"]), title=x["title"])
                 for x in overlay["regions"]],
        blocks=overlay["blocks"],
        constants=out_consts,
        enums=out_enums,
        registers=out_regs,
        counters=out_mibs,
    )
    hdr = ("# YT921x register description. Written by tools/extract.py from the\n"
           "# Linux driver, the vendor SDK and tools/overlay.yaml. Edit overlay.yaml\n"
           "# and run extract.py again; tools/generate.py turns this file into the\n"
           "# documentation, the SVD and SystemRDL files and the language bindings.\n")
    with open(os.path.join(ROOT, "yt921x.yaml"), "w") as f:
        f.write(hdr)
        yaml.safe_dump(doc, f, sort_keys=False, width=100, allow_unicode=True)

    # ---- SDK table list
    covered = {}
    for r in out_regs:
        if "table" in r.get("sdk", {}):
            covered.setdefault(r["sdk"]["table"], []).append(r["id"])
    sdk_doc = dict(
        schema=1,
        source=dict(repo="https://github.com/OpenEmbeddedBSP/motorcomm-yt9215-switch-sdk",
                    commit=args.sdk_sha,
                    index="switch_sdk/core/fal/tiger/fal_tiger_index.c",
                    struct="switch_sdk/core/fal/tiger/fal_tiger_struct.c",
                    modules="switch_sdk/core/fal/tiger/fal_tiger_mem.h"),
        modules=[dict(name=n, base=Hex(b)) for b, n in modules],
        tables=[dict(name=t["name"], address=Hex(t["base"]), stride=t["stride"],
                     bytes=t["bytes"], entries=t["entries"],
                     index_line=t["line"], struct_line=t["struct_line"],
                     registers=Flow(covered.get(t["name"], [])),
                     fields=[dict(name=f["name"], lsb=f["lsb"], width=f["width"],
                                  line=f["line"])
                             for f in sorted(t["fields"], key=lambda f: -f["lsb"])])
                for t in tables])
    with open(os.path.join(ROOT, "sdk-tables.yaml"), "w") as f:
        f.write("# Vendor SDK table list. Written by tools/extract.py.\n")
        yaml.safe_dump(sdk_doc, f, sort_keys=False, width=100)
    nf = sum(len(r["fields"]) + sum(len(l["fields"]) for l in r.get("layouts", []))
             for r in out_regs)
    print(f"{len(out_regs)} registers, {nf} fields, {len(out_mibs)} counters, "
          f"{len(tables)} SDK tables")


if __name__ == "__main__":
    main()
