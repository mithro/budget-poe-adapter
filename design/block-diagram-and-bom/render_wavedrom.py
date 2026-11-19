#!/usr/bin/env python3
"""Render every WaveDrom source of this folder to an SVG with a white background.

Needs the Python package wavedrom (pip install wavedrom). Run it from any folder.
"""
import pathlib
import re

import wavedrom

HERE = pathlib.Path(__file__).resolve().parent

for source in sorted(HERE.glob("*.json")):
    svg = wavedrom.render(source.read_text(encoding="utf-8")).tostring()
    # A white sheet behind the drawing keeps it readable on a dark page.
    svg = re.sub(r"(<svg[^>]*>)", r'\1<rect width="100%" height="100%" fill="#ffffff"/>', svg, count=1)
    source.with_suffix(".svg").write_text(svg, encoding="utf-8")
    print(source.with_suffix(".svg").name)
