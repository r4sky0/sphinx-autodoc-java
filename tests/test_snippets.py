from __future__ import annotations

from html.parser import HTMLParser

from docutils import nodes
import pytest
from test_integration import build, element

from sphinx_java_autodoc.extractor import extract, run
from sphinx_java_autodoc.render import comment


def test_inline_snippets_preserve_literal_content_and_standard_indentation(tmp_path):
    source = tmp_path / "Snippets.java"
    source.write_text("""/** An example before the snippet.
 * {@snippet :
 *     if (1 < 2) {
 *         System.out.println("<&amp;>");
 *     }
 * }
 * After the snippet.
 * {@snippet lang="text" :
 *     .. include:: /etc/passwd
 *     {@link java.lang.String}
 * }
 */
public class Snippets {}
""")
    root, path, _ = extract([source], [], tmp_path / "cache")
    assert not root.findall("diagnostic")
    part = element(root, "Snippets").find("doc/part[@kind='body']")
    content = nodes.container("", *comment(part, None))
    blocks = list(content.findall(nodes.literal_block))
    assert len(blocks) == 2
    assert blocks[0]["language"] == "java"
    assert (
        blocks[0].astext()
        == '    if (1 < 2) {\n        System.out.println("<&amp;>");\n    }\n'
    )
    assert blocks[1]["language"] == "text"
    assert (
        blocks[1].astext()
        == "    .. include:: /etc/passwd\n    {@link java.lang.String}\n"
    )
    assert not list(content.findall(nodes.raw))
    assert not list(content.findall(nodes.reference))

    standard = tmp_path / "standard"
    run(["javadoc", "-quiet", "-d", str(standard), str(source)])

    class SnippetText(HTMLParser):
        def __init__(self):
            super().__init__()
            self.active = False
            self.blocks = []

        def handle_starttag(self, tag, attrs):
            if tag == "pre" and "snippet" in dict(attrs).get("class", "").split():
                self.active = True
                self.blocks.append("")

        def handle_endtag(self, tag):
            if tag == "pre":
                self.active = False

        def handle_data(self, data):
            if self.active:
                self.blocks[-1] += data

    oracle = SnippetText()
    oracle.feed((standard / "Snippets.html").read_text())
    assert oracle.blocks == [block.astext() for block in blocks]

    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        f"extensions=['sphinx_java_autodoc']\njava_model={str(path)!r}\n"
    )
    (docs / "index.rst").write_text(
        "Snippets\n========\n\n.. java:autoclass:: Snippets\n"
    )
    for theme in ("alabaster", "classic"):
        output = tmp_path / theme
        build(docs, output, "-D", f"html_theme={theme}")
        html = (output / "index.html").read_text()
        assert "highlight-java" in html and "highlight-text" in html
        assert ".. include:: /etc/passwd" in html
    build(docs, tmp_path / "text", "-b", "text")
    assert 'System.out.println("<&amp;>");' in (tmp_path / "text/index.txt").read_text()


@pytest.mark.parametrize(
    "snippet",
    [
        '{@snippet file="missing.java"}',
        '{@snippet class="missing.Example"}',
        '{@snippet file="missing.java" :\n int value = 1;\n}',
        '{@snippet region="example" :\n int value = 1;\n}',
        '{@snippet id="example" :\n int value = 1;\n}',
        '{@snippet lang="java" lang="text" :\n int value = 1;\n}',
        "{@snippet lang :\n int value = 1;\n}",
        '{@snippet :\n int value = 1; // @highlight substring="value"\n}',
        '{@snippet :\n // @start region="example"\n int value = 1;\n // @end\n}',
    ],
)
def test_unsupported_snippet_features_are_diagnosed(tmp_path, snippet):
    source = tmp_path / "Snippets.java"
    source.write_text(f"/** {snippet} */ public class Snippets {{}}")
    root = extract([source], [], tmp_path / "cache").root
    assert any("Unsupported snippet" in d.text for d in root.findall("diagnostic"))
    assert snippet in "".join(element(root, "Snippets").itertext())


def test_empty_inline_snippet(tmp_path):
    source = tmp_path / "Snippets.java"
    source.write_text("/** Before. {@snippet :\n} After. */ public class Snippets {}")
    root = extract([source], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")
    content = nodes.container("", *comment(root.find("type/doc/part"), None))
    assert next(content.findall(nodes.literal_block)).astext() == ""
