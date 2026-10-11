"""Map compiler-produced comment tokens to portable docutils nodes."""

from __future__ import annotations

import re
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET

from docutils import nodes
from sphinx import addnodes
from sphinx.util import logging

LOGGER = logging.getLogger(__name__)


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
    root = nodes.container()
    stack: list[tuple[str, nodes.Element]] = [("root", root)]
    block_tags = {"p", "ul", "ol", "li", "pre", "blockquote"}
    supported = block_tags | {"code", "b", "strong", "i", "em", "a", "br"}

    def warn(message):
        LOGGER.warning(message, location=location, type="java", subtype="html")

    def close(tag):
        for i in range(len(stack) - 1, 0, -1):
            if stack[i][0] == tag:
                del stack[i:]
                return

    def append(node):
        current = stack[-1][1]
        if isinstance(current, nodes.literal_block):
            current += nodes.Text(node.astext())
            return
        if isinstance(current, (nodes.container, nodes.list_item, nodes.block_quote)):
            if isinstance(node, nodes.Text) and not node.astext().strip():
                return
            if not current.children or not isinstance(
                current.children[-1], nodes.paragraph
            ):
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
                append(nodes.literal("", value) if tag == "code" else nodes.Text(value))
            elif tag == "link":
                label = comment(token, location)
                inline = [child for p in label for child in p.children]
                append(reference(token, inline))
            elif tag == "start":
                name = token.get("name", "").lower()
                attrs = {a.get("name"): a.text or "" for a in token}
                if name not in supported:
                    warn(
                        f"Unsupported Javadoc HTML <{name}>; use paragraphs, lists, emphasis, links or <pre>."
                    )
                    continue
                if any(k not in {"href"} for k in attrs):
                    warn(
                        f"Javadoc HTML attributes on <{name}> are not supported except href; move layout and assets to a guide."
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
                if name in block_tags:
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
                    elif name == "ul":
                        node = nodes.bullet_list()
                    elif name == "ol":
                        node = nodes.enumerated_list(enumtype="arabic", start=1)
                    elif name == "li":
                        node = nodes.list_item()
                    elif name == "pre":
                        node = nodes.literal_block("", "", language="java")
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
                close(token.get("name", "").lower())
            else:
                warn(f"Unsupported XML comment token {tag}; regenerate the model.")

    tokens(part)

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
