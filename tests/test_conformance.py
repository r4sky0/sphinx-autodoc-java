"""Compare semantic comment content with the standard JDK doclet (test oracle only)."""

from html import unescape
from html.parser import HTMLParser
import re

from docutils import nodes
from test_integration import element

from sphinx_java_autodoc.domain import summary_label, summary_type
from sphinx_java_autodoc.extractor import extract, run
from sphinx_java_autodoc.model import use_model
from sphinx_java_autodoc.render import FIELD_TITLES, comment


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


def test_link_labels_match_standard_doclet(tmp_path):
    source = tmp_path / "p/Links.java"
    source.parent.mkdir()
    source.write_text("""package p;
import java.util.Map;
/**
 * {@link java.util.Map.Entry}, {@link Map.Entry#getKey()}, {@link #of}, {@link #take},
 * {@link Links.Inner}, {@link Inner#go()}, {@link #Links()}, {@link #of(Object,Object)},
 * {@link String#format(String, Object...)}, {@link #FIELD} and {@link p}.
 */
public class Links {
    /** A field. */ public static final int FIELD = 1;
    /** Constructs. */ public Links() {}
    /** Pairs. @param <L> left @param <R> right @param left l @param right r @return a map */
    public static <L, R> Map<L, R> of(L left, R right) { return null; }
    /** Takes. @param a lists @param b numbers */
    public void take(java.util.List<String>[] a, int... b) {}
    /** Nested. */ public static class Inner { /** Goes. */ public void go() {} }
}
""")
    (tmp_path / "p/package-info.java").write_text("/** Package. */\npackage p;\n")
    root = extract([tmp_path], [], tmp_path / "cache").root
    assert not root.findall("diagnostic")
    output = tmp_path / "standard"
    run(["javadoc", "-quiet", "-Xdoclint:none", "-d", str(output), str(source)])
    standard = Blocks()
    standard.feed((output / "p/Links.html").read_text())
    body = element(root, "p.Links").find("doc/part[@kind='body']")
    rendered = " ".join(n.astext() for n in comment(body, None))
    assert rendered == (
        "Map.Entry, Map.Entry.getKey(), of(L, R), take(List[], int...), Links.Inner,"
        " Links.Inner.go(), Links(), of(Object,Object), String.format(String, Object...),"
        " FIELD and p."
    )
    assert rendered in standard.blocks


def test_override_notes_and_summaries_match_standard_doclet(tmp_path):
    (tmp_path / "p").mkdir()
    (tmp_path / "p/A.java").write_text("""package p;
import java.util.Map;
/** A. @param <T> the type */
public abstract class A<T> implements Comparable<A<T>>, Map.Entry<T, T> {
    /** Constant. */ public static final int F = 1;
    /** Compares. @param o other @return order */
    @Override public int compareTo(A<T> o) { return 0; }
    /** Hashes. @return hash */
    @Override public int hashCode() { return 0; }
    /** Key. @return key */
    @Override public final T getKey() { return null; }
    /** Abstract. @return value */
    public abstract T y();
    /** Pairs. @param <L> l @param <R> r @param left l @param right r @return map */
    public static <L, R> Map<L, R> of(L left, R right) { return null; }
}
""")
    (tmp_path / "p/B.java").write_text("""package p;
/** B. @param <T> the type */
public class B<T> extends A<T> {
    /** Implements. @return value */
    @Override public T y() { return null; }
    /** Value. @return value */
    public T getValue() { return null; }
    /** Sets. @param v value @return old */
    public T setValue(T v) { return null; }
}
""")
    root = extract([tmp_path], [], tmp_path / "cache").root
    use_model(root)
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
            str(tmp_path / "p/A.java"),
            str(tmp_path / "p/B.java"),
        ]
    )

    def text(markup):
        return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", "", markup))).strip()

    for owner in ("A", "B"):
        html = (output / f"p/{owner}.html").read_text()
        summary = html[html.index('<section class="method-summary"') :]
        summary = summary[: summary.index("</section>")]
        cells = re.findall(
            r'<div class="col-first[^"]*">(.*?)</div>\s*'
            r'<div class="col-second[^"]*">(.*?)</div>',
            summary,
            re.S,
        )
        standard = [(text(a), text(b)) for a, b in cells]
        members = [
            m
            for m in element(root, f"p.{owner}").findall("member")
            if m.get("kind") == "method"
        ]
        rendered = [
            (
                nodes.literal("", "", *summary_type(m)).astext(),
                summary_label(m),
            )
            for m in members
        ]
        # The standard doclet omits spaces between type arguments.
        assert sorted(
            tuple(re.sub(r"\s", "", cell) for cell in row) for row in rendered
        ) == sorted(tuple(re.sub(r"\s", "", cell) for cell in row) for row in standard)
        for member in members:
            name = member.get("name")
            section = html[html.index(f'<section class="detail" id="{name}(') :]
            section = section[: section.index("</section>")]
            notes = re.findall(
                r"<dt>(Specified by|Overrides):</dt>\s*<dd>(.*?)</dd>", section, re.S
            )
            # Javadoc adds the ancestor's type arguments, which the model does not record.
            expected = [(kind, re.sub(r"<.*", "", text(note))) for kind, note in notes]
            parts = [
                p
                for p in member.findall("doc/part")
                if p.get("kind") in {"specifiedBy", "overrides"}
            ]
            assert [
                (
                    FIELD_TITLES[p.get("kind")],
                    " ".join(n.astext() for n in comment(p, None)),
                )
                for p in parts
            ] == expected, member.get("id")
