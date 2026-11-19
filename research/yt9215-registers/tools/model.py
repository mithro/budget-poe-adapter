"""Load yt921x.yaml and answer the questions every generator asks."""
import itertools
import os
import re

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ROLE_RE = re.compile(r":(?:reg|field|blk|enum|counter|const|chip|sdk|val|lx|ev):`([^`<]+?)(?: <[^`]+>)?`")
REF_RE = re.compile(r":(?:ref|doc):`([^`<]+?) <[^`]+>`")


def plain(text):
    """Description text without documentation roles or inline markup."""
    text = ROLE_RE.sub(r"\1", text)
    text = REF_RE.sub(r"\1", text)
    text = re.sub(r"`([^`<]+) <[^`]+>`__", r"\1", text)
    text = text.replace("``", "").replace("|ds|", "YT9215SCH datasheet")
    return " ".join(text.split())


class Model:
    def __init__(self, path=None):
        with open(path or os.path.join(ROOT, "yt921x.yaml")) as f:
            self.d = yaml.safe_load(f)
        self.regs = self.d["registers"]
        self.byid = {r["id"]: r for r in self.regs}
        self.blocks = self.d["blocks"]
        self.enums = {e["name"]: e for e in self.d["enums"]}
        self.counters = self.d["counters"]
        self.constants = self.d["constants"]
        self.chips = self.d["chips"]
        self.regions = sorted(self.d["regions"], key=lambda x: x["base"])
        self.sources = self.d["sources"]
        for r in self.regs:
            r["region"] = self.region_of(r["address"])["name"]
            r.setdefault("layouts", [])
        with open(os.path.join(ROOT, "sdk-tables.yaml")) as f:
            self.sdk = yaml.safe_load(f)

    def region_of(self, addr):
        best = None
        for x in self.regions:
            if x["base"] <= addr:
                best = x
        return best

    def block_regs(self, block_id):
        return sorted((r for r in self.regs if r["block"] == block_id),
                      key=lambda r: r["address"])


# ---- registers

def n_elems(reg):
    n = 1
    for d in reg["dims"]:
        n *= d["count"]
    return n


def addr_of(reg, idx):
    """Address of one element; idx holds the real index values."""
    return reg["address"] + sum(d["stride"] * (i - d["first"])
                                for d, i in zip(reg["dims"], idx))


def lowest_addr(reg):
    return min(addr_of(reg, idx) for idx in corner_indices(reg))


def highest_addr(reg):
    return max(addr_of(reg, idx) for idx in corner_indices(reg)) + 4 * reg["words"] - 1


def corner_indices(reg):
    return itertools.product(*[(d["first"], d["first"] + d["count"] - 1)
                               for d in reg["dims"]])


def index_text(reg):
    """PORT_CTRL[port] style suffix."""
    return "".join("[%s]" % d["var"] for d in reg["dims"])


def addr_formula(reg, mul="×"):
    """0x80100 + 4 × port, written for people."""
    s = "0x%05x" % reg["address"]
    for d in reg["dims"]:
        v = d["var"] if d["first"] == 0 else "(%s − %d)" % (d["var"], d["first"])
        if d["stride"] < 0:
            s += " − %s %s %s" % (stride_text(-d["stride"]), mul, v)
        else:
            s += " + %s %s %s" % (stride_text(d["stride"]), mul, v)
    return s


def stride_text(n):
    return str(n) if n < 16 else "0x%x" % n


def all_fields(reg):
    """Every field of the register, layout fields included, as (layout, field)."""
    for f in reg["fields"]:
        yield None, f
    for lay in reg["layouts"]:
        for f in lay["fields"]:
            yield lay, f


def fsym(reg, fld, lay=None):
    """Flat symbol of a field: PORT_CTRL_LINK_AN, IO_LEVEL_YT9215_NORMAL,
    ACL_KEY_VLAN_SVID."""
    parts = [reg["id"]]
    if lay is not None:
        parts.append(lay["name"])
    if fld.get("chip"):
        parts.append(fld["chip"].upper())
    parts.append(fld["name"])
    return "_".join(parts)


def fdisplay(fld):
    """Field name as shown in documents: BLOCK[port]."""
    a = fld.get("array")
    if not a:
        return fld["name"]
    return fld["name"] + "".join("[%s]" % d["var"] for d in a["dims"])


def elems(fld):
    """(index tuple, lsb, width) of every element of an array field."""
    a = fld["array"]
    out = []
    for idx in itertools.product(*[range(d["count"]) for d in a["dims"]]):
        lsb = a["lsb"] + sum(d["step"] * i for d, i in zip(a["dims"], idx))
        out.append((tuple(d["first"] + i for d, i in zip(a["dims"], idx)), lsb, a["width"]))
    return out


def packed(fld):
    """True when the elements of an array field fill its bit range with no gaps."""
    a = fld["array"]
    return fld["width"] == a["width"] * len(elems(fld))


def bits_text(lsb, width):
    return str(lsb) if width == 1 else "%d:%d" % (lsb + width - 1, lsb)


def values_of(model, fld):
    """Enumerated values of a field: its own or those of its shared enum."""
    if fld.get("values"):
        return fld["values"]
    if fld.get("enum"):
        return model.enums[fld["enum"]]["values"]
    return []


def chips_of(model, family):
    return [c for c in model.chips if c["family"] == family]


def visible_fields(reg, family=None, lay=None):
    """Fields to draw or list: no group masks, and only one chip family."""
    src = lay["fields"] if lay is not None else reg["fields"]
    out = []
    for f in src:
        if f.get("group"):
            continue
        if family and f.get("chip") and f["chip"] != family:
            continue
        out.append(f)
    return out


def families(reg):
    fams = sorted({f["chip"] for f in reg["fields"] if f.get("chip")})
    return fams or [None]
