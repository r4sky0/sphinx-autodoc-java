from __future__ import annotations

from html.parser import HTMLParser
import xml.etree.ElementTree as ET

from docutils import nodes
import pytest
from test_integration import build, project

from sphinx_java_autodoc.domain import anchor
from sphinx_java_autodoc.render import summary


class Page(HTMLParser):
    """Collects autosummary rows, section headings and local table of contents."""

    def __init__(self):
        super().__init__()
        self.tables, self.headings, self.toc = [], [], []
        self.mode = ""
        self.text = ""
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = (attrs.get("class") or "").split()
        if tag == "table" and "autosummary" in classes:
            self.tables.append([])
            self.mode = "table"
        elif self.mode == "table" and tag == "tr":
            self.tables[-1].append([])
        elif self.mode == "table" and tag == "td":
            self.mode, self.text = "td", ""
        elif self.mode == "td" and tag == "a":
            self.tables[-1][-1].append(attrs.get("href"))
        elif tag == "h2":
            self.mode, self.text = "h2", ""
        elif tag == "div" and "sphinxsidebarwrapper" in classes:
            self.depth = 1
        elif self.depth and tag == "div":
            self.depth += 1
        elif self.depth and tag == "a":
            self.mode, self.text = "toc", ""

    def handle_endtag(self, tag):
        if self.mode == "td" and tag == "td":
            self.tables[-1][-1].append(" ".join(self.text.split()))
            self.mode = "table"
        elif self.mode == "table" and tag == "table":
            self.mode = ""
        elif self.mode == "h2" and tag == "h2":
            self.headings.append(self.text.strip().rstrip("¶"))
            self.mode = ""
        elif self.mode == "toc" and tag == "a":
            self.toc.append(self.text.strip())
            self.mode = ""
        elif self.depth and tag == "div":
            self.depth -= 1

    def handle_data(self, data):
        if self.mode in {"td", "h2", "toc"}:
            self.text += data


def parse(path):
    page = Page()
    page.feed(path.read_text())
    return page


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("navigation")
    out = root / "html"
    sidebars = "html_sidebars = {'**': ['localtoc.html']}\n"
    build(project(root, extra=sidebars), out)
    return out


def test_type_pages_have_sections_with_summaries(site):
    page = parse(site / "api/type-demo.Widget.html")
    assert page.headings == ["Constructors", "Fields and constants", "Methods"]
    constructors, fields, methods = page.tables
    assert [row[1] for row in constructors] == ["Widget()", "Widget(String)"]
    by_name = {row[1]: row for row in methods}
    assert by_name["convert(int)"][0] == "#" + anchor("demo.Widget#convert(int)")
    assert by_name["convert(int)"][2] == "Converts a number to text."
    assert by_name["old()"][2] == "Deprecated. Old entry point."


def test_members_appear_in_the_page_toc_and_general_index(site):
    toc = parse(site / "api/type-demo.Widget.html").toc
    assert toc.index("Methods") < toc.index("convert(int)")
    assert "convert(String)" in toc
    index = (site / "genindex.html").read_text()
    assert "convert(int) (Java method in demo.Widget)" in index
    assert "demo (Java package)" in index


def test_package_pages_and_index_summarize_by_kind(site):
    package = parse(site / "api/package-demo.html")
    assert package.headings == [
        "Interfaces",
        "Classes",
        "Enums",
        "Records",
        "Annotation types",
    ]
    classes = {row[1]: row[2] for row in package.tables[1]}
    assert classes["Widget.Nested"] == "A nested type with a stable qualified name."
    assert classes["Widget"].startswith("A widget with a unified Java API")
    index = parse(site / "api/index.html")
    assert index.tables[0][0][1:] == ["demo", "Example API."]


def test_deprecated_members_use_the_standard_notice(site):
    html = (site / "api/type-demo.Widget.html").read_text()
    method = html[html.index('id="' + anchor("demo.Widget#old()") + '"') :]
    content = method[: method.index("</dd>")]
    notice = '<span class="versionmodified deprecated">Deprecated: </span>'
    assert notice in content
    assert content.index(notice) < content.index("Old entry point.")


@pytest.mark.parametrize(
    ("tokens", "expected"),
    [
        ("<text>Converts text. Then more.</text>", "Converts text."),
        (
            "<text>Uses </text><code>a.b</code><text> safely. More.</text>",
            "Uses a.b safely.",
        ),
        ("<text>No period</text>", "No period"),
        ('<start name="pre"/><text>code</text><end name="pre"/>', ""),
    ],
)
def test_summary_is_the_first_sentence(tokens, expected):
    element = ET.fromstring(
        f'<type><doc><part kind="body">{tokens}</part></doc></type>'
    )
    assert nodes.paragraph("", "", *summary(element, None)).astext() == expected
