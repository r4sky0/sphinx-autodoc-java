from __future__ import annotations

from html.parser import HTMLParser
import re

from docutils import nodes
from test_integration import build, element

from sphinx_java_autodoc.extractor import extract, run
from sphinx_java_autodoc.render import comment

CONSTANTS = """package demo;

/** Refs: {@value #S}, {@value #C}, {@value #D}, {@value %x #I}, {@value #L},
 * {@value #F}, {@value Other#NAME} and {@value Double#MAX_VALUE}. */
public class Constants {
  /** String {@value}. */
  public static final String S = "a\\"b<c  d";
  /** Char {@value}. */
  public static final char C = '_';
  /** Double {@value}. */
  public static final double D = 1.5;
  /** Int {@value %04d}. */
  public static final int I = 255;
  /** Long {@value}. */
  public static final long L = 3L;
  /** Float {@value}. */
  public static final float F = 2.5f;

  private Constants() {}

  /** Nested constants. */
  public static final class Other {
    /** A name. */
    public static final String NAME = "other";

    private Other() {}
  }
}
"""


class BlockText(HTMLParser):
    """Collects the text of standard doclet description blocks in document order."""

    def __init__(self):
        super().__init__()
        self.depth = 0
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag == "div" and self.depth:
            self.depth += 1
        elif tag == "div" and "block" in (dict(attrs).get("class") or "").split():
            self.depth = 1
            self.blocks.append("")

    def handle_endtag(self, tag):
        if tag == "div" and self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.blocks[-1] += data


def text(part):
    content = nodes.container("", *comment(part, None))
    return re.sub(r"\s+", " ", content.astext()).strip()


def test_value_tags_render_constant_expressions_like_the_standard_doclet(tmp_path):
    source = tmp_path / "demo" / "Constants.java"
    source.parent.mkdir()
    source.write_text(CONSTANTS)
    root = extract([source], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")

    body = element(root, "demo.Constants").find("doc/part[@kind='body']")
    assert text(body) == (
        'Refs: "a\\"b<c d", \'_\', 1.5, ff, 3L, 2.5f, "other" and'
        " 1.7976931348623157E308."
    )
    links = body.findall("link")
    assert [link.get("target") for link in links] == [
        "demo.Constants#S",
        "demo.Constants#C",
        "demo.Constants#D",
        "demo.Constants#I",
        "demo.Constants#L",
        "demo.Constants#F",
        "demo.Constants.Other#NAME",
        "java.lang.Double#MAX_VALUE",
    ]
    assert {(link.get("role"), link.get("plain")) for link in links} == {
        ("field", "true")
    }
    assert links[0].find("literal").text == '"a\\"b<c  d"'
    external = links[-1]
    assert external.get("module") == "java.base"
    assert external.get("path") == "java/lang/Double.html"
    assert external.get("fragment") == "MAX_VALUE"

    own = {
        name: text(element(root, f"demo.Constants#{name}").find("doc/part"))
        for name in "SCDILF"
    }
    assert own == {
        "S": 'String "a\\"b<c d".',
        "C": "Char '_'.",
        "D": "Double 1.5.",
        "I": "Int 0255.",
        "L": "Long 3L.",
        "F": "Float 2.5f.",
    }
    assert not element(root, "demo.Constants#S").find("doc/part").findall("link")

    standard = tmp_path / "standard"
    run(["javadoc", "-quiet", "-d", str(standard), str(source)])
    oracle = BlockText()
    oracle.feed((standard / "demo/Constants.html").read_text())
    expected = {re.sub(r"\s+", " ", block).strip() for block in oracle.blocks}
    assert {text(body), *own.values()} <= expected


def test_value_tags_link_in_sphinx_builds(tmp_path):
    source = tmp_path / "demo" / "Constants.java"
    source.parent.mkdir()
    source.write_text(CONSTANTS)
    path = extract([source], [], tmp_path / "cache").path
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc']\n"
        f"java_model = {str(path)!r}\nnitpicky = True\n"
        "java_external_javadoc = {'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{module}/'}\n"
    )
    (docs / "index.rst").write_text(
        "Constants\n=========\n\n.. java:autoclass:: demo.Constants\n   :members:\n"
        "\n.. java:autoclass:: demo.Constants.Other\n   :members:\n"
    )
    build(docs, tmp_path / "html")
    html = (tmp_path / "html/index.html").read_text()
    assert (
        'href="https://docs.oracle.com/en/java/javase/25/docs/api/java.base/'
        'java/lang/Double.html#MAX_VALUE"' in html
    )
    assert "1.7976931348623157E308" in html
    assert "&quot;a\\&quot;b&lt;c  d&quot;" in html
    assert "&#x27;_&#x27;" in html or "'_'" in html
    assert "{@value" not in html
    build(docs, tmp_path / "text", "-b", "text")
    assert "{@value" not in (tmp_path / "text/index.txt").read_text()


def test_invalid_value_tags_are_diagnosed_and_kept(tmp_path):
    source = tmp_path / "Bad.java"
    source.write_text("""/** Missing {@value Missing#X}; computed {@value #O};
 * wrong format {@value %d #S}. */
public class Bad {
  /** Not constant {@value}. */
  public static final Object O = new Object();
  /** Text. */
  public static final String S = "s";
  /** Method {@value}. */
  public void method() {}
}
""")
    root = extract([source], [], tmp_path / "cache").root
    messages = "\n".join(d.text for d in root.findall("diagnostic"))
    assert "Unresolved Javadoc reference Missing#X" in messages
    assert "{@value #O} must reference a constant field" in messages
    assert "Invalid {@value} format %d" in messages
    assert "{@value} without a reference must document a constant field" in messages
    body = "".join(element(root, "Bad").find("doc/part").itertext())
    assert "{@value Missing#X}" in body
    assert "{@value #O}" in body
    assert '"s"' in body
    assert "{@value}" in "".join(element(root, "Bad#O").find("doc/part").itertext())
