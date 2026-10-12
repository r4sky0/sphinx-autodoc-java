"""Compare semantic comment content with the standard JDK doclet (test oracle only)."""

from html.parser import HTMLParser
import re

from test_integration import element

from sphinx_java_autodoc.extractor import extract, run
from sphinx_java_autodoc.render import comment


class Blocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks = []
        self.depth = 0
        self.content = []

    def handle_starttag(self, tag, attrs):
        if self.depth:
            self.depth += tag not in {"br", "hr", "wbr"}
        elif (tag == "div" and dict(attrs).get("class") == "block") or tag == "dd":
            self.depth = 1
            self.content = []

    def handle_endtag(self, tag):
        if self.depth and tag not in {"br", "hr", "wbr"}:
            self.depth -= 1
            if not self.depth:
                self.blocks.append(re.sub(r"\s+", " ", "".join(self.content)).strip())

    def handle_data(self, data):
        if self.depth:
            self.content.append(data)


def test_inline_and_inherited_return_descriptions_match_standard_doclet(tmp_path):
    source = tmp_path / "Returns.java"
    source.write_text("""public class Returns {
    /** {@return the {@code answer}} More details. */
    public int value() { return 42; }
    /** A value.
     * @return the {@code answer}
     */
    public int block() { return 42; }
    public static class Child extends Returns {
        /** {@return {@inheritDoc}} More details. */
        @Override public int value() { return 42; }
        /** {@return {@inheritDoc}} */
        @Override public int block() { return 42; }
    }
    public static class Omitted extends Returns {
        @Override public int value() { return 42; }
    }
}
""")
    root = extract([source], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")
    output = tmp_path / "standard"
    run(
        [
            "javadoc",
            "-J-Duser.language=en",
            "-J-Duser.country=US",
            "-locale",
            "en_US",
            "-quiet",
            "-Xdoclint:none",
            "-d",
            str(output),
            str(source),
        ]
    )
    for owner in ("Returns", "Returns.Child", "Returns.Omitted"):
        standard = Blocks()
        standard.feed((output / f"{owner}.html").read_text())
        member = element(root, owner + "#value()")
        body = member.find("doc/part[@kind='body']")
        result = member.find("doc/part[@kind='return']")
        rendered_body = " ".join(n.astext() for n in comment(body, None))
        rendered_return = " ".join(n.astext() for n in comment(result, None))
        assert rendered_body == "Returns the answer. More details."
        assert rendered_return == "the answer"
        assert rendered_body in standard.blocks
        assert rendered_return in standard.blocks
    child = element(root, "Returns.Child#block()")
    assert (
        " ".join(
            n.astext() for n in comment(child.find("doc/part[@kind='body']"), None)
        )
        == "Returns the answer."
    )
