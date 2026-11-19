# SPDX-License-Identifier: Apache-2.0
"""Checks that every generated file agrees with yt921x.yaml.

Each output is read back with a tool that did not write it: the SVD files
with xmllint (schema) and an independent XML expander, the SystemRDL files with the
systemrdl-compiler, the C header with gcc, and the Python module by import.
"""
import itertools
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, os.path.join(ROOT, "bindings", "micropython"))

import model  # noqa: E402
from model import addr_of, all_fields, corner_indices, elems, fsym  # noqa: E402

M = model.Model()


def expected_addresses():
    """(register id, index tuple, address) for the corner elements."""
    for r in M.regs:
        for idx in corner_indices(r):
            yield r, idx, addr_of(r, idx)


class UpToDate(unittest.TestCase):
    def test_generated_files_match_yaml(self):
        res = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "generate.py"),
                              "--check"], capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)


class PythonModule(unittest.TestCase):
    def test_addresses_and_fields(self):
        import yt921x_regs as R
        for r, idx, addr in expected_addresses():
            sym = getattr(R, r["id"])
            self.assertEqual(sym(*idx) if r["dims"] else sym, addr, r["id"])
        n = 0
        for r in M.regs:
            for lay, f in all_fields(r):
                fs = fsym(r, f, lay)
                word = f["lsb"] // 32
                if f.get("array"):
                    for i, lsb, w in elems(f):
                        self.assertEqual(getattr(R, fs + "_S")(*i), lsb - 32 * word, fs)
                        self.assertEqual(getattr(R, fs + "_M")(*i),
                                         ((1 << w) - 1) << (lsb - 32 * word), fs)
                        n += 1
                elif (f["lsb"] + f["width"] - 1) // 32 == word:
                    self.assertEqual(getattr(R, fs + "_M"),
                                     ((1 << f["width"]) - 1) << (f["lsb"] - 32 * word), fs)
                    n += 1
                else:
                    self.assertEqual(getattr(R, fs + "_LSB"), f["lsb"], fs)
                    n += 1
        self.assertGreater(n, 700)


@unittest.skipUnless(shutil.which("gcc"), "gcc not installed")
class CHeader(unittest.TestCase):
    def test_static_asserts(self):
        lines = ['#include "yt921x_regs.h"']
        chk = "_Static_assert(%s == %s, \"%s\");"
        for r, idx, addr in expected_addresses():
            sym = "YT921X_" + r["id"]
            if r["dims"]:
                sym += "(%s)" % ", ".join(str(i) for i in idx)
            lines.append(chk % (sym, "0x%xu" % addr, r["id"]))
        for r in M.regs:
            for lay, f in all_fields(r):
                fs = "YT921X_" + fsym(r, f, lay)
                word = f["lsb"] // 32
                if f.get("array"):
                    for i, lsb, w in elems(f):
                        args = ", ".join(str(x) for x in i)
                        lines.append(chk % ("%s_M(%s)" % (fs, args),
                                            "0x%xu" % (((1 << w) - 1) << (lsb - 32 * word)), fs))
                elif (f["lsb"] + f["width"] - 1) // 32 == word:
                    lines.append(chk % (fs + "_M", "0x%xu" % (
                        ((1 << f["width"]) - 1) << (f["lsb"] - 32 * word)), fs))
                    lines.append(chk % (fs + "_S", "%du" % (f["lsb"] - 32 * word), fs))
                for v in f.get("values", []):
                    lines.append(chk % ("%s_%s" % (fs, v["name"]), "%du" % v["value"], fs))
        for c in M.counters:
            lines.append(chk % ("YT921X_MIB_" + c["name"], "0x%xu" % c["offset"], c["name"]))
        lines.append("int main(void) { return 0; }")
        with tempfile.TemporaryDirectory() as tmp:
            src = os.path.join(tmp, "asserts.c")
            with open(src, "w") as f:
                f.write("\n".join(lines) + "\n")
            res = subprocess.run(
                ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
                 "-I", os.path.join(ROOT, "bindings", "c"), "-fsyntax-only", src],
                capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr[:2000])
        self.assertGreater(len(lines), 1000)


class Svd(unittest.TestCase):
    @unittest.skipUnless(shutil.which("xmllint"), "xmllint not installed")
    def test_schema(self):
        for fam in ("yt9215", "yt9218"):
            res = subprocess.run(
                ["xmllint", "--noout", "--schema",
                 os.path.join(ROOT, "tools", "schema", "CMSIS-SVD.xsd"),
                 os.path.join(ROOT, "svd", fam + ".svd")], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0, res.stderr[:2000])

    @staticmethod
    def expand(path):
        """Expand an SVD file to {address: (path name, {field: (lsb, width)})}."""
        import xml.etree.ElementTree as ET

        def num(el, tag, default=0):
            t = el.findtext(tag)
            return int(t, 0) if t is not None else default

        out = {}

        def walk(el, base, prefix):
            for child in el:
                if child.tag not in ("register", "cluster"):
                    continue
                dim, inc = num(child, "dim", 1), num(child, "dimIncrement")
                name = prefix + child.findtext("name")
                for i in range(dim):
                    addr = base + num(child, "addressOffset") + i * inc
                    if child.tag == "cluster":
                        walk(child, addr, name + ".")
                        continue
                    fields = {}
                    for f in child.iterfind("fields/field"):
                        if f.find("dim") is None:
                            fields[f.findtext("name")] = (num(f, "bitOffset"), num(f, "bitWidth"))
                    out.setdefault(addr, (name, fields))

        for per in ET.parse(path).getroot().iterfind("peripherals/peripheral"):
            walk(per.find("registers"), num(per, "baseAddress"), per.findtext("name") + ".")
        return out

    def test_addresses_and_fields(self):
        at = self.expand(os.path.join(ROOT, "svd", "yt9215.svd"))
        for r, idx, addr in expected_addresses():
            if r["id"] == "MIB_DATA":
                continue
            self.assertIn(addr, at, "%s%s" % (r["id"], idx))
            name, got = at[addr]
            self.assertIn(r["id"], name)
            for f in model.visible_fields(r, "yt9215"):
                if f.get("array") or f["lsb"] // 32 or (f["lsb"] + f["width"] - 1) // 32:
                    continue
                self.assertEqual(got.get(f["name"]), (f["lsb"], f["width"]),
                                 "%s.%s" % (r["id"], f["name"]))
        mib = M.byid["MIB_DATA"]
        for c in M.counters:
            self.assertIn(addr_of(mib, (10,)) + c["offset"], at, c["name"])


class Rdl(unittest.TestCase):
    def test_compiles_and_addresses_match(self):
        try:
            from systemrdl import RDLCompiler
            from systemrdl.node import RegNode
        except ImportError:
            self.skipTest("systemrdl-compiler not installed")
        for fam in ("yt9215", "yt9218"):
            c = RDLCompiler()
            c.compile_file(os.path.join(ROOT, "rdl", fam + ".rdl"))
            root = c.elaborate()
            starts = {}
            for node in root.descendants(unroll=True):
                if isinstance(node, RegNode):
                    starts[node.absolute_address] = node
            for r, idx, addr in expected_addresses():
                if r["id"] == "MIB_DATA":
                    continue
                self.assertIn(addr, starts, "%s %s%s" % (fam, r["id"], idx))
                node = starts[addr]
                got = {f.inst_name: (f.lsb, f.width) for f in node.fields()}
                for f in model.visible_fields(r, fam):
                    if f.get("array"):
                        continue
                    self.assertEqual(got.get(f["name"]), (f["lsb"], f["width"]),
                                     "%s.%s" % (r["id"], f["name"]))


class ModelSanity(unittest.TestCase):
    def test_no_overlapping_fields(self):
        for r in M.regs:
            for fam in model.families(r):
                groups = [model.visible_fields(r, fam)]
                groups += [groups[0] + model.visible_fields(r, fam, l) for l in r["layouts"]]
                for fields in groups:
                    seen = {}
                    for f in fields:
                        self.assertLessEqual(f["lsb"] + f["width"], 32 * r["words"], r["id"])
                        spans = ([(l, w) for _, l, w in elems(f)] if f.get("array")
                                 else [(f["lsb"], f["width"])])
                        for lsb, w in spans:
                            for b in range(lsb, lsb + w):
                                self.assertNotIn(b, seen, "%s bit %d: %s and %s" % (
                                    r["id"], b, f["name"], seen.get(b)))
                                seen[b] = f["name"]

    def test_no_overlapping_registers(self):
        spans = []
        for r in M.regs:
            for idx in itertools.product(*[range(d["first"], d["first"] + d["count"])
                                           for d in r["dims"]]):
                a = addr_of(r, idx)
                spans.append((a, a + 4 * r["words"], r["id"]))
                if len(spans) > 200000:
                    break
        spans.sort()
        for (a0, e0, n0), (a1, e1, n1) in zip(spans, spans[1:]):
            if n0 == "MIB_DATA" or n1 == "MIB_DATA":
                continue
            self.assertLessEqual(e0, a1, "%s overlaps %s at 0x%x" % (n0, n1, a1))

    def test_every_item_is_described(self):
        for r in M.regs:
            self.assertTrue(r["title"] and r["desc"], r["id"])
            for lay, f in all_fields(r):
                self.assertTrue(f["desc"], "%s.%s" % (r["id"], f["name"]))
                for v in f.get("values", []):
                    self.assertTrue(v["desc"], "%s.%s.%s" % (r["id"], f["name"], v["name"]))


class ReferenceNames(unittest.TestCase):
    """Every binding name printed in the reference exists in the bindings."""

    def test_names_exist(self):
        import re

        import gen_docs

        def read(*parts):
            with open(os.path.join(ROOT, "bindings", *parts)) as f:
                return f.read()

        c_names = set(re.findall(r"#define (YT921X_\w+)", read("c", "yt921x_regs.h")))
        rust = read("rust", "src", "regs.rs")
        rs_names = set(re.findall(r"pub (?:const fn|const|mod|fn) (\w+)", rust))
        py_names = set(dir(__import__("yt921x_regs")))
        text = "\n".join("\n".join(lines) for lines in
                         gen_docs.pages(M, os.path.join(ROOT, "docs")).values())
        # The source tables print Linux names, which are not binding names.
        text = re.sub(r":class: yt-sources\n(\n|   .*\n)*", "", text)
        # The row "Linux name" of a register prints a Linux name too.
        linux = {r["linux"]["macro"].split("(")[0] for r in M.regs if r.get("linux")}
        seen = {"c": 0, "rust": 0, "py": 0}
        for name in re.findall(r"``(YT921X_\w*[^\W_])(?!\w)", text):  # not the bare prefixes
            if name in linux and name not in c_names:
                continue
            self.assertIn(name, c_names)
            seen["c"] += 1
        for name in re.findall(r"``regs::(\w+)", text):
            self.assertIn(name, rs_names)
            seen["rust"] += 1
        for name in re.findall(r"MicroPython name <bindings-micropython>`\W+``(\w+)", text):
            self.assertIn(name, py_names)
            seen["py"] += 1
        for kind, count in seen.items():
            self.assertGreater(count, 90, kind)


if __name__ == "__main__":
    unittest.main()
