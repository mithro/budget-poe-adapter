"""Sphinx extension of the YT921x documentation.

Roles, each a link to the generated reference:

  :reg:`PORT_CTRL`          register
  :field:`PORT_CTRL.SPEED`  field (``:field:`SPEED <PORT_CTRL.SPEED>``` sets the text)
  :blk:`port`               function block, shown by its title
  :enum:`speed`             shared value list
  :counter:`RX_BROADCAST`   port counter
  :const:`EDATA_LEN`        constant
  :chip:`YT9215S`           part
  :sdk:`PORT_CTRL`          vendor SDK table
  :val:`FDB_OP.OP.ADD`      value of a field or of a shared value list
  :lx:`yt921x_chip_reset`   function, file or ``file:line`` of the Linux driver
  :ev:`inferred`            evidence word, linked to its definition

Directives:

  .. yt-bitfield:: REGISTER   WaveDrom diagram of a register (options ``family``, ``layout``)
  .. wavedrom::               WaveDrom diagram of the JSON source in the content (option ``caption``)
  .. yt-diagram:: name        a diagram of ``guide_diagrams.py`` (option ``caption``)

The reference pages are written into the source tree when the build starts,
so one ``sphinx-build`` run is all a build needs. A name that does not exist
is an error, and so is a link without a target when ``nitpicky`` is set.
"""
import json
import os
import sys

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains import Domain
from sphinx.util.docutils import SphinxDirective, SphinxRole
from sphinx.util.nodes import make_refnode, split_explicit_title

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_docs  # noqa: E402
import guide_diagrams  # noqa: E402
import model as M  # noqa: E402
import wavedrom_diagrams  # noqa: E402

_state = {}


def state():
    if not _state:
        m = M.Model()
        _state.update(model=m, targets=gen_docs.targets(m), fields=gen_docs.field_syms(m),
                      blocks={b["id"]: b for b in m.blocks},
                      fieldobj={M.fsym(r, f, lay): f for r in m.regs for lay, f in M.all_fields(r)},
                      layouts={(r["id"], lay["name"]): lay for r in m.regs for lay in r["layouts"]})
    return _state


def resolve(kind, name):
    """(label, default text, literal?) of a role target, or None."""
    s = state()
    m = s["model"]
    if kind == "reg" and name in m.byid:
        return gen_docs.reg_label(name), name, True
    if kind == "field" and name in s["fields"]:
        return gen_docs.field_label(s["fields"][name]), name, True
    if kind == "val":
        owner, _, vname = name.rpartition(".")
        if owner in m.enums:
            if any(v["name"] == vname for v in m.enums[owner]["values"]):
                return gen_docs.enum_val_label(owner, vname), vname, True
        elif owner in s["fields"]:
            sym = s["fields"][owner]
            f = s["fieldobj"][sym]
            if f.get("enum") and any(v["name"] == vname for v in m.enums[f["enum"]]["values"]):
                return gen_docs.enum_val_label(f["enum"], vname), vname, True
            if any(v["name"] == vname for v in f.get("values") or []):
                return gen_docs.val_label(sym, vname), vname, True
        return None
    if kind == "blk" and name in s["blocks"]:
        return gen_docs.blk_label(name), s["blocks"][name]["title"], False
    if kind == "enum" and name in m.enums:
        return gen_docs.enum_label(name), name, True
    if kind == "counter" and any(c["name"] == name for c in m.counters):
        return gen_docs.counter_label(name), name, True
    if kind == "const" and any(c["name"] == name for c in m.constants):
        return gen_docs.const_label(name), name, True
    if kind == "chip" and (any(c["name"] == name for c in m.chips)
                           or any(n == name for n, _ in gen_docs.ASSUMED_PARTS)):
        return gen_docs.chip_label(name), name, False
    if kind == "sdk" and gen_docs.sdk_label(name) in s["targets"]:
        return gen_docs.sdk_label(name), name, True
    return None


class YtRole(SphinxRole):
    def __init__(self, kind):
        super().__init__()
        self.kind = kind

    def run(self):
        explicit, title, name = split_explicit_title(self.text)
        found = resolve(self.kind, name)
        if found is None:
            msg = self.inliner.reporter.error(
                "unknown YT921x %s: %s" % (self.kind, name), line=self.lineno)
            prb = self.inliner.problematic(self.rawtext, self.rawtext, msg)
            return [prb], [msg]
        label, text, literal = found
        if explicit:
            text = title
        ref = addnodes.pending_xref("", refdomain="yt", reftype="ref", reftarget=label,
                                    refexplicit=True, refwarn=True, refdoc=self.env.docname)
        ref += nodes.literal(text, text) if literal else nodes.Text(text)
        return [ref], []


class LinuxRole(SphinxRole):
    """``:lx:`yt921x_chip_reset``` links a function of the Linux driver, ``:lx:`chip.h```
    a file and ``:lx:`chip.h:22``` a line, all at the commit the description was taken from."""

    def run(self):
        explicit, title, name = split_explicit_title(self.text)
        m = state()["model"]
        funcs = m.d["linux_functions"]
        paths = m.sources["linux"]["paths"]
        fn, _, line = name.partition(":")
        if name in funcs:
            src, text = funcs[name], name + "()"
        elif fn in paths and (not line or line.isdigit()):
            src, text = [fn, int(line) if line else None], name
        else:
            msg = self.inliner.reporter.error(
                "unknown Linux driver function or file: " + name, line=self.lineno)
            return [self.inliner.problematic(self.rawtext, self.rawtext, msg)], [msg]
        uri = gen_docs.linux_url(m, src)
        ref = nodes.reference("", "", refuri=uri, classes=["external"])
        ref += nodes.literal(text, title if explicit else text)
        return [ref], []


class EvidenceRole(SphinxRole):
    """``:ev:`inferred``` links an evidence word to the list that defines it."""

    def run(self):
        explicit, title, name = split_explicit_title(self.text)
        if name not in gen_docs.EVIDENCE_WORDS:
            msg = self.inliner.reporter.error("unknown evidence word: " + name, line=self.lineno)
            return [self.inliner.problematic(self.rawtext, self.rawtext, msg)], [msg]
        ref = addnodes.pending_xref("", refdomain="yt", reftype="ref",
                                    reftarget=gen_docs.EVIDENCE_WORDS[name],
                                    refexplicit=True, refwarn=True, refdoc=self.env.docname)
        ref += nodes.Text(title if explicit else name)
        return [ref], []


class YtDomain(Domain):
    """Resolves the roles above against the labels of the standard domain."""
    name = "yt"
    label = "YT921x"

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        docname, labelid = env.domains.standard_domain.anonlabels.get(target, ("", ""))
        if not docname:
            return None
        return make_refnode(builder, fromdocname, docname, labelid, contnode)

    def resolve_any_xref(self, env, fromdocname, builder, target, node, contnode):
        return []

    def merge_domaindata(self, docnames, otherdata):
        pass


class Links:
    """Builds the links inside a diagram of the current page."""

    def __init__(self, directive):
        self.env = directive.env
        self.model = state()["model"]

    def page(self, page, anchor=None):
        """Link to a page of the documentation, by its name inside docs/."""
        uri = self.env.app.builder.get_relative_uri(self.env.docname, gen_docs.DOCROOT + "/" + page)
        return uri + ("#" + anchor if anchor else "")

    def label(self, label):
        """Link to a label of the generated reference."""
        return self.page(state()["targets"][label], gen_docs.html_id(label))

    def reg(self, reg_id):
        return self.label(gen_docs.reg_label(reg_id))

    def field(self, name):
        return self.label(gen_docs.field_label(state()["fields"][name]))


def figure(svg, caption, link=None, classes=()):
    html = '<div class="%s">%s</div>' % (" ".join(("yt-scroll",) + tuple(classes)), svg)
    fig = nodes.figure("", nodes.raw("", html, format="html"), classes=["yt-figure"])
    if caption:
        cap = nodes.caption(caption, "")
        if link:
            head, name, tail = caption.partition(link[0])
            cap += nodes.Text(head)
            cap += nodes.reference("", name, refuri=link[1], classes=["internal"])
            cap += nodes.Text(tail)
        else:
            cap += nodes.Text(caption)
        fig += cap
    return fig


class Bitfield(SphinxDirective):
    required_arguments = 1
    option_spec = {"family": directives.unchanged, "layout": directives.unchanged}

    def run(self):
        s = state()
        reg = s["model"].byid.get(self.arguments[0])
        if reg is None:
            raise self.error("unknown register " + self.arguments[0])
        layout = None
        caption = "Bits of %s" % reg["id"]
        if self.options.get("layout"):
            layout = s["layouts"].get((reg["id"], self.options["layout"]))
            if layout is None:
                raise self.error("unknown layout " + self.options["layout"])
            caption += " with layout %s" % layout["name"]
        family = self.options.get("family")
        if family:
            caption += " on the " + gen_docs.FAMILY[family]
        ln = Links(self)
        words = gen_docs.register_diagram(s["model"], reg, family, layout)
        svg = ""
        try:
            for i, (source, names) in enumerate(words):
                label = caption
                if len(words) > 1:
                    top = 32 * (len(words) - i) - 1
                    label += ", bits %d to %d" % (top, top - 31)
                links = [(ln.label(target), tip) for target, tip in names]
                svg += wavedrom_diagrams.render(source, label, links)
        except wavedrom_diagrams.RenderError as err:
            raise self.error(str(err))
        return [figure(svg, caption, (reg["id"], ln.reg(reg["id"])), ["yt-wavedrom"])]


class Wavedrom(SphinxDirective):
    """``.. wavedrom::`` draws the WaveDrom JSON source in its content."""
    has_content = True
    option_spec = {"caption": directives.unchanged}

    def run(self):
        try:
            source = json.loads("\n".join(self.content))
        except ValueError as err:
            raise self.error("the WaveDrom source is not JSON: %s" % err)
        caption = self.options.get("caption")
        try:
            svg = wavedrom_diagrams.render(source, caption or "WaveDrom diagram")
        except wavedrom_diagrams.RenderError as err:
            raise self.error(str(err))
        return [figure(svg, caption, classes=["yt-wavedrom"])]


class Diagram(SphinxDirective):
    required_arguments = 1
    option_spec = {"caption": directives.unchanged}

    def run(self):
        fn = guide_diagrams.DIAGRAMS.get(self.arguments[0])
        if fn is None:
            raise self.error("unknown diagram " + self.arguments[0])
        return [figure(fn(Links(self)).render(), self.options.get("caption"))]


def config_inited(app, config):
    docs = os.path.join(app.srcdir, gen_docs.DOCROOT)
    gen_docs.generate(state()["model"], docs)
    config.html_static_path.append(os.path.join(docs, "_static"))


def break_names(app, doctree, docname):
    """Let a long name in a table cell break after an underscore, not inside a word."""
    if app.builder.format != "html":
        return
    for entry in doctree.findall(nodes.entry):
        for text in list(entry.findall(nodes.Text)):
            value = text.astext()
            if "_" not in value.strip("_") or len(value) < 12 or " " in value:
                continue
            parts = value.split("_")
            new = []
            for i, part in enumerate(parts):
                new.append(nodes.Text(part + ("_" if i < len(parts) - 1 else "")))
                if i < len(parts) - 1:
                    new.append(nodes.raw("", "<wbr>", format="html"))
            text.parent.replace(text, [n for n in new if n.astext()])


def setup(app):
    app.add_domain(YtDomain)
    for kind in ("reg", "field", "blk", "enum", "counter", "const", "chip", "sdk", "val"):
        app.add_role(kind, YtRole(kind))
    app.add_role("lx", LinuxRole())
    app.add_role("ev", EvidenceRole())
    app.add_directive("yt-bitfield", Bitfield)
    app.add_directive("wavedrom", Wavedrom)
    app.add_directive("yt-diagram", Diagram)
    app.add_css_file("yt921x.css")
    app.connect("config-inited", config_inited)
    app.connect("doctree-resolved", break_names)
    return {"parallel_read_safe": True, "parallel_write_safe": True}
