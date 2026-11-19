#!/usr/bin/env python3
"""Turn yt921x.yaml into every generated file of this directory.

  generate.py            write the register description files and bindings
  generate.py --check    fail if a generated file differs from what is on disk
  generate.py --docs DIR also write the documentation pages and diagrams to DIR

The files written by the first form are committed, so that the bindings can be
used without running anything. The documentation pages are generated during
the Sphinx build.
"""
import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_c  # noqa: E402
import gen_py  # noqa: E402
import gen_rust  # noqa: E402
import model  # noqa: E402


def outputs(m):
    """Path (relative to the register directory) -> file content."""
    out = {
        "bindings/c/yt921x_regs.h": gen_c.generate(m),
        "bindings/rust/src/regs.rs": gen_rust.generate(m),
        "bindings/micropython/yt921x_regs.py": gen_py.generate(m),
    }
    try:
        import gen_svd
        import gen_rdl
    except ImportError:
        return out
    for family in ("yt9215", "yt9218"):
        out["svd/%s.svd" % family] = gen_svd.generate(m, family)
        out["rdl/%s.rdl" % family] = gen_rdl.generate(m, family)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--docs")
    args = ap.parse_args()
    m = model.Model()
    stale = []
    for rel, text in outputs(m).items():
        path = os.path.join(model.ROOT, rel)
        old = None
        if os.path.exists(path):
            with open(path) as f:
                old = f.read()
        if old == text:
            continue
        if args.check:
            stale.append(rel)
            continue
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            f.write(text)
        print("wrote", rel)
    if stale:
        sys.exit("out of date, run tools/generate.py: " + ", ".join(stale))
    if args.docs:
        import gen_docs
        gen_docs.generate(m, args.docs)


if __name__ == "__main__":
    main()
