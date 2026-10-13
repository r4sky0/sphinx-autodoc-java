"""Map compiler-produced comment tokens to portable docutils nodes."""

from __future__ import annotations

import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging

LOGGER = logging.getLogger(__name__)
TABLE_TAGS = {"table", "caption", "thead", "tbody", "tfoot", "tr", "th", "td"}
TABLE_SECTIONS = {"thead", "tbody", "tfoot"}
# Presentation attributes are dropped; Sphinx themes style native tables.
ATTRIBUTES = {
    "pre": {"lang"},
    "table": {"class", "summary", "border"},
    "th": {"colspan", "rowspan", "scope"},
    "td": {"colspan", "rowspan", "scope"},
}
# Unsupported block elements still end the current paragraph.
BLOCK_LEVEL = {
    *(f"h{level}" for level in range(1, 7)),
    *("address", "article", "aside", "center", "dd", "div", "dl", "dt", "figcaption"),
    *("figure", "footer", "header", "hr", "main", "nav", "section"),
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


def comment(part: ET.Element, location, quiet: bool = False) -> list[nodes.Node]:
    """Renders comment tokens; ``quiet`` skips warnings for repeated renderings."""
    root = nodes.container()
    stack: list[tuple[str, nodes.Element]] = [("root", root)]
    block_tags = {"p", "ul", "ol", "li", "pre", "blockquote"}
    supported = block_tags | TABLE_TAGS | {"code", "b", "strong", "i", "em", "a", "br"}
    head_rows: set[int] = set()
    header_cells: set[int] = set()
    # Paragraphs from <p> or ended by a block element take no further inline content.
    sealed: set[int] = set()

    def warn(message):
        if not quiet:
            LOGGER.warning(message, location=location, type="java", subtype="html")

    def close(tag):
        for i in range(len(stack) - 1, 0, -1):
            if stack[i][0] == tag:
                del stack[i:]
                return

    def break_paragraph():
        close("p")
        current = stack[-1][1]
        if current.children and isinstance(current.children[-1], nodes.paragraph):
            sealed.add(id(current.children[-1]))

    def unwind(tags):
        """Closes elements above the innermost open tag in ``tags`` and returns it."""
        for i in range(len(stack) - 1, 0, -1):
            if stack[i][0] in tags:
                del stack[i + 1 :]
                return stack[i][0]
        return None

    def span(attrs, name):
        value = attrs.get(name, "1")
        if not value.strip().isdigit() or int(value) < 1:
            warn(
                f"Invalid {name} {value!r} on a Javadoc table cell; use a positive integer."
            )
            return 1
        return min(int(value), SPAN_LIMITS[name])

    def table_start(name, attrs):
        """Opens table structure; HTML's optional end tags close implicitly."""
        close("p")
        if name == "table":
            node = nodes.table(classes=["colwidths-auto", "java-table"])
            stack[-1][1].append(node)
            return node
        table = next((node for tag, node in reversed(stack) if tag == "table"), None)
        if table is None:
            warn(f"Javadoc <{name}> needs a surrounding <table>.")
            return None
        if name == "caption" or name in TABLE_SECTIONS:
            unwind({"table"})
        if name == "caption":
            if table.children and isinstance(table.children[0], nodes.title):
                warn("Javadoc <table> has more than one <caption>.")
                return None
            node = nodes.title()
            table.insert(0, node)
            return node
        if name in TABLE_SECTIONS:
            return table
        section = unwind({"table", *TABLE_SECTIONS, "tr"})
        if name == "tr" or section != "tr":
            unwind({"table", *TABLE_SECTIONS})
            row = nodes.row()
            table += row
            if stack[-1][0] == "thead":
                head_rows.add(id(row))
            if name == "tr":
                return row
            stack.append(("tr", row))
        node = nodes.entry()
        if (cols := span(attrs, "colspan")) > 1:
            node["morecols"] = cols - 1
        if (rows := span(attrs, "rowspan")) > 1:
            node["morerows"] = rows - 1
        if name == "th":
            header_cells.add(id(node))
        stack[-1][1].append(node)
        return node

    def table_finish(table):
        """Lays out collected rows on a grid as a docutils table with a header."""
        rows = [child for child in table.children if isinstance(child, nodes.row)]
        if not rows:
            warn("Javadoc <table> has no rows; use <tr> with <td> or <th> cells.")
            table.parent.remove(table)
            return
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
        columns = max(c for _, c in occupied) + 1
        for r, row in enumerate(rows):
            row.extend(nodes.entry() for c in range(columns) if (r, c) not in occupied)
        head = 0
        while head < len(rows) and (
            id(rows[head]) in head_rows
            or rows[head].children
            and all(id(entry) in header_cells for entry in rows[head].children)
        ):
            head += 1
        if head == len(rows):
            head = 0
        group = nodes.tgroup(cols=columns)
        # Text and LaTeX builders size columns from colwidth; HTML sizes automatically.
        group.extend(nodes.colspec(colwidth=widths.get(c, 1)) for c in range(columns))
        if head:
            group += nodes.thead("", *rows[:head])
        group += nodes.tbody("", *rows[head:])
        table.children = [c for c in table.children if isinstance(c, nodes.title)]
        table += group
        # Themes style tables differently, but all leave a plain wrapper alone, so the
        # wrapper is what scrolls a wide table.
        wrapper = nodes.container(classes=["java-table-wrapper"])
        table.parent.replace(table, wrapper)
        wrapper += table

    def append(node):
        current = stack[-1][1]
        if isinstance(current, nodes.literal_block):
            current += nodes.Text(node.astext())
            return
        if isinstance(current, (nodes.table, nodes.row)):
            if node.astext().strip():
                warn("Javadoc table content must be inside <td> or <th>.")
            return
        if isinstance(
            current, (nodes.container, nodes.list_item, nodes.block_quote, nodes.entry)
        ):
            last = current.children[-1] if current.children else None
            if not isinstance(last, nodes.paragraph) or id(last) in sealed:
                # Whitespace between blocks does not start a paragraph.
                if isinstance(node, nodes.Text) and not node.astext().strip():
                    return
                current += nodes.paragraph()
            current.children[-1] += node
        elif isinstance(current, (nodes.bullet_list, nodes.enumerated_list)):
            if node.astext().strip():
                warn("Javadoc list content must be inside <li>.")
        else:
            current += node

    def tokens(items):
        for token in items:
            tag = token.tag
            if tag in {"text", "literal", "code"}:
                value = token.text or ""
                if (
                    not any(isinstance(n, nodes.literal_block) for _, n in stack)
                    and tag == "text"
                ):
                    value = re.sub(r"\s+", " ", value)
                if tag == "code":
                    append(nodes.literal("", value))
                elif tag == "literal":
                    # Verbatim text such as {@literal} and {@value} keeps straight quotes.
                    append(nodes.inline("", value, support_smartquotes=False))
                else:
                    append(nodes.Text(value))
            elif tag == "link":
                label = comment(token, location, quiet)
                inline = [child for p in label for child in p.children]
                append(reference(token, inline))
            elif tag == "start":
                name = token.get("name", "").lower()
                attrs = {a.get("name"): a.text or "" for a in token}
                if name not in supported:
                    warn(
                        f"Unsupported Javadoc HTML <{name}>; use paragraphs, lists, tables, emphasis, links or <pre>."
                    )
                    if name in BLOCK_LEVEL:
                        break_paragraph()
                    continue
                if any(k not in ATTRIBUTES.get(name, {"href"}) for k in attrs):
                    warn(
                        f"Javadoc HTML attributes on <{name}> are not supported except href on links, lang on pre and table structure; move layout and assets to a guide."
                    )
                if name == "br":
                    append(
                        nodes.Text("\n")
                        if isinstance(stack[-1][1], nodes.literal_block)
                        else nodes.line()
                    )
                    continue
                if any(isinstance(n, nodes.literal_block) for _, n in stack):
                    if name != "code":
                        warn(
                            f"Unsupported nested HTML <{name}> inside <pre>; use escaped code."
                        )
                    continue
                if name in TABLE_TAGS:
                    node = table_start(name, attrs)
                    if node is not None and token.get("closed") != "true":
                        stack.append((name, node))
                    continue
                if name in block_tags:
                    if isinstance(stack[-1][1], (nodes.table, nodes.row)):
                        warn(
                            f"Javadoc <{name}> in a table must be inside <td> or <th>."
                        )
                        continue
                    close("p")
                    if name == "li":
                        for open_tag, _ in reversed(stack):
                            if open_tag in {"ul", "ol"}:
                                break
                            if open_tag == "li":
                                close("li")
                                break
                    if name == "p":
                        node = nodes.paragraph()
                        sealed.add(id(node))
                    elif name == "ul":
                        node = nodes.bullet_list()
                    elif name == "ol":
                        node = nodes.enumerated_list(enumtype="arabic", start=1)
                    elif name == "li":
                        node = nodes.list_item()
                    elif name == "pre":
                        node = nodes.literal_block(
                            "", "", language=attrs.get("lang", "java")
                        )
                    else:
                        node = nodes.block_quote()
                    if name == "li" and not isinstance(
                        stack[-1][1], (nodes.bullet_list, nodes.enumerated_list)
                    ):
                        warn("Javadoc <li> needs a surrounding <ul> or <ol>.")
                        continue
                    stack[-1][1].append(node)
                else:
                    if name in {"b", "strong"}:
                        node = nodes.strong()
                    elif name in {"i", "em"}:
                        node = nodes.emphasis()
                    elif name == "code":
                        node = nodes.literal()
                    else:
                        href = attrs.get("href", "")
                        if urlsplit(href).scheme not in {"https", "http", "mailto"}:
                            warn(
                                f"Unsupported Javadoc HTML link {href!r}; use a Java {{@link}} or an absolute https URL."
                            )
                            node = nodes.inline()
                        else:
                            node = nodes.reference("", "", refuri=href)
                    append(node)
                if token.get("closed") != "true":
                    stack.append((name, node))
            elif tag == "end":
                name = token.get("name", "").lower()
                if name in BLOCK_LEVEL:
                    break_paragraph()
                close(name)
            else:
                warn(f"Unsupported XML comment token {tag}; regenerate the model.")

    tokens(part)
    for table in reversed(list(root.findall(nodes.table))):
        table_finish(table)

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
    # Javadoc prints comment text as written; Sphinx would curl quotes and join dots.
    for node in root.children:
        node["support_smartquotes"] = False
    return root.children


# Sphinx's deprecated directive labels its text with these classes.
CHANGE_CLASSES = ["versionmodified", "deprecated"]
# Javadoc's default first sentence ends at a period followed by whitespace.
SENTENCE_END = re.compile(r"\.(?=\s|$)")


def deprecated(element: ET.Element) -> bool:
    # Only annotations directly on the declaration, not on parameters or in values.
    return element.find("doc/part[@kind='deprecated']") is not None or (
        element.find("sig/r[@target='java.lang.Deprecated']") is not None
    )


def summary(element: ET.Element, location) -> list[nodes.Node]:
    """Returns the first sentence of the description as inline nodes."""
    body = element.find("doc/part[@kind='body']")
    content = comment(body, location, quiet=True) if body is not None else []
    if not content or not isinstance(content[0], nodes.paragraph):
        return []
    done = False

    def truncate(node):
        nonlocal done
        if isinstance(node, nodes.Text):
            text = node.astext()
            if match := SENTENCE_END.search(text):
                done = True
                text = text[: match.end()]
            return nodes.Text(text)
        copy = node.copy()
        for child in node.children:
            copy += truncate(child)
            if done:
                break
        return copy

    sentence = truncate(content[0])
    # The full description reports unresolved links; the summary repeats them quietly.
    for reference in sentence.findall(addnodes.pending_xref):
        reference["java:quiet"] = True
    return sentence.children


def quiet_reference(app, env, node, contnode):
    """Sphinx missing-reference handler: summary links fall back to their text."""
    return contnode if node.get("java:quiet") else None


FIELD_TITLES = {
    "specifiedBy": "Specified by",
    "overrides": "Overrides",
    "param": "Parameters",
    "typeparam": "Type parameters",
    "return": "Returns",
    "throws": "Throws",
    "see": "See also",
    "since": "Since",
    # The standard doclet's headings for the JDK's custom note tags.
    "apiNote": "API Note",
    "implSpec": "Implementation Requirements",
    "implNote": "Implementation Note",
}


def field(kind: str, items) -> nodes.field:
    """One field per kind; labelled items read "name – description", as in Sphinx."""
    bodies = []
    for label, content in items:
        content = list(content)
        if label:
            label = nodes.strong("", "", label)
            if content and isinstance(content[0], nodes.paragraph):
                content[0].insert(0, [label, nodes.Text(" – ")])
            else:
                content.insert(0, nodes.paragraph("", "", label))
        bodies.append(content)
    if len(bodies) == 1:
        body = nodes.field_body("", *bodies[0])
    else:
        body = nodes.field_body(
            "", nodes.bullet_list("", *(nodes.list_item("", *b) for b in bodies))
        )
    return nodes.field("", nodes.field_name("", FIELD_TITLES.get(kind, kind)), body)


def documentation(element: ET.Element, location) -> list[nodes.Node]:
    result: list[nodes.Node] = []
    fields = nodes.field_list()
    notice = None
    fields_by_kind: dict[str, list] = {}
    if deprecated(element):
        # The structure of Sphinx's deprecated directive, which themes style.
        notice = addnodes.versionmodified(type="deprecated", version="")
        result.append(notice)
    for part in element.findall("doc/part"):
        content = comment(part, location)
        kind = part.get("kind")
        if kind in {"specifiedBy", "overrides"}:
            # Ancestors outside the documented API stay text, as in summaries.
            for node in content:
                for xref in node.findall(addnodes.pending_xref):
                    xref["java:quiet"] = True
        if kind == "body":
            result.extend(content)
        elif kind == "deprecated":
            notice.extend(content)
        else:
            label = part.get("label") and nodes.Text(part.get("label"))
            if label and part.get("target"):
                # A documented exception links to its type, as in signatures.
                label = reference(part, [label])
                label["refwarn"] = False
            fields_by_kind.setdefault(kind, []).append((label, content))
    for kind, items in fields_by_kind.items():
        fields += field(kind, items)
    if notice is not None:
        if notice.children and isinstance(notice[0], nodes.paragraph):
            label = "Deprecated: "
            notice[0].insert(0, nodes.inline("", label, classes=CHANGE_CLASSES))
        else:
            label = nodes.inline("", "Deprecated.", classes=CHANGE_CLASSES)
            notice.insert(0, nodes.paragraph("", "", label))
    if fields.children:
        result.append(fields)
    return result
