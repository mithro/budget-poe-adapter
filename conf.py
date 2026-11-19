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
rst_prolog = """
.. |ds| replace:: :download:`YT9215SCH datasheet </datasheets/motorcomm/YT9215SCH_Datasheet_V1.03_2025-02-10.pdf>`
"""
primary_domain = None
myst_heading_anchors = 4

html_theme = "furo"
html_title = project
html_static_path = []


REPO_URL = "https://github.com/mithro/budget-poe-adapter/tree/main/"


def link_directories(app, docname, source):
    """A Markdown link to a directory has no page to point at; link it on GitHub."""
    import re

    path = os.fspath(app.env.doc2path(docname))
    if not path.endswith(".md"):
        return
    base = os.path.dirname(path)

    def fix(m):
        target = os.path.normpath(os.path.join(base, m.group(1)))
        if not os.path.isdir(target):
            return m.group(0)
        return "](%s%s)" % (REPO_URL, os.path.relpath(target, os.fspath(app.srcdir)).replace(os.sep, "/"))

    source[0] = re.sub(r"\]\((?!https?:)([^)#\s]+/)\)", fix, source[0])


def setup(app):
    app.connect("source-read", link_directories)
