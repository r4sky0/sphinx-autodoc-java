from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import pytest
from sphinx.errors import ExtensionError
from test_integration import SOURCES, build, element, project

from sphinx_java_autodoc.domain import anchor
from sphinx_java_autodoc.extractor import extract, read_model


@pytest.fixture(scope="module")
def signatures(tmp_path_factory):
    root = tmp_path_factory.mktemp("signatures")
    source = root / "Api.java"
    source.write_text("""package api;
import java.util.*;
import java.io.IOException;
import java.lang.annotation.*;
public class Api<T extends Number & Comparable<T>> {
    public static class Result {}
    @Target(ElementType.TYPE_USE) public @interface Mark { int value() default 0; }
    public class Inner<U> {}
    public Result @Mark(1) [] @Mark(2) [] matrix;
    public record Entry(Result result) {}
    public Result convert(List<? extends Result> input) throws IOException { return null; }
    public Map.Entry<String, Result[]>[] nested(Map<String, ? super Result> input) { return null; }
    public Api<T>.Inner<String> inner() { return null; }
    public @Mark Result @Mark[] array(@Mark Result @Mark... values) { return values; }
}
""")
    path, _ = extract([source], [], root / "cache")
    return path


def test_signature_tokens_preserve_display_and_type_identity(signatures):
    root = read_model(signatures)
    assert not root.findall("diagnostic")
    for declaration in root.findall("type") + root.findall("type/member"):
        signature = declaration.find("signature")
        text = "".join(
            n.text or "" for n in signature.iter() if n.tag in {"text", "name"}
        )
        assert text == declaration.get("signature")
        assert len(signature.findall("name")) == 1
    assert "api.Api.Result @api.Api.Mark(1) [] @api.Api.Mark(2) []" in element(
        root, "api.Api#matrix"
    ).get("signature")
    method = element(root, "api.Api#convert(java.util.List)")
    targets = {n.get("target") for n in method.findall("signature/link")}
    assert targets == {"api.Api.Result", "java.util.List", "java.io.IOException"}
    nested = element(root, "api.Api#nested(java.util.Map)")
    entry = next(
        n
        for n in nested.findall("signature/link")
        if n.get("target") == "java.util.Map.Entry"
    )
    assert entry.get("path") == "java/util/Map.Entry.html"
    assert entry.get("module") == "java.base"
    assert "api.Api<T>.Inner<java.lang.String>" in element(root, "api.Api#inner()").get(
        "signature"
    )
    assert "@api.Api.Mark" in element(root, "api.Api#array(api.Api.Result[])").get(
        "signature"
    )


@pytest.mark.parametrize("theme", ["alabaster", "classic"])
def test_signature_links_in_native_html_and_legacy_models(signatures, tmp_path, theme):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc']\nnitpicky = True\njava_generate = 'api'\n"
        f"java_model = {str(signatures)!r}\nhtml_theme = {theme!r}\n"
        "java_external_javadoc = {'java': 'https://docs.example/{module}/'}\n"
    )
    (docs / "index.rst").write_text("API\n===\n\n.. toctree::\n\n   api/index\n")
    out = tmp_path / "html"
    build(docs, out, "-j", "2")
    html = (out / "api/type-api.Api.html").read_text()
    declarations = "".join(re.findall(r"<dt\b.*?</dt>", html, re.S))
    assert 'href="type-api.Api.Result.html#' + anchor("api.Api.Result") in declarations
    assert (
        'href="https://docs.example/java.base/java/util/Map.Entry.html"' in declarations
    )
    assert (
        'href="https://docs.example/java.base/java/io/IOException.html"' in declarations
    )
    # Older models still work without structured signatures or external mappings.
    legacy = read_model(signatures)
    for declaration in legacy.findall("type") + legacy.findall("type/member"):
        declaration.remove(declaration.find("signature"))
    model = docs / "legacy.xml"
    model.write_bytes(ET.tostring(legacy))
    with (docs / "conf.py").open("a") as stream:
        stream.write("java_model = 'legacy.xml'\njava_external_javadoc = {}\n")
    build(docs, tmp_path / "legacy", "-b", "text")
    assert (
        "convert(java.util.List<? extends api.Api.Result> input)"
        in (tmp_path / "legacy/api/type-api.Api.txt").read_text()
    )


def test_automatic_signature_links_use_intersphinx_and_allow_missing_targets(tmp_path):
    supplier = project(tmp_path / "supplier")
    supplier_out = tmp_path / "supplier-out"
    build(supplier, supplier_out)
    source = tmp_path / "Consumer.java"
    source.write_text(
        "public class Consumer { public demo.Widget echo(demo.Widget value) { return value; } }"
    )
    docs = tmp_path / "consumer"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc', 'sphinx.ext.intersphinx']\nnitpicky = True\njava_generate = 'api'\n"
        f"java_sources = [{str(source)!r}]\njava_sourcepath = [{str(SOURCES)!r}]\n"
        f"intersphinx_mapping = {{'supplier': ('https://supplier.example/', {str(supplier_out / 'objects.inv')!r})}}\n"
    )
    (docs / "index.rst").write_text("API\n===\n\n.. toctree::\n\n   api/index\n")
    out = tmp_path / "consumer-out"
    build(docs, out)
    assert (
        "https://supplier.example/api/type-demo.Widget.html#" + anchor("demo.Widget")
        in (out / "api/type-Consumer.html").read_text()
    )
    with (docs / "conf.py").open("a") as stream:
        stream.write("intersphinx_mapping = {}\n")
    build(docs, tmp_path / "unmapped")
    # Automatic fallback must not suppress explicit missing-reference errors.
    with (docs / "index.rst").open("a") as stream:
        stream.write("\n:java:type:`missing.Type`\n")
    assert "missing.Type" in build(docs, tmp_path / "explicit", success=False)


def test_model_rejects_invalid_signature_reference(signatures, tmp_path):
    model = read_model(signatures)
    link = model.find("type/signature/link")
    link.set("target", "broken#member")
    path = tmp_path / "bad.xml"
    path.write_bytes(ET.tostring(model))
    with pytest.raises(ExtensionError, match="invalid signature type reference"):
        read_model(path)
