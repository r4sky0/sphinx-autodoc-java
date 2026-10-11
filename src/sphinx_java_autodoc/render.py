"""Map compiler-produced comment tokens to portable docutils nodes.

Comment tokens are serialized to an internal HTML fragment, with Javadoc tokens as
placeholder elements, and parsed by an HTML5 parser. The parser repairs omitted end
tags and misnesting like browsers do; the resulting tree maps to docutils nodes.
"""

from __future__ import annotations

import html
import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from docutils import nodes
from justhtml import JustHTML
from sphinx import addnodes
from sphinx.util import logging

LOGGER = logging.getLogger(__name__)
# Javadoc tokens travel through the HTML parser as these elements.
PLACEHOLDER = "java-token"
NAME = re.compile(r"[a-z][a-z0-9-]*\Z")
ATTRIBUTE = re.compile(r"[a-z][a-z0-9:_.-]*\Z")
VOID = {
    "area",
    "base",
    "br",
    "col",
    "embed",
    "hr",
    "img",
    "input",
    "link",
    "meta",
    "wbr",
}
INLINE = {
    "b": nodes.strong,
    "strong": nodes.strong,
    "i": nodes.emphasis,
    "em": nodes.emphasis,
    "code": nodes.literal,
}
TABLE_PARTS = {"caption", "thead", "tbody", "tfoot", "tr", "th", "td"}
SUPPORTED = {"p", "ul", "ol", "li", "pre", "blockquote", "table", "a", "br"}
SUPPORTED |= INLINE.keys() | TABLE_PARTS
# Unsupported block elements keep their content as separate paragraphs.
BLOCK_LEVEL = {
    *(f"h{level}" for level in range(1, 7)),
    *("address", "article", "aside", "center", "dd", "div", "dl", "dt", "figcaption"),
    *("figure", "footer", "header", "hr", "main", "nav", "section"),
}
# Presentation attributes are dropped; Sphinx themes style native tables.
ATTRIBUTES = {
    "a": {"href"},
    "pre": {"lang"},
    "table": {"class", "summary", "border"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan", "scope"},
}
# HTML limits for cell spans.
SPAN_LIMITS = {"colspan": 1000, "rowspan": 65534}


def reference(token: ET.Element, children: list[nodes.Node]) -> nodes.Node:
    node = addnodes.pending_xref(
        "",
        refdomain="java",
        reftype=token.get("role", "obj"),
        reftarget=token.get("target", ""),
        refexplicit=True,
        refwarn=True,
    )
    node["java:external"] = dict(token.attrib)
    if token.get("plain") == "true":
        node.extend(children)
    else:
        node += nodes.literal("", "", *children)
    return node


def comment(part: ET.Element, location) -> list[nodes.Node]:
    def warn(message):
        LOGGER.warning(message, location=location, type="java", subtype="html")

    def unsupported(name):
        warn(
            f"Unsupported Javadoc HTML <{name}>; use paragraphs, lists, tables, emphasis, links or <pre>."
        )

    tokens: list[ET.Element] = []

    def serialize() -> str:
        markup = []
        for token in part:
            tag = token.tag
            if tag == "text":
                markup.append(html.escape(token.text or "", quote=False))
            elif tag in {"literal", "code", "link"}:
                markup.append(f'<{PLACEHOLDER} data-i="{len(tokens)}"></{PLACEHOLDER}>')
                tokens.append(token)
            elif tag in {"start", "end"}:
                name = token.get("name", "").lower()
                if name == PLACEHOLDER or not NAME.match(name):
                    unsupported(name)
                elif tag == "end":
                    markup.append(f"</{name}>")
                else:
                    attrs = "".join(
                        f' {key}="{html.escape(attr.text or "")}"'
                        for attr in token
                        if ATTRIBUTE.match(key := (attr.get("name") or "").lower())
                    )
                    markup.append(f"<{name}{attrs}>")
                    # A self-closed <p/> or <td/> is empty, unlike in HTML parsing.
                    if token.get("closed") == "true" and name not in VOID:
                        markup.append(f"</{name}>")
            else:
                warn(f"Unsupported XML comment token {tag}; regenerate the model.")
        return "".join(markup)

    def check_attributes(element):
        if any(key not in ATTRIBUTES.get(element.name, set()) for key in element.attrs):
            warn(
                f"Javadoc HTML attributes on <{element.name}> are not supported except href on links, lang on pre and table structure; move layout and assets to a guide."
            )

    def token_node(element) -> nodes.Node:
        token = tokens[int(element.attrs["data-i"])]
        if token.tag == "code":
            return nodes.literal("", token.text or "")
        if token.tag == "literal":
            # Verbatim text such as {@literal} and {@value} keeps straight quotes.
            return nodes.inline("", token.text or "", support_smartquotes=False)
        label = comment(token, location)
        return reference(token, [child for p in label for child in p.children])

    def inline(element) -> list[nodes.Node]:
        if element.name == "#text":
            return [nodes.Text(re.sub(r"\s+", " ", element.data))]
        if element.name == PLACEHOLDER:
            return [token_node(element)]
        if element.name == "br":
            return [nodes.line()]
        check_attributes(element)
        children = [node for child in element.children for node in inline(child)]
        if element.name in INLINE:
            return [INLINE[element.name]("", "", *children)]
        if element.name == "a":
            href = element.attrs.get("href", "")
            if urlsplit(href).scheme in {"https", "http", "mailto"}:
                return [nodes.reference("", "", *children, refuri=href)]
            warn(
                f"Unsupported Javadoc HTML link {href!r}; use a Java {{@link}} or an absolute https URL."
            )
        elif element.name in SUPPORTED:
            warn(f"Javadoc <{element.name}> cannot appear inside inline text.")
        else:
            unsupported(element.name)
        return children

    def preformatted(element) -> str:
        text = []
        for child in element.children:
            if child.name == "#text":
                text.append(child.data)
            elif child.name == PLACEHOLDER:
                text.append(token_node(child).astext())
            elif child.name == "br":
                text.append("\n")
            else:
                if child.name != "code":
                    warn(
                        f"Unsupported nested HTML <{child.name}> inside <pre>; use escaped code."
                    )
                text.append(preformatted(child))
        return "".join(text)

    def blocks(element) -> list[nodes.Node]:
        """Converts children, collecting inline runs into paragraphs."""
        result: list[nodes.Node] = []
        run: list[nodes.Node] = []

        def flush():
            if run:
                result.append(nodes.paragraph("", "", *run))
                run.clear()

        for child in element.children:
            block = block_node(child)
            if block is None:
                run.extend(inline(child))
            else:
                flush()
                result.extend(block)
        flush()
        return result

    def block_node(element) -> list[nodes.Node] | None:
        name = element.name
        if name not in {"p", "ul", "ol", "li", "pre", "blockquote", "table"}:
            if name in BLOCK_LEVEL:
                unsupported(name)
                return blocks(element)
            return None
        check_attributes(element)
        if name == "p":
            return [nodes.paragraph("", "", *inline_children(element))]
        if name == "blockquote":
            return [nodes.block_quote("", *blocks(element))]
        if name == "pre":
            language = element.attrs.get("lang", "java")
            text = preformatted(element)
            return [nodes.literal_block(text, text, language=language)]
        if name == "li":
            warn("Javadoc <li> needs a surrounding <ul> or <ol>.")
            return blocks(element)
        if name == "table":
            return table(element)
        items = (
            nodes.bullet_list()
            if name == "ul"
            else nodes.enumerated_list(enumtype="arabic", start=1)
        )
        for child in element.children:
            if child.name == "li":
                check_attributes(child)
                items += nodes.list_item("", *blocks(child))
            elif nodes.Element("", *inline(child)).astext().strip():
                warn("Javadoc list content must be inside <li>.")
        return [items]

    def inline_children(element) -> list[nodes.Node]:
        return [node for child in element.children for node in inline(child)]

    def span(cell, name):
        value = cell.attrs.get(name, "1")
        if not value.strip().isdigit() or int(value) < 1:
            warn(
                f"Invalid {name} {value!r} on a Javadoc table cell; use a positive integer."
            )
            return 1
        return min(int(value), SPAN_LIMITS[name])

    def table(element) -> list[nodes.Node]:
        node = nodes.table(classes=["colwidths-auto", "java-table"])
        rows: list[nodes.row] = []
        header: list[bool] = []
        for child in element.children:
            if child.name == "caption":
                if node.children:
                    warn("Javadoc <table> has more than one <caption>.")
                else:
                    node += nodes.title("", "", *inline_children(child))
            elif child.name in {"thead", "tbody", "tfoot"}:
                check_attributes(child)
                for tr in child.children:
                    if tr.name != "tr":
                        continue
                    check_attributes(tr)
                    row = nodes.row()
                    only_th = True
                    for cell in tr.children:
                        if cell.name not in {"td", "th"}:
                            continue
                        check_attributes(cell)
                        entry = nodes.entry("", *blocks(cell))
                        if (cols := span(cell, "colspan")) > 1:
                            entry["morecols"] = cols - 1
                        if (rowspan := span(cell, "rowspan")) > 1:
                            entry["morerows"] = rowspan - 1
                        only_th &= cell.name == "th"
                        row += entry
                    rows.append(row)
                    header.append(
                        child.name == "thead" or bool(row.children) and only_th
                    )
        if not rows:
            warn("Javadoc <table> has no rows; use <tr> with <td> or <th> cells.")
            return []
        layout(node, rows, header)
        return [node]

    document = JustHTML(serialize(), fragment=True, sanitize=False, collect_errors=True)
    for error in document.errors:
        warn(f"Malformed Javadoc HTML: {error.message}.")
    root = nodes.container("", *blocks(document.root))

    def split_lines(element):
        lines = [element.copy()]
        for child in element.children:
            if isinstance(child, nodes.line):
                lines.append(element.copy())
            elif isinstance(child, nodes.Text):
                lines[-1] += child
            else:
                fragments = split_lines(child)
                lines[-1] += fragments[0]
                for fragment in fragments[1:]:
                    lines.append(element.copy())
                    lines[-1] += fragment
        return lines

    for p in list(root.findall(nodes.paragraph)):
        if any(p.findall(nodes.line)):
            p.replace_self(
                nodes.line_block(
                    "", *[nodes.line("", "", *line.children) for line in split_lines(p)]
                )
            )
        elif not p.astext().strip():
            p.parent.remove(p)
    return root.children


def layout(table: nodes.table, rows: list[nodes.row], header: list[bool]) -> None:
    """Places rows on a grid, pads short rows and splits off leading header rows."""
    occupied: set[tuple[int, int]] = set()
    widths: dict[int, int] = {}
    for r, row in enumerate(rows):
        c = 0
        for entry in row.children:
            while (r, c) in occupied:
                c += 1
            if not entry.get("morecols"):
                # The text builder adds quotes or asterisks around inline markup.
                markup = entry.findall(
                    lambda n: isinstance(
                        n, (nodes.literal, nodes.emphasis, nodes.strong)
                    )
                )
                width = max(map(len, entry.astext().splitlines() or [""]))
                width += 2 * len(list(markup))
                widths[c] = max(widths.get(c, 1), min(width, 40))
            entry["morerows"] = min(entry.get("morerows", 0), len(rows) - r - 1)
            for dr in range(entry.get("morerows", 0) + 1):
                for dc in range(entry.get("morecols", 0) + 1):
                    occupied.add((r + dr, c + dc))
            c += entry.get("morecols", 0) + 1
    columns = max((c for _, c in occupied), default=0) + 1
    for r, row in enumerate(rows):
        row.extend(nodes.entry() for c in range(columns) if (r, c) not in occupied)
    head = 0
    while head < len(rows) and header[head]:
        head += 1
    if head == len(rows):
        head = 0
    group = nodes.tgroup(cols=columns)
    # Text and LaTeX builders size columns from colwidth; HTML sizes automatically.
    group.extend(nodes.colspec(colwidth=widths.get(c, 1)) for c in range(columns))
    if head:
        group += nodes.thead("", *rows[:head])
    group += nodes.tbody("", *rows[head:])
    table += group


def documentation(element: ET.Element, location) -> list[nodes.Node]:
    result: list[nodes.Node] = []
    fields = nodes.field_list()
    for part in element.findall("doc/part"):
        content = comment(part, location)
        kind = part.get("kind")
        if kind == "body":
            result.extend(content)
        else:
            titles = {
                "param": "Parameter",
                "typeparam": "Type parameter",
                "return": "Returns",
                "throws": "Throws",
                "see": "See also",
                "since": "Since",
                "deprecated": "Deprecated",
            }
            label = titles.get(kind, str(kind)) + (
                " " + part.get("label") if part.get("label") else ""
            )
            field = nodes.field(
                "", nodes.field_name("", label), nodes.field_body("", *content)
            )
            fields += field
    if fields.children:
        result.append(fields)
    return result
