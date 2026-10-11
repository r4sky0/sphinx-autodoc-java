from __future__ import annotations

import re

import pytest
from test_integration import SOURCES, build, element, project

from sphinx_java_autodoc.domain import anchor
from sphinx_java_autodoc.extractor import extract, read_model

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
    path, _ = extract([SOURCES], [], tmp_path / "cache")
    tokens = element(
        read_model(path), "demo.Widget#combine(int[][],java.lang.String[])"
    )
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


def test_models_without_signature_tokens_still_render(tmp_path):
    path, _ = extract([SOURCES], [], tmp_path / "cache")
    model = tmp_path / "old.xml"
    text = path.read_text()
    while "<sig>" in text:
        text = text[: text.index("<sig>")] + text[text.index("</sig>") + 6 :]
    model.write_text(text)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc']\n"
        f"java_model = {str(model)!r}\njava_generate = 'api'\n"
        f"java_external_javadoc = {{'java': '{ORACLE}{{module}}/'}}\n"
    )
    (docs / "index.rst").write_text("Old\n===\n\n.. toctree::\n\n   api/index\n")
    build(docs, tmp_path / "html")
    html = (tmp_path / "html/api/type-demo.Widget.html").read_text()
    text = " ".join(re.sub(r"<[^>]+>", " ", html).split())
    assert "public class demo.Widget implements demo.Transformer" in text
