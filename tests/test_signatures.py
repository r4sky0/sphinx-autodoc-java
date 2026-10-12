from __future__ import annotations

import pytest
from sphinx.errors import ExtensionError
from test_integration import SOURCES, build, element, project

from sphinx_java_autodoc.domain import anchor
from sphinx_java_autodoc.extractor import extract, read_model
from sphinx_java_autodoc.render import deprecated

ORACLE = "https://docs.oracle.com/en/java/javase/25/docs/api/"


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("signatures")
    out = root / "html"
    build(project(root), out)
    return out


def method_html(html, symbol):
    start = html.index('id="' + anchor(symbol) + '"')
    return html[start : html.index("</dt>", start)]


def test_signature_tokens_are_extracted(tmp_path):
    root = extract([SOURCES], [], tmp_path / "cache").root
    tokens = element(root, "demo.Widget#combine(int[][],java.lang.String[])")
    sig = tokens.find("sig")
    assert [t.tag for t in sig if t.tag not in {"t"}] == ["k", "r", "n", "params"]
    labels = [p.find("r") for p in sig.find("params")]
    assert labels[0] is None and labels[1].text == "String"
    assert labels[1].get("target") == "java.lang.String"
    assert labels[1].get("module") == "java.base"
    assert "".join(t.text for t in sig.find("params")[1]) == "String... labels"


def test_signatures_use_standard_nodes_and_link_types(site):
    html = (site / "api/type-demo.Widget.html").read_text()
    combine = method_html(html, "demo.Widget#combine(int[][],java.lang.String[])")
    assert '<span class="sig-paren">(</span>' in combine
    assert combine.count('<em class="sig-param">') == 2
    assert f'href="{ORACLE}java.base/java/lang/String.html"' in combine
    assert '<span class="sig-name descname"><span class="pre">combine</span>' in combine
    widget = method_html(html, "demo.Widget")
    assert (
        '<span class="sig-prename descclassname"><span class="pre">demo.</span>'
        in widget
    )
    assert (
        'href="type-demo.Transformer.html#' + anchor("demo.Transformer") + '"' in widget
    )


def test_long_parameter_lists_follow_the_sphinx_option(tmp_path):
    out = tmp_path / "html"
    build(project(tmp_path, extra="java_maximum_signature_line_length = 60\n"), out)
    html = (out / "api/type-demo.Widget.html").read_text()
    long = method_html(html, "demo.Widget#buildIndex(java.util.List,java.util.Map)")
    assert '<dd><em class="sig-param">' in long
    short = method_html(html, "demo.Widget#convert(int)")
    assert "<dd>" not in short


def test_only_annotations_on_the_declaration_mark_it_deprecated(tmp_path):
    source = tmp_path / "p/R.java"
    source.parent.mkdir()
    source.write_text("""package p;
/** A record. */
public record R(@Deprecated int old, int now) {
  /** Not deprecated. @param s text */
  public void m(@Deprecated String s) {}
  /** Not deprecated either. */
  public static final String TAG = "@java.lang.Deprecated";
  /** Deprecated. */
  @Deprecated
  public void gone() {}
}
""")
    root = extract([tmp_path], [], tmp_path / "cache").root
    flagged = {e.get("id") for e in root.iter() if e.get("id") and deprecated(e)}
    assert "p.R#gone()" in flagged
    assert not flagged & {
        "p.R",
        "p.R#<init>(int,int)",
        "p.R#m(java.lang.String)",
        "p.R#TAG",
    }


@pytest.mark.parametrize(
    "sig",
    [
        "<sig><script>x</script></sig>",
        "<sig><r target='java.lang.String)'>String</r></sig>",
        "<sig><r target='java.lang.String'><t>x</t></r></sig>",
        "<sig><params><t>x</t></params></sig>",
    ],
)
def test_models_with_invalid_signature_tokens_are_rejected(tmp_path, sig):
    path = extract([SOURCES], [], tmp_path / "cache").path
    text = path.read_text()
    start = text.index("<sig>")
    model = tmp_path / "bad.xml"
    model.write_text(text[:start] + sig + text[text.index("</sig>", start) + 6 :])
    with pytest.raises(ExtensionError, match="invalid model"):
        read_model(model)
