"""Write the generated pages of the documentation: the register reference.

``generate(model, docs_dir)`` writes ``docs_dir/reference/``. The pages use
the roles and directives of ``yt921x_sphinx.py``; the hand-written guide in
``docs_dir`` is scanned so that every register lists the guide sections
that mention it.
"""
import glob
import os
import re

import diagrams
import model as M

#: Document name prefix of the documentation inside the Sphinx project.
DOCROOT = "research/yt9215-registers/docs"

ACCESS = {"rw": "read/write", "ro": "read only"}
EVIDENCE = ("driver", "header", "inferred")


# ------------------------------------------------------------------- labels

def reg_label(reg_id):
    return "reg-" + reg_id.lower()


def field_label(sym):
    return "field-" + sym.lower()


def blk_label(block_id):
    return "blk-" + block_id


def enum_label(name):
    return "enum-" + name.lower()


def counter_label(name):
    return "counter-" + name.lower()


def const_label(name):
    return "const-" + name.lower()


def chip_label(name):
    return "chip-" + name.lower()


def sdk_label(name):
    return "sdk-" + name.lower()


def vals_label(sym):
    """The value table of a field."""
    return "vals-" + sym.lower()


def val_label(sym, name):
    """One value of a field."""
    return "val-%s-%s" % (sym.lower(), name.lower())


def enum_val_label(enum, name):
    return "val-enum-%s-%s" % (enum.lower(), name.lower())


FAMILY = {"yt9215": "YT9215 family", "yt9218": "YT9218 family"}


def html_id(label):
    """The id docutils gives the target of a label."""
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


#: Stand-in region of the SDK tables that have no address of their own.
NO_ADDRESS = {"name": "RULE_LAYOUTS", "base": None,
              "title": "ACL rule layouts without an address"}


def region_slug(region):
    return region["name"].lower().replace("_", "-")


def region_page(region):
    return "reference/regions/" + region_slug(region)


def sdk_region(m, table):
    """Region of an SDK table; tables at address 0 are layouts, not registers."""
    if table["address"] == 0:
        return NO_ADDRESS
    return m.region_of(table["address"])


def targets(m):
    """Every label of the generated pages -> page (relative to the docs)."""
    t = {}

    def put(label, page):
        if label in t:
            raise ValueError("label defined twice: " + label)
        t[label] = page

    for b in m.blocks:
        put(blk_label(b["id"]), "reference/" + b["id"])
    for r in m.regs:
        page = "reference/" + r["block"]
        put(reg_label(r["id"]), page)
        for lay, f in M.all_fields(r):
            sym = M.fsym(r, f, lay)
            put(field_label(sym), page)
            if f.get("values"):
                put(vals_label(sym), page)
                for v in f["values"]:
                    put(val_label(sym, v["name"]), page)
    for e in m.enums.values():
        put(enum_label(e["name"]), "reference/enums")
        for v in e["values"]:
            put(enum_val_label(e["name"], v["name"]), "reference/enums")
    for c in m.counters:
        put(counter_label(c["name"]), "reference/counters")
    for c in m.constants:
        put(const_label(c["name"]), "reference/constants")
    for c in m.chips:
        put(chip_label(c["name"]), "reference/parts")
    for tb in m.sdk["tables"]:
        put(sdk_label(tb["name"]), region_page(sdk_region(m, tb)))
    ids = {}
    for label in t:
        if ids.setdefault(html_id(label), label) != label:
            raise ValueError("labels share an id: %s, %s" % (label, ids[html_id(label)]))
    return t


def field_syms(m):
    """REG.FIELD spelling accepted by the field role -> flat symbol."""
    out = {}
    for r in m.regs:
        for lay, f in M.all_fields(r):
            sym = M.fsym(r, f, lay)
            out[r["id"] + "." + sym[len(r["id"]) + 1:]] = sym
    return out


# ---------------------------------------------------------------------- rst

def heading(text, ch):
    return [text, ch * len(text), ""]


def target(label):
    return [".. _%s:" % label, ""]


def table(headers, rows, widths=None, cls=None):
    """list-table; a cell may hold several lines."""
    out = [".. list-table::", "   :header-rows: 1"]
    if widths:
        out.append("   :widths: " + " ".join(str(w) for w in widths))
    if cls:
        out.append("   :class: " + cls)
    out.append("")
    for row in [headers] + rows:
        for i, cell in enumerate(row):
            lines = str(cell).split("\n") or [""]
            out.append("   %s - %s" % ("*" if i == 0 else " ", lines[0]))
            out.extend(("       " + ln).rstrip() for ln in lines[1:])
    out.append("")
    return out


def facts(rows):
    out = [".. list-table::", "   :widths: 22 78", "   :class: yt-facts", ""]
    for k, v in rows:
        out.append("   * - " + k)
        out.append("     - " + v)
    out.append("")
    return out


def lit(s):
    return "``%s``" % s


def hexaddr(a):
    return "0x%05x" % a


def linux_url(m, src):
    s = m.sources["linux"]
    return "%s/blob/%s/%s#L%d" % (s["repo"], s["commit"], s["paths"][src[0]], src[1])


def sdk_url(m, path, line=None):
    s = m.sources["sdk"]
    return "%s/blob/%s/%s%s" % (s["repo"], s["commit"], path, "#L%d" % line if line else "")


def linux_link(m, lx):
    if not lx or not lx.get("src"):
        return ""
    return "`%s:%d <%s>`__" % (lx["src"][0], lx["src"][1], linux_url(m, lx["src"]))


def evidence(item):
    lx = item.get("linux") or {}
    if item.get("inferred"):
        return "inferred"
    return "driver" if lx.get("used") else "header"


def evidence_link(item):
    return ":ref:`%s <evidence>`" % evidence(item)


def range_text(first, count):
    return "%d to %d" % (first, first + count - 1) if count > 1 else str(first)


# ----------------------------------------------------------------- diagrams

def diagram_fields(m, reg, family=None, layout=None, href=None):
    """Boxes of the register diagram of one register."""
    out = []

    def add(f, lay, cls):
        sym = M.fsym(reg, f, lay)
        base = {"cls": cls, "href": href(field_label(sym)) if href else None,
                "tip": "%s: %s" % (M.fdisplay(f), M.plain(f["desc"]))}
        if f.get("array") and not M.packed(f):
            for idx, lsb, width in M.elems(f):
                name = f["name"] + "".join("[%d]" % i for i in idx)
                out.append(dict(base, name=name, lsb=lsb, width=width))
            return
        ticks = [lsb for _, lsb, _ in M.elems(f)] if f.get("array") else ()
        out.append(dict(base, name=M.fdisplay(f), lsb=f["lsb"], width=f["width"], ticks=ticks))

    for f in M.visible_fields(reg, family):
        add(f, None, "yt-ro" if f["access"] == "ro" else "")
    if layout is not None:
        for f in M.visible_fields(reg, family, layout):
            if f.get("key_only") and reg["id"] != "ACL_KEY":
                continue
            add(f, layout, "yt-alt")
    return out


def bitfield_svg(m, reg, family=None, layout=None, href=None):
    label = "Bit fields of " + reg["id"]
    return diagrams.bitfield(label, reg["words"], diagram_fields(m, reg, family, layout, href))


# -------------------------------------------------------------- guide scan

ROLE = re.compile(r":(reg|field|enum|counter|const):`(?:[^`<]*<)?([A-Za-z0-9_.]+)>?`")
UNDERLINE = re.compile(r"^([=\-~^\"#*+])\1{2,}\s*$")
LABEL = re.compile(r"^\.\. _([^:]+):\s*$")


def scan_guide(docs_dir):
    """Names mentioned in the hand-written pages -> [(label or None, page, title)]."""
    refs = {}
    for path in sorted(glob.glob(os.path.join(docs_dir, "*.rst"))):
        page = os.path.splitext(os.path.basename(path))[0]
        with open(path) as f:
            lines = f.read().split("\n")
        label, pending, title, doc_title = None, None, None, None
        for i, line in enumerate(lines):
            mo = LABEL.match(line)
            if mo:
                pending = mo.group(1)
                continue
            if i + 1 < len(lines) and line.strip() and UNDERLINE.match(lines[i + 1]) \
                    and not UNDERLINE.match(line):
                title = line.strip()
                doc_title = doc_title or title
                label, pending = pending, None
                continue
            for kind, name in ROLE.findall(line):
                key = (kind if kind != "field" else "reg", name.split(".")[0])
                entry = (label, page, title or doc_title or page)
                if entry not in refs.setdefault(key, []):
                    refs[key].append(entry)
    return refs


def reg_mentions(m):
    """Register -> registers whose descriptions mention it."""
    out = {}
    for r in m.regs:
        texts = [r["desc"]] + [f["desc"] for _, f in M.all_fields(r)]
        for kind, name in ROLE.findall(" ".join(texts)):
            other = name.split(".")[0]
            if kind in ("reg", "field") and other != r["id"] and other in m.byid:
                if r["id"] not in out.setdefault(other, []):
                    out[other].append(r["id"])
    return out


def used_in(entries):
    out = []
    for label, page, title in entries:
        if label:
            out.append(":ref:`%s <%s>`" % (title, label))
        else:
            out.append(":doc:`%s </%s/%s>`" % (title, DOCROOT, page))
    return out


# ------------------------------------------------------------ register page

def field_rows(m, reg, fields, lay, show_parts, show_unit, show_reset):
    rows = []
    for f in sorted(fields, key=lambda f: -f["lsb"]):
        sym = M.fsym(reg, f, lay)
        desc = f["desc"].strip()
        if f.get("enum"):
            desc += " Values: :enum:`%s`." % f["enum"]
        elif f.get("values"):
            desc += " :ref:`Value list <%s>`." % vals_label(sym)
        name = ".. _%s:\n\n.. index:: single: %s (field of %s)\n\n%s" % (
            field_label(sym), f["name"], reg["id"], lit(M.fdisplay(f)))
        row = [M.bits_text(f["lsb"], f["width"]), name, ACCESS[f["access"]]]
        if show_parts:
            row.append(FAMILY.get(f.get("chip"), "all"))
        if show_unit:
            row.append(f.get("unit", ""))
        if show_reset:
            row.append(lit("0x%x" % f["reset"]) if f.get("reset") is not None else "")
        row += [evidence_link(f), desc]
        rows.append(row)
    return rows


def field_table(m, reg, fields, lay=None):
    show_parts = any(f.get("chip") for f in fields)
    show_unit = any(f.get("unit") for f in fields)
    show_reset = any(f.get("reset") is not None for f in fields)
    extra = [(show_parts, "Parts", 14), (show_unit, "Unit", 10), (show_reset, "Reset value", 10)]
    extra = [(h, w) for on, h, w in extra if on]
    head = ["Bits", "Field", "Access"] + [h for h, _ in extra] + ["Evidence", "Description"]
    widths = [8, 24, 12] + [w for _, w in extra] + [10, 46 - sum(w for _, w in extra) // 2]
    out = table(head, field_rows(m, reg, fields, lay, show_parts, show_unit, show_reset),
                widths, "yt-fields")
    return out + array_table(reg, fields, lay)


def array_table(reg, fields, lay):
    """Where the elements of the array fields sit."""
    rows = []
    for f in sorted(fields, key=lambda f: -f["lsb"]):
        a = f.get("array")
        if not a:
            continue
        sym = M.fsym(reg, f, lay)
        for d in a["dims"]:
            rows.append([":field:`%s <%s.%s>`" % (M.fdisplay(f), reg["id"], sym[len(reg["id"]) + 1:]),
                         lit(d["var"]), d["first"], d["first"] + d["count"] - 1,
                         a["width"], a["lsb"], d["step"]])
    if not rows:
        return []
    out = [".. rubric:: Array fields", "",
           "The lowest bit of an element is the first bit plus the step times the distance of "
           "the index from its first value.", ""]
    return out + table(["Field", "Index", "First index", "Last index", "Bits per element",
                        "First bit", "Step in bits"], rows, [28, 12, 12, 12, 12, 12, 12])


def value_tables(m, reg, fields, lay=None):
    out = []
    for f in sorted(fields, key=lambda f: -f["lsb"]):
        if not f.get("values"):
            continue
        sym = M.fsym(reg, f, lay)
        fam = " (%s)" % FAMILY[f["chip"]] if f.get("chip") else ""
        out += target(vals_label(sym))
        out += [".. rubric:: Values of %s%s" % (M.fdisplay(f), fam), ""]
        rows = [[lit(str(v["value"])),
                 ".. _%s:\n\n%s" % (val_label(sym, v["name"]), lit(v["name"])),
                 v.get("desc", "")] for v in f["values"]]
        out += table(["Value", "Name", "Meaning"], rows, [12, 28, 60])
    return out


def source_rows(m, reg):
    rows = []
    sdk = reg.get("sdk") or {}
    if sdk.get("table"):
        sdk_cell = ":sdk:`%s`" % sdk["table"]
    elif sdk.get("literal"):
        sdk_cell = "`address constant <%s>`__" % sdk_url(m, sdk["src"][0], sdk["src"][1])
    else:
        sdk_cell = "none"
    lx = reg.get("linux") or {}
    rows.append([":reg:`%s`" % reg["id"], lit(lx["macro"]) if lx else "", linux_link(m, lx),
                 sdk_cell, "", ""])
    for lay, f in M.all_fields(reg):
        sym = M.fsym(reg, f, lay)
        lx = f.get("linux") or {}
        first = [":field:`%s <%s>`" % (sym[len(reg["id"]) + 1:], reg["id"] + "." + sym[len(reg["id"]) + 1:]),
                 lit(lx["macro"]) if lx.get("macro") else "", linux_link(m, lx)]
        fs = f.get("sdk") or {}
        names = fs.get("fields") or [""]
        for n in names:
            rows.append(first + [sdk_cell if n else "", lit(n) if n else "", fs.get("status", "")])
    return rows


def register_section(m, reg, guide_refs, mentions):
    out = target(reg_label(reg["id"]))
    out += [".. index:: single: %s (register)" % reg["id"], ""]
    out += heading(reg["id"] + M.index_text(reg), "-")
    out += ["**%s.** %s" % (reg["title"], reg["desc"].strip()), ""]
    rows = [("Address", lit(M.addr_formula(reg)))]
    for d in reg["dims"]:
        rows.append(("Index ``%s``" % d["var"], range_text(d["first"], d["count"])))
    if reg["dims"]:
        rows.append(("Address range", "%s to %s" % (lit(hexaddr(M.lowest_addr(reg))),
                                                    lit(hexaddr(M.highest_addr(reg))))))
    size = "%d bits" % (32 * reg["words"])
    if reg["words"] > 1:
        size += " in %d words; :ref:`word order <access-wide>`" % reg["words"]
    rows.append(("Size", size))
    rows.append(("Access", ACCESS[reg["access"]]))
    if reg.get("reset") is not None:
        rows.append(("Reset value", lit("0x%08x" % reg["reset"])))
    rows.append(("Evidence", evidence_link(reg)))
    c = "YT921X_%s%s" % (reg["id"], "(%s)" % ", ".join(d["var"] for d in reg["dims"]) if reg["dims"] else "")
    rs = "regs::%s(%s)" % (reg["id"].lower(), ", ".join(d["var"] for d in reg["dims"])) \
        if reg["dims"] else "regs::" + reg["id"]
    py = c[len("YT921X_"):]
    rows.append((":ref:`C name <bindings-c>`", lit(c)))
    rows.append((":ref:`Rust name <bindings-rust>`", lit(rs)))
    rows.append((":ref:`MicroPython name <bindings-micropython>`", lit(py)))
    out += facts(rows)

    fams = M.families(reg)
    for fam in fams:
        out += [".. yt-bitfield:: " + reg["id"]]
        if fam:
            out += ["   :family: " + fam]
        out += [""]
    fields = [f for f in reg["fields"] if not f.get("group")]
    groups = [f for f in reg["fields"] if f.get("group")]
    if fields:
        out += field_table(m, reg, fields)
        out += value_tables(m, reg, fields)
    if groups:
        out += [".. rubric:: Field groups", "",
                "A group is a mask that covers several fields of this register.", ""]
        out += field_table(m, reg, groups)
    for lay in reg["layouts"]:
        lf = [f for f in lay["fields"] if not (f.get("key_only") and reg["id"] != "ACL_KEY")]
        out += [".. rubric:: Layout %s: %s" % (lay["name"], lay["title"]), ""]
        types = ", ".join(lit(t) for t in lay["types"])
        out += ["Used when TYPE of the slot (:field:`ACL_KEY.TYPE`, values :enum:`acl_type`) is %s."
                % types, ""]
        out += [".. yt-bitfield:: " + reg["id"], "   :layout: " + lay["name"], ""]
        out += field_table(m, reg, lf, lay)
        out += value_tables(m, reg, lf, lay)

    refs = used_in(guide_refs.get(("reg", reg["id"]), []))
    refs += [":reg:`%s`" % other for other in mentions.get(reg["id"], [])]
    if refs:
        out += [".. rubric:: Referenced from", ""]
        out += ["* " + r for r in refs] + [""]
    out += [".. rubric:: Sources", ""]
    rows = source_rows(m, reg)
    out += table(["Item", "Linux name", "Linux source"], [r[:3] for r in rows],
                 [26, 54, 20], "yt-sources")
    out += table(["Item", "SDK table", "SDK field", "SDK comparison"],
                 [r[:1] + r[3:] for r in rows], [26, 26, 26, 22], "yt-sources")
    return out


def block_page(m, block, guide_refs, mentions):
    regs = m.block_regs(block["id"])
    out = target(blk_label(block["id"]))
    out += heading(block["title"], "=")
    out += [block["summary"], "",
            "The guide page :doc:`/%s/%s` explains how to use these registers." % (DOCROOT, block["guide"]),
            ""]
    rows = [[lit(hexaddr(r["address"])), ":reg:`%s`" % r["id"],
             "".join("[%s]" % d["var"] for d in r["dims"]) and lit(M.index_text(r)), r["title"]]
            for r in regs]
    out += table(["Address", "Register", "Index", "Purpose"], rows, [14, 28, 16, 42])
    for r in regs:
        out += register_section(m, r, guide_refs, mentions)
    return out


# -------------------------------------------------------------- other pages

def index_page(m):
    out = target("reference")
    out += heading("Register reference", "=")
    out += [
        "Every register this manual describes, grouped by function. Each register has its "
        "address, a bit diagram, a field table and the sources it was taken from. The fields in "
        "a diagram are links to their descriptions. :ref:`evidence` explains the Evidence column.",
        "",
        ".. toctree::", "   :maxdepth: 1", "",
    ]
    out += ["   " + b["id"] for b in m.blocks]
    out += ["   enums", "   counters", "   constants", "   parts", "   regions/index", ""]
    out += target("reference-map")
    out += heading("Address map", "-")
    out += ["Registers sit at 32-bit addresses that are multiples of four. The diagram shows the "
            "regions this manual has registers in; each box is a link to the complete register "
            "list of that region.", "",
            ".. yt-diagram:: address-map", "   :caption: Address regions of the YT921x", ""]
    rows = []
    for x in m.regions:
        n = sum(1 for r in m.regs if r["region"] == x["name"])
        nt = sum(1 for t in m.sdk["tables"] if sdk_region(m, t) is x)
        rows.append([lit(hexaddr(x["base"])), ":doc:`%s <regions/%s>`" % (x["name"], region_slug(x)),
                     x["title"], n, nt])
    out += table(["Base address", "Region", "Title", "Registers described", "Vendor SDK tables"],
                 rows, [14, 18, 40, 14, 14])
    out += target("reference-blocks")
    out += heading("Function blocks", "-")
    rows = [[":blk:`%s`" % b["id"], len(m.block_regs(b["id"])),
             ":doc:`/%s/%s`" % (DOCROOT, b["guide"])] for b in m.blocks]
    out += table(["Block", "Registers", "Guide page"], rows, [40, 20, 40])
    out += target("reference-all")
    out += heading("All registers by address", "-")
    rows = []
    for r in sorted(m.regs, key=lambda r: r["address"]):
        rows.append([lit(hexaddr(r["address"])), ":reg:`%s`" % r["id"],
                     lit(M.index_text(r)) if r["dims"] else "", 32 * r["words"],
                     ACCESS[r["access"]], ":blk:`%s`" % r["block"], r["title"]])
    out += table(["Address", "Register", "Index", "Bits", "Access", "Block", "Purpose"], rows,
                 [11, 20, 12, 6, 11, 18, 22])
    return out


def enums_page(m):
    out = target("reference-enums")
    out += heading("Shared value lists", "=")
    out += ["Value lists that more than one field uses. A field that has its own values lists "
            "them with its register.", ""]
    users = {}
    for r in m.regs:
        for lay, f in M.all_fields(r):
            if f.get("enum"):
                sym = M.fsym(r, f, lay)
                users.setdefault(f["enum"], []).append(
                    ":field:`%s.%s`" % (r["id"], sym[len(r["id"]) + 1:]))
    for e in m.enums.values():
        out += target(enum_label(e["name"]))
        out += [".. index:: single: %s (value list)" % e["name"], ""]
        out += heading("%s: %s" % (e["name"], e["title"]), "-")
        out += [e["desc"].strip(), ""]
        prefix = e["name"].upper()
        rows = [[lit(str(v["value"])),
                 ".. _%s:\n\n%s" % (enum_val_label(e["name"], v["name"]), lit(v["name"])),
                 lit("YT921X_%s_%s" % (prefix, v["name"])),
                 linux_link(m, v.get("linux")), v.get("desc", "")] for v in e["values"]]
        out += table(["Value", "Name", "C name", "Linux source", "Meaning"], rows, [8, 18, 30, 14, 30])
        if users.get(e["name"]):
            out += [".. rubric:: Used by", ""]
            out += ["* " + u for u in users[e["name"]]] + [""]
    return out


def counters_page(m, guide_refs):
    mib = m.byid["MIB_DATA"]
    out = target("reference-counters")
    out += heading("Counter list", "=")
    out += ["Each port has a block of counters that starts at :reg:`MIB_DATA`. A counter sits at "
            "the listed offset from the start of the block of its port: address = %s + offset. "
            "A counter of two words holds its low 32 bits at the offset and its high 32 bits four "
            "bytes higher. In the :ref:`bindings <bindings-naming>` the offset of a counter is named "
            "``YT921X_MIB_`` followed by the counter name (without the prefix in Rust and MicroPython). "
            ":doc:`/%s/mib` shows how to enable, read and clear the counters."
            % (lit(M.addr_formula(mib)), DOCROOT), ""]
    rows = []
    for c in m.counters:
        name = ".. _%s:\n\n.. index:: single: %s (counter)\n\n%s" % (
            counter_label(c["name"]), c["name"], lit(c["name"]))
        rows.append([lit("0x%02x" % c["offset"]), name, 32 * c["words"],
                     linux_link(m, c.get("linux")), c["desc"]])
    out += table(["Offset", "Counter", "Bits", "Linux source", "Counts"], rows,
                 [10, 30, 8, 16, 36])
    return out


def constants_page(m):
    out = target("reference-constants")
    out += heading("Constants", "=")
    out += ["Sizes and fixed values that the register descriptions rely on. In the "
            ":ref:`bindings <bindings-naming>` each constant is named ``YT921X_`` followed by "
            "its name in the table (without the prefix in Rust and MicroPython).", ""]
    rows = []
    for c in m.constants:
        name = ".. _%s:\n\n.. index:: single: %s (constant)\n\n%s" % (
            const_label(c["name"]), c["name"], lit(c["name"]))
        v = c["value"]
        rows.append([name, lit(str(v)), lit("0x%x" % v),
                     linux_link(m, c.get("linux")), c["desc"]])
    out += table(["Name", "Value", "Hexadecimal", "Linux source", "Meaning"], rows,
                 [26, 12, 14, 16, 32])
    return out


def parts_page(m):
    out = target("reference-parts")
    out += heading("Parts", "=")
    out += ["The members of the family and how software tells them apart. "
            ":ref:`bringup-identify` gives the procedure. The identification values come from "
            "the Linux driver; the YT9215SCH is not in its table and is expected to identify as "
            "the YT9215SC, which is unverified.", ""]
    rows = []
    for c in m.chips:
        name = ".. _%s:\n\n.. index:: single: %s (part)\n\n%s" % (chip_label(c["name"]), c["name"], c["name"])
        rows.append([name, {"yt9215": "YT9215", "yt9218": "YT9218"}[c["family"]],
                     lit("0x%04x" % c["major"]), lit(str(c["mode"])), lit(str(c["extmode"]))])
    out += table(["Part", "Register layout family", ":field:`CHIP_ID.MAJOR`",
                  ":field:`CHIP_MODE.MODE`", "Extended mode byte"], rows, [20, 20, 20, 20, 20])
    out += target("reference-parts-ports")
    out += heading("Port interfaces", "-")
    out += ["Ports 0 to 7 can have a built-in copper PHY, ports 8 and 9 an external interface, and "
            "port 10 is the built-in microcontroller. A port that a part does not have is not "
            "listed.", ""]
    rows = []
    for c in m.chips:
        for p in range(11):
            kinds = [p in c["phy"], p in c["xmii"], p in c["serdes"]]
            if p == 10:
                rows.append([":chip:`%s`" % c["name"], p, "no", "no", "no", "yes"])
            elif any(kinds):
                rows.append([":chip:`%s`" % c["name"], p] + ["yes" if k else "no" for k in kinds] + ["no"])
    out += table(["Part", "Port", "Built-in PHY", "xMII pins", "SerDes", "Internal CPU"], rows,
                 [20, 10, 18, 16, 16, 20])
    return out


def sdk_pages(m):
    pages = {}
    s = m.sdk["source"]
    regions = m.regions + [NO_ADDRESS]
    out = target("reference-sdk")
    out += heading("Address regions and vendor SDK tables", "=")
    out += [
        "The vendor SDK carries a machine-generated list of every register table of the chip: "
        "`%s <%s>`__ has the addresses and `%s <%s>`__ the field positions. It has names but no "
        "descriptions. The region pages list, region by region, the registers this manual "
        "describes next to all %d SDK tables, so that a driver writer can see what exists beyond "
        "the %d described registers. Field names on these pages are the SDK's own."
        % (os.path.basename(s["index"]), sdk_url(m, s["index"]),
           os.path.basename(s["struct"]), sdk_url(m, s["struct"]),
           len(m.sdk["tables"]), len(m.regs)), "",
        ".. toctree::", "   :maxdepth: 1", "",
    ]
    out += ["   " + region_slug(x) for x in regions]
    out += [""]
    rows = []
    for t in sorted(m.sdk["tables"], key=lambda t: (t["address"], t["name"])):
        for reg in t.get("registers") or [""]:
            rows.append([lit(hexaddr(t["address"])) if t["address"] else "none",
                         ":sdk:`%s`" % t["name"], t["entries"],
                         t["bytes"], ":reg:`%s`" % reg if reg else ""])
    out += heading("All SDK tables by address", "-")
    out += table(["Address", "SDK table", "Entries", "Bytes per entry", "Described as"], rows,
                 [14, 36, 10, 14, 26])
    pages["reference/regions/index"] = out
    for x in regions:
        tabs = sorted((t for t in m.sdk["tables"] if sdk_region(m, t) is x),
                      key=lambda t: (t["address"], t["name"]))
        regs = sorted((r for r in m.regs if x is not NO_ADDRESS and r["region"] == x["name"]),
                      key=lambda r: r["address"])
        out = heading("%s: %s" % (x["name"], x["title"]), "=")
        if x is NO_ADDRESS:
            out += ["The SDK defines these tables without an address. They are the layouts of one "
                    "key slot of the ACL, which this manual describes as the layouts of "
                    ":reg:`ACL_KEY` and :reg:`ACL_MASK`. See :ref:`reference-sdk` for what this "
                    "list is.", ""]
        else:
            out += ["Region from address %s. See :ref:`reference-map` for the other regions."
                    % lit(hexaddr(x["base"])), ""]
            out += heading("Registers described in this manual", "-")
            if regs:
                rows = [[lit(hexaddr(r["address"])), ":reg:`%s`" % r["id"],
                         lit(M.index_text(r)) if r["dims"] else "", ":blk:`%s`" % r["block"],
                         r["title"]] for r in regs]
                out += table(["Address", "Register", "Index", "Block", "Purpose"], rows,
                             [14, 24, 14, 22, 26])
            else:
                out += ["None.", ""]
            out += heading("Vendor SDK tables", "-")
            if not tabs:
                out += ["The SDK register list has no table in this region.", ""]
            else:
                out += ["See :ref:`reference-sdk` for what this list is.", ""]
        for t in tabs:
            out += target(sdk_label(t["name"]))
            out += [".. index:: single: %s (vendor SDK table)" % t["name"], ""]
            out += heading(t["name"], "~" if x is not NO_ADDRESS else "-")
            rows = []
            if t["address"]:
                rows.append(("Address", lit(hexaddr(t["address"]))))
            rows += [("Entries", str(t["entries"])),
                     ("Bytes per entry", str(t["bytes"])),
                     ("Address step", str(t["stride"])),
                     ("Source", "`%s:%d <%s>`__" % (os.path.basename(s["index"]), t["index_line"],
                                                    sdk_url(m, s["index"], t["index_line"])))]
            for reg in t.get("registers") or []:
                rows.append(("Described as", ":reg:`%s`" % reg))
            out += facts(rows)
            if t.get("fields"):
                rows = [[M.bits_text(f["lsb"], f["width"]), lit(f["name"]),
                         "`%s:%d <%s>`__" % (os.path.basename(s["struct"]), f["line"],
                                             sdk_url(m, s["struct"], f["line"]))]
                        for f in sorted(t["fields"], key=lambda f: -f["lsb"])]
                out += table(["Bits", "SDK field", "Source"], rows, [16, 54, 30])
            else:
                out += ["The SDK lists no fields for this table.", ""]
        pages[region_page(x)] = out
    return pages


# --------------------------------------------------------------------- main

def pages(m, docs_dir):
    guide_refs = scan_guide(docs_dir)
    mentions = reg_mentions(m)
    out = {"reference/index": index_page(m),
           "reference/enums": enums_page(m),
           "reference/counters": counters_page(m, guide_refs),
           "reference/constants": constants_page(m),
           "reference/parts": parts_page(m)}
    for b in m.blocks:
        out["reference/" + b["id"]] = block_page(m, b, guide_refs, mentions)
    out.update(sdk_pages(m))
    return out


def generate(m, docs_dir):
    """Write the generated pages; files that did not change are left alone."""
    targets(m)
    wanted = set()
    for name, lines in pages(m, docs_dir).items():
        path = os.path.join(docs_dir, name + ".rst")
        wanted.add(os.path.abspath(path))
        text = ".. Generated by tools/gen_docs.py from yt921x.yaml. Do not edit.\n\n" + \
            "\n".join(lines).rstrip() + "\n"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        old = None
        if os.path.exists(path):
            with open(path) as f:
                old = f.read()
        if old != text:
            with open(path, "w") as f:
                f.write(text)
    for path in glob.glob(os.path.join(docs_dir, "reference", "**", "*.rst"), recursive=True):
        if os.path.abspath(path) not in wanted:
            os.remove(path)
