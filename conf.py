"""Sphinx configuration of the whole repository; Read the Docs builds this."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "research", "yt9215-registers", "tools"))

project = "Budget PoE to USB-C adapter"
author = "Budget PoE adapter contributors"
copyright = "Budget PoE adapter contributors"

extensions = ["myst_parser", "sphinx_design", "yt921x_sphinx"]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
root_doc = "index"
exclude_patterns = [
    "_build",
    ".venv",
    "**/target",
    "**/__pycache__",
    "research/yt9215-registers/bindings",
    "research/yt9215-registers/tools",
]

nitpicky = True
primary_domain = None
myst_heading_anchors = 4

html_theme = "furo"
html_title = project
html_static_path = []
