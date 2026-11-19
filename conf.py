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
    "README.md",
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
# Lets an HTML <img> in Markdown carry a width; Sphinx then copies the image file.
myst_enable_extensions = ["html_image"]

html_theme = "furo"
html_title = project
html_show_sourcelink = False
html_static_path = []


REPO_URL = "https://github.com/mithro/budget-poe-adapter/tree/main/"


ANCHOR_RE = r'<a id="([^"]+)"></a>'
LINK_TEXT = r"\[((?:[^\[\]]|\[[^\]]*\])*)\]"


def link_directories(app, docname, source):
    """Markdown links that GitHub resolves and MyST does not.

    A link to a directory has no page to point at, so it goes to GitHub. A link to an
    ``<a id>`` anchor becomes an HTML link, because MyST only knows heading anchors.
    """
    import re

    path = os.fspath(app.env.doc2path(docname))
    if not path.endswith(".md"):
        return
    base = os.path.dirname(path)
    text = source[0]

    def directory(m):
        target = os.path.normpath(os.path.join(base, m.group(1)))
        if not os.path.isdir(target):
            return m.group(0)
        return "](%s%s)" % (REPO_URL, os.path.relpath(target, os.fspath(app.srcdir)).replace(os.sep, "/"))

    text = re.sub(r"\]\((?!https?:)([^)#\s]+/)\)", directory, text)

    def root_readme(m):
        # index.md includes the root README, so a link to that README goes to the index.
        target = os.path.normpath(os.path.join(base, m.group(1)))
        if target != os.path.join(os.fspath(app.srcdir), "README.md"):
            return m.group(0)
        return "](%sindex.md%s)" % (m.group(1)[:-len("README.md")], m.group(2) or "")

    text = re.sub(r"\]\(((?:\.\./)*README\.md)(#[\w.-]+)?\)", root_readme, text)
    ids = set(re.findall(ANCHOR_RE, text))

    def local(m):
        if m.group(2) not in ids:
            return m.group(0)
        return '<a href="#%s">%s</a>' % (m.group(2), m.group(1))

    text = re.sub(LINK_TEXT + r"\(#([\w.-]+)\)", local, text)

    def other(m):
        target = os.path.join(base, m.group(2))
        if not os.path.isfile(target):
            return m.group(0)
        with open(target, encoding="utf-8") as f:
            if m.group(3) not in re.findall(ANCHOR_RE, f.read()):
                return m.group(0)
        return '<a href="%s.html#%s">%s</a>' % (m.group(2)[:-3], m.group(3), m.group(1))

    text = re.sub(LINK_TEXT + r"\((?!https?:)([^)#\s]+\.md)#([\w.-]+)\)", other, text)
    source[0] = text


# Furo opens the sidebar at its top; this brings the entry of the current page into view.
SCROLL_SIDEBAR_JS = """
document.addEventListener("DOMContentLoaded", function () {
  var box = document.querySelector(".sidebar-scroll");
  var here = document.querySelector(".sidebar-tree .current-page > a");
  if (!box || !here) return;
  var b = box.getBoundingClientRect(), h = here.getBoundingClientRect();
  if (h.bottom > b.bottom || h.top < b.top) box.scrollTo({top: box.scrollTop + h.top - b.top - b.height / 3, behavior: "instant"});
});
"""


def setup(app):
    app.add_js_file(None, body=SCROLL_SIDEBAR_JS)
    app.connect("source-read", link_directories)
