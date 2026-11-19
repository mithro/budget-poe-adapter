"""CMSIS-SVD description, one file per chip family."""
from xml.sax.saxutils import escape

from model import (addr_of, elems, highest_addr, lowest_addr, n_elems, plain,
                   values_of, visible_fields)

ACCESS = {"rw": "read-write", "ro": "read-only", "wo": "write-only"}


def is_packed(reg):
    """True when the elements of a register array fill one address range in
    index order (last index fastest), so that one flat array describes it."""
    size = 4 * reg["words"]
    want = size
    for d in reversed(reg["dims"]):
        if abs(d["stride"]) != want:
            return False
        want *= d["count"]
    return True


class X:
    def __init__(self):
        self.lines = []
        self.depth = 0

    def tag(self, name, text):
        self.lines.append("%s<%s>%s</%s>" % ("  " * self.depth, name, escape(str(text)), name))

    def open(self, name, attrs=""):
        self.lines.append("%s<%s%s>" % ("  " * self.depth, name, attrs))
        self.depth += 1

    def close(self, name):
        self.depth -= 1
        self.lines.append("%s</%s>" % ("  " * self.depth, name))


def emit_field(x, m, name, lsb, width, f, dim=None):
    x.open("field")
    if dim:
        x.tag("dim", dim["count"])
        x.tag("dimIncrement", dim["step"])
        x.tag("dimIndex", "%d-%d" % (dim["first"], dim["first"] + dim["count"] - 1))
    x.tag("name", name)
    x.tag("description", plain(f["desc"]))
    x.tag("bitOffset", lsb)
    x.tag("bitWidth", width)
    x.tag("access", ACCESS[f["access"]])
    return x


def emit_values(x, m, f, family, width):
    vals = [v for v in values_of(m, f) if not v.get("chip") or v["chip"] == family]
    vals = [v for v in vals if v["value"] < (1 << width)]
    if vals:
        x.open("enumeratedValues")
        for v in vals:
            x.open("enumeratedValue")
            x.tag("name", v["name"])
            x.tag("description", plain(v["desc"]))
            x.tag("value", v["value"])
            x.close("enumeratedValue")
        x.close("enumeratedValues")


def emit_fields(x, m, fields, word, family):
    """Fields (or the parts of fields) that fall into one 32-bit word."""
    lo, hi = 32 * word, 32 * word + 31
    todo = []
    for f in fields:
        if f["lsb"] > hi or f["lsb"] + f["width"] - 1 < lo:
            continue
        todo.append(f)
    if not todo:
        return
    x.open("fields")
    for f in sorted(todo, key=lambda f: f["lsb"]):
        a = f.get("array")
        if a:
            d = a["dims"][0]
            if len(a["dims"]) == 1 and d["step"] > 0:
                emit_field(x, m, f["name"] + "%s", a["lsb"] - lo, a["width"], f, d)
                emit_values(x, m, f, family, a["width"])
                x.close("field")
            else:
                for idx, lsb, w in elems(f):
                    emit_field(x, m, f["name"] + "".join("_%d" % i for i in idx),
                               lsb - lo, w, f)
                    emit_values(x, m, f, family, w)
                    x.close("field")
            continue
        flo = max(f["lsb"], lo)
        fhi = min(f["lsb"] + f["width"] - 1, hi)
        name = f["name"]
        if f["lsb"] < lo:
            name += "_HI"
        elif f["lsb"] + f["width"] - 1 > hi:
            name += "_LO"
        emit_field(x, m, name, flo - lo, fhi - flo + 1, f)
        if name == f["name"]:
            emit_values(x, m, f, family, f["width"])
        x.close("field")
    x.close("fields")


def reg_common(x, reg, name, offset, desc, word=0):
    x.tag("name", name)
    x.tag("description", desc)
    x.tag("addressOffset", "0x%X" % offset)
    x.tag("size", 32)
    x.tag("access", ACCESS[reg["access"]])
    if "reset" in reg and word == 0:
        x.tag("resetValue", "0x%08X" % reg["reset"])
        x.tag("resetMask", "0xFFFFFFFF")


def emit_words(x, m, reg, family, base_off, prefix=""):
    """The word registers of one (possibly multi-word) register entry."""
    fields = visible_fields(reg, family)
    multi = reg["words"] > 1
    for word in range(reg["words"]):
        wname = (prefix + "W%d" % word) if multi else prefix
        x.open("register")
        desc = plain(reg["desc"])
        if multi:
            desc = "%s: bits %d to %d. %s" % (reg["title"], 32 * word + 31, 32 * word, desc)
        reg_common(x, reg, wname, base_off + 4 * word, desc, word)
        emit_fields(x, m, fields, word, family)
        x.close("register")
        for lay in reg["layouts"]:
            lf = visible_fields(reg, family, lay)
            if not any(f["lsb"] // 32 <= word <= (f["lsb"] + f["width"] - 1) // 32 for f in lf):
                continue
            x.open("register")
            x.tag("name", "%s_%s" % (wname, lay["name"]))
            x.tag("description", "%s, bits %d to %d, layout for key types %s: %s"
                  % (reg["title"], 32 * word + 31, 32 * word, ", ".join(lay["types"]),
                     lay["title"]))
            x.tag("alternateRegister", wname)
            x.tag("addressOffset", "0x%X" % (base_off + 4 * word))
            x.tag("size", 32)
            x.tag("access", ACCESS[reg["access"]])
            emit_fields(x, m, fields + lf, word, family)
            x.close("register")


def dim_tags(x, count, incr, first=0):
    x.tag("dim", count)
    x.tag("dimIncrement", "0x%X" % incr)
    if first:
        x.tag("dimIndex", "%d-%d" % (first, first + count - 1))


def emit_register(x, m, reg, family, pbase):
    rid = reg["id"]
    off = lowest_addr(reg) - pbase
    dims = reg["dims"]
    multi = reg["words"] > 1
    size = 4 * reg["words"]
    if rid == "MIB_DATA":
        d = dims[0]
        x.open("cluster")
        dim_tags(x, d["count"], d["stride"])
        x.tag("name", "MIB[%s]")
        x.tag("description", "Counters of one port. " + plain(reg["desc"]))
        x.tag("addressOffset", "0x%X" % off)
        for c in m.counters:
            x.open("register")
            x.tag("name", c["name"])
            x.tag("description", plain(c["desc"]))
            x.tag("addressOffset", "0x%X" % c["offset"])
            x.tag("size", 32 * c["words"])
            x.tag("access", "read-only")
            x.close("register")
        x.close("cluster")
        return
    idx_note = ""
    if dims:
        idx_note = " Index: " + ", ".join(
            "%s = %d to %d" % (d["var"], d["first"], d["first"] + d["count"] - 1)
            for d in dims) + "."
    if not dims:
        if multi:
            x.open("cluster")
            x.tag("name", rid)
            x.tag("description", plain(reg["desc"]))
            x.tag("addressOffset", "0x%X" % off)
            emit_words(x, m, reg, family, 0)
            x.close("cluster")
        else:
            emit_words(x, m, reg, family, off, rid)
        return
    if is_packed(reg) or len(dims) == 1:
        count = n_elems(reg)
        stride = abs(dims[-1]["stride"]) if is_packed(reg) else dims[0]["stride"]
        first = dims[0]["first"] if len(dims) == 1 else 0
        if len(dims) > 1 or dims[0]["stride"] < 0:
            order = " Flat index = " + " + ".join(
                "%s%s" % ("%d × " % prod if prod > 1 else "",
                           d["var"] if d["stride"] > 0 else "(%d − %s)" % (d["count"] - 1, d["var"]))
                for d, prod in zip(dims, strides_in_elems(reg))) + "."
            idx_note += order
        if multi:
            x.open("cluster")
            dim_tags(x, count, stride, first)
            x.tag("name", rid + ("[%s]" if not first else "_%s"))
            x.tag("description", plain(reg["desc"]) + idx_note)
            x.tag("addressOffset", "0x%X" % off)
            emit_words(x, m, reg, family, 0)
            x.close("cluster")
        else:
            x.open("register")
            dim_tags(x, count, stride, first)
            reg_common(x, reg, rid + ("[%s]" if not first else "_%s"), off,
                       plain(reg["desc"]) + idx_note)
            emit_fields(x, m, visible_fields(reg, family), 0, family)
            x.close("register")
        return
    # outer dimension with gaps: a cluster array around the inner array
    inner, outer = dims[0], dims[1]
    x.open("cluster")
    dim_tags(x, outer["count"], outer["stride"], outer["first"])
    x.tag("name", rid + "[%s]")
    x.tag("description", plain(reg["desc"]) + " Index: %s = %d to %d; the member array index is %s."
          % (outer["var"], outer["first"], outer["first"] + outer["count"] - 1, inner["var"]))
    x.tag("addressOffset", "0x%X" % off)
    x.open("cluster")
    dim_tags(x, inner["count"], inner["stride"], inner["first"])
    x.tag("name", inner["var"].upper() + "[%s]")
    x.tag("description", "One %s entry; index %s = %d to %d."
          % (rid, inner["var"], inner["first"], inner["first"] + inner["count"] - 1))
    x.tag("addressOffset", "0x0")
    emit_words(x, m, reg, family, 0)
    x.close("cluster")
    x.close("cluster")


def strides_in_elems(reg):
    size = 4 * reg["words"]
    return [abs(d["stride"]) // size for d in reg["dims"]]


def generate(m, family):
    x = X()
    dev = m.d["device"]
    parts = [c["name"] for c in m.chips if c["family"] == family]
    x.lines.append('<?xml version="1.0" encoding="utf-8"?>')
    x.lines.append("<!-- Generated by tools/generate.py from yt921x.yaml. Do not edit. -->")
    x.open("device", ' schemaVersion="1.3" xmlns:xs="http://www.w3.org/2001/XMLSchema-instance"'
                     ' xs:noNamespaceSchemaLocation="CMSIS-SVD.xsd"')
    x.tag("vendor", dev["vendor"])
    x.tag("name", family.upper())
    x.tag("series", dev["name"])
    x.tag("version", "1.0")
    x.tag("description",
          "%s, %s family (%s). The addresses are those of the switch register space, "
          "which a host reaches indirectly over MDIO; they are not memory mapped."
          % (dev["title"], family.upper(), ", ".join(parts)))
    x.tag("addressUnitBits", 8)
    x.tag("width", 32)
    x.tag("size", 32)
    x.tag("access", "read-write")
    x.tag("resetValue", "0x00000000")
    x.tag("resetMask", "0x00000000")
    x.open("peripherals")
    for region in m.regions:
        regs = sorted((r for r in m.regs if r["region"] == region["name"]),
                      key=lowest_addr)
        if not regs:
            continue
        end = max(highest_addr(r) for r in regs)
        if any(r["id"] == "MIB_DATA" for r in regs):
            end = max(end, lowest_addr(m.byid["MIB_DATA"]) + 0x100 * 11 - 1)
        x.open("peripheral")
        x.tag("name", region["name"])
        x.tag("description", region["title"])
        x.tag("baseAddress", "0x%08X" % region["base"])
        x.open("addressBlock")
        x.tag("offset", "0x0")
        x.tag("size", "0x%X" % (end - region["base"] + 1))
        x.tag("usage", "registers")
        x.close("addressBlock")
        x.open("registers")
        for r in regs:
            emit_register(x, m, r, family, region["base"])
        x.close("registers")
        x.close("peripheral")
    x.close("peripherals")
    x.close("device")
    return "\n".join(x.lines) + "\n"
