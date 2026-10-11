from __future__ import annotations

from html.parser import HTMLParser
import re
import xml.etree.ElementTree as ET

from docutils import nodes
import pytest
from test_integration import build, element

from sphinx_java_autodoc import render as render_module
from sphinx_java_autodoc.extractor import extract, read_model, run
from sphinx_java_autodoc.render import comment

TABLE = """package demo;

/**
 * Pattern tokens.
 * <table class="striped">
 *  <caption>Pattern Tokens</caption>
 *  <thead>
 *  <tr><th scope="col">character</th><th scope="col">duration element</th></tr>
 *  </thead>
 *  <tbody>
 *  <tr><td>y</td><td>years</td></tr>
 *  <tr><td>{@code 'text'}</td><td>arbitrary <em>text</em> content</td></tr>
 *  </tbody>
 * </table>
 * <table border="1">
 *  <caption>Examples</caption>
 *  <tr>
 *   <th>input</th>
 *   <th>output</th>
 *  <tr>
 *   <td>{@code null}
 *   <td>{@link Object}
 * </table>
 * After the tables.
 */
public class Tables {}
"""


def cells(table):
    return [
        [re.sub(r"\s+", " ", entry.astext()).strip() for entry in row.children]
        for row in table.findall(nodes.row)
    ]


@pytest.fixture
def warnings(monkeypatch):
    messages = []
    monkeypatch.setattr(
        render_module.LOGGER, "warning", lambda message, **_: messages.append(message)
    )
    return messages


def render(markup):
    part = ET.fromstring(f"<part>{markup}</part>")
    return nodes.container("", *comment(part, None))


def start(name, closed=False, **attrs):
    children = "".join(f'<attr name="{k}">{v}</attr>' for k, v in attrs.items())
    flag = ' closed="true"' if closed else ""
    return f'<start name="{name}"{flag}>{children}</start>'


def end(name):
    return f'<end name="{name}"/>'


def test_tables_become_native_tables_with_headers_spans_and_optional_end_tags(
    warnings,
):
    markup = (
        "<text>Intro</text>"
        + start("table", **{"class": "striped", "summary": "s", "border": "1"})
        + start("caption")
        + "<text>Caption </text><code>text</code>"
        + end("caption")
        + start("tr")
        + start("th", scope="col")
        + "<text>A</text>"
        + start("th", colspan="2")
        + "<text>B</text>"
        + start("tr")
        + start("td", rowspan="2")
        + "<text>tall</text>"
        + start("td")
        + start("p")
        + "<text>para</text>"
        + end("p")
        + start("ul")
        + start("li")
        + "<text>item</text>"
        + end("ul")
        + end("td")
        + start("td")
        + "<text>  wide\n  text </text>"
        + start("tr")
        + start("td")
        + "<text>short</text>"
        + end("table")
        + "<text>After</text>"
    )
    result = render(markup)
    assert warnings == []
    assert [type(child) for child in result.children] == [
        nodes.paragraph,
        nodes.table,
        nodes.paragraph,
    ]
    table = result.children[1]
    assert table.children[0].astext() == "Caption text"
    assert isinstance(table.children[0][1], nodes.literal)
    tgroup = table.children[1]
    assert tgroup["cols"] == 3
    assert len(list(tgroup.findall(nodes.colspec))) == 3
    assert cells(next(tgroup.findall(nodes.thead))) == [["A", "B"]]
    assert cells(next(tgroup.findall(nodes.tbody))) == [
        ["tall", "para item", "wide text"],
        ["short", ""],
    ]
    head = next(tgroup.findall(nodes.thead))
    assert head.children[0].children[1]["morecols"] == 1
    body = next(tgroup.findall(nodes.tbody))
    assert body.children[0].children[0]["morerows"] == 1
    assert next(result.findall(nodes.bullet_list)).parent.parent is body.children[0]


def test_table_without_header_rows_and_nested_tables(warnings):
    inner = (
        start("table") + start("tr") + start("td") + "<text>inner</text>" + end("table")
    )
    markup = (
        start("table")
        + start("tr")
        + start("th")
        + "<text>row header</text>"
        + start("td")
        + inner
        + end("tr")
        + start("tr")
        + start("th")
        + "<text>second</text>"
        + start("td")
        + "<text>value</text>"
        + end("table")
    )
    result = render(markup)
    assert warnings == []
    outer, nested = list(result.findall(nodes.table))
    assert not list(outer.children[0].findall(nodes.thead))
    assert cells(nested) == [["inner"]]
    assert nested.parent.parent.parent.parent.parent is outer


@pytest.mark.parametrize(
    ("markup", "message"),
    [
        (
            start("table", style="width: 50%")
            + start("tr")
            + start("td")
            + end("table"),
            "attributes on <table>",
        ),
        (
            start("table") + start("tr") + start("td", colspan="many") + end("table"),
            "Invalid colspan",
        ),
        (start("table") + end("table"), "<table> has no rows"),
    ],
)
def test_invalid_table_markup_warns(warnings, markup, message):
    render(markup)
    assert any(message in warning for warning in warnings), warnings


def test_misplaced_table_markup_is_repaired_like_browsers(warnings):
    stray = render(start("tr") + start("td") + "<text>stray</text>")
    assert not list(stray.findall(nodes.table))
    assert stray.astext() == "stray"
    loose = render(
        start("table")
        + "<text>loose</text>"
        + start("tr")
        + start("td")
        + "<text>cell</text>"
        + end("table")
    )
    assert [type(child) for child in loose.children] == [nodes.paragraph, nodes.table]
    assert loose.children[0].astext() == "loose"
    assert warnings == []


class TableCells(HTMLParser):
    """Collects standard doclet table cell text from description blocks."""

    def __init__(self):
        super().__init__()
        self.tables = []
        self.cell = None

    def finish_cell(self):
        if self.cell is not None:
            self.tables[-1][-1].append(re.sub(r"\s+", " ", self.cell).strip())
            self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag in {"tr", "td", "th"}:
            self.finish_cell()
        if tag == "table":
            self.tables.append([])
        elif tag == "tr":
            self.tables[-1].append([])
        elif tag in {"td", "th"}:
            self.cell = ""

    def handle_endtag(self, tag):
        if tag in {"td", "th", "tr", "table"}:
            self.finish_cell()

    def handle_data(self, data):
        if self.cell is not None:
            self.cell += data


def test_tables_match_standard_doclet_and_build_in_themes(tmp_path, warnings):
    source = tmp_path / "demo" / "Tables.java"
    source.parent.mkdir()
    source.write_text(TABLE)
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    assert not root.findall("diagnostic")
    part = element(root, "demo.Tables").find("doc/part")
    content = nodes.container("", *comment(part, None))
    assert warnings == []
    rendered = [cells(table) for table in content.findall(nodes.table)]

    standard = tmp_path / "standard"
    run(["javadoc", "-quiet", "-d", str(standard), str(source)])
    oracle = TableCells()
    oracle.feed((standard / "demo/Tables.html").read_text())
    assert rendered == oracle.tables[-2:]

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc']\n"
        f"java_model = {str(path)!r}\nnitpicky = True\n"
        "java_external_javadoc = {'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{module}/'}\n"
    )
    (docs / "index.rst").write_text(
        "Tables\n======\n\n.. java:autoclass:: demo.Tables\n"
    )
    for theme in ("alabaster", "classic"):
        output = tmp_path / theme
        build(docs, output, "-D", f"html_theme={theme}")
        html = (output / "index.html").read_text()
        assert html.count("<table") == 2
        assert "<caption>" in html and "<thead>" in html
        assert "Pattern Tokens" in html and "duration element" in html
    build(docs, tmp_path / "text", "-b", "text")
    text = (tmp_path / "text/index.txt").read_text()
    assert "duration element" in text and "arbitrary *text* content" in text
