from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest
from sphinx.errors import ExtensionError
from sphinx.util.inventory import InventoryFile

from sphinx_java_autodoc import generate_pages
from sphinx_java_autodoc.domain import anchor
from sphinx_java_autodoc.extractor import extract, read_model, run

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "examples/standalone/src"


def build(source, output, *args, success=True):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx",
            "-W",
            "--keep-going",
            *args,
            str(source),
            str(output),
        ],
        text=True,
        capture_output=True,
    )
    if success:
        assert result.returncode == 0, result.stdout + result.stderr
    else:
        assert result.returncode != 0, result.stdout
    return result.stdout + result.stderr


def project(path, sources=SOURCES, extra=""):
    docs = path / "docs"
    docs.mkdir(parents=True)
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc', 'sphinx.ext.intersphinx']\n"
        f"java_sources = [{str(sources)!r}]\njava_generate = 'api'\n"
        "java_external_javadoc = {'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{module}/'}\n"
        "nitpicky = True\nmaster_doc = 'index'\nproject = 'Fixture'\n" + extra
    )
    (docs / "index.rst").write_text(
        "Fixture\n=======\n\n.. toctree::\n\n   api/index\n\n"
        ":java:method:`demo.Widget#convert(int)`\n"
    )
    return docs


@pytest.fixture(scope="module")
def model(tmp_path_factory):
    cache = tmp_path_factory.mktemp("model")
    path, fingerprint = extract([SOURCES], [], cache)
    return read_model(path), path, fingerprint


@pytest.fixture(scope="module")
def site(tmp_path_factory):
    root = tmp_path_factory.mktemp("site")
    docs = project(root)
    out = root / "html"
    build(docs, out, "-j", "2")
    return docs, out


def element(root, symbol):
    return next(n for n in root.iter() if n.get("id") == symbol)


def signature(element):
    """The signature tokens' text, without the model's indentation between them."""
    return "".join(t.text or "" for t in element.find("sig").iter() if not len(t))


def test_semantic_extraction(model):
    root, _, _ = model
    assert not root.findall("diagnostic")
    assert {t.get("kind") for t in root.findall("type")} >= {
        "class",
        "interface",
        "record",
        "enum",
        "annotation_type",
    }
    assert element(root, "demo.Widget.Nested").get("kind") == "class"
    combine = element(root, "demo.Widget#combine(int[][],java.lang.String[])")
    assert signature(combine).endswith("combineint[][] valuesString... labels")
    generic = signature(
        element(root, "demo.Widget#buildIndex(java.util.List,java.util.Map)")
    )
    assert "<T extends Number & Comparable<T>>" in generic
    assert "? extends CharSequence" in generic
    assert '@Deprecated(since="1.0", forRemoval=true)' in signature(
        element(root, "demo.Widget#old()")
    )
    assert signature(element(root, "demo.Label#value()")).endswith('default "default"')
    assert element(root, "demo.Mode#FAST").get("kind") == "enum_constant"
    assert (
        element(root, "demo.Widget#<init>(java.lang.String)").get("kind")
        == "constructor"
    )
    assert not any(n.get("name") == "secret" for n in root.iter())
    inherited = element(root, "demo.Widget#convert(java.lang.String)")
    assert "Transforms a value" in "".join(inherited.find("doc").itertext())
    assert inherited.find("doc/part[@kind='param']").get("label") == "renamed"
    assert (
        inherited.find("doc/part[@kind='return']/text").text == "the transformed value"
    )
    assert (
        inherited.find("doc/part[@kind='throws']/text").text
        == "if the value is invalid"
    )
    assert "if the value is empty" in "".join(
        inherited.find("doc/part[@kind='throws']").itertext()
    )
    assert inherited.find("doc/part/link").get("target") == "demo.Widget#convert(int)"


def test_html_links_structure_inventory_search(site):
    docs, out = site
    html = (out / "api/type-demo.Widget.html").read_text()
    assert "java-autodoc.css" in html
    assert (out / "_static/java-autodoc.css").is_file()
    for symbol in ("demo.Widget#convert(int)", "demo.Widget#convert(java.lang.String)"):
        assert f'id="{anchor(symbol)}"' in html
    assert anchor("demo.Widget#convert(int)") != anchor(
        "demo.Widget#convert(java.lang.String)"
    )
    assert 'href="#' + anchor("demo.Widget#convert(int)") in html
    assert (
        "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/time/Instant.html"
        in html
    )
    assert "java/util/Map.Entry.html" in html
    assert "java/lang/String.html#substring(int,int)" in html
    assert "<strong>structure</strong>" in html
    assert 'href="https://example.test/?a=1&amp;b=2"' in html
    assert '<div class="line">First line</div>' in html
    assert '<div class="line"><em>Second line</em></div>' in html
    assert '<div class="line"><em>Third line</em></div>' in html
    assert '<ol class="arabic' in html
    assert "highlight-java" in html
    assert "[unresolved inheritDoc]" not in html
    assert "the text overload" in html
    assert "Deprecated" in html and "Since" in html
    assert "Constructors" in html and "Fields and constants" in html
    with (out / "objects.inv").open("rb") as stream:
        inventory = InventoryFile.load(stream, "", lambda base, uri: uri)
    assert "demo.Widget" in inventory["java:type"]
    assert "demo.Widget#convert(int)" in inventory["java:method"]
    assert "demo.Widget#LABEL" in inventory["java:field"]
    assert "demo.Widget.Nested" in inventory["java:type"]
    assert "demo" in inventory["java:package"]
    assert "transform" in (out / "searchindex.js").read_text().lower()


def test_intersphinx_consumer(site, tmp_path):
    _, provider = site
    docs = tmp_path / "consumer"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions=['sphinx_java_autodoc','sphinx.ext.intersphinx']\n"
        f"intersphinx_mapping={{'fixture': ('https://api.example.test/', {str(provider / 'objects.inv')!r})}}\n"
        "nitpicky=True\n"
    )
    (docs / "index.rst").write_text(
        "Consumer\n========\n\n"
        ":java:type:`demo.Widget` and :java:method:`demo.Widget#convert(int)`\n"
        "and :java:field:`demo.Widget#LABEL`.\n"
    )
    build(docs, tmp_path / "out")
    html = (tmp_path / "out/index.html").read_text()
    assert (
        "https://api.example.test/api/type-demo.Widget.html#"
        + anchor("demo.Widget#convert(int)")
        in html
    )


def test_deterministic_extraction_and_cache(model, tmp_path):
    _, original, _ = model
    copied = tmp_path / "source with spaces"
    shutil.copytree(SOURCES, copied)
    second, key = extract([copied], [], tmp_path / "cache")
    assert original.read_bytes() == second.read_bytes()
    mtime = second.stat().st_mtime_ns
    assert extract([copied], [], tmp_path / "cache") == (second, key)
    assert second.stat().st_mtime_ns == mtime
    source = copied / "demo/Widget.java"
    times = source.stat()
    source.write_text(
        source.read_text().replace(
            "Converts a number to text.", "Converts a number to prose."
        )
    )
    os.utime(source, ns=(times.st_atime_ns, times.st_mtime_ns))
    changed, newkey = extract([copied], [], tmp_path / "cache")
    assert newkey != key and b"to prose" in changed.read_bytes()
    _, releasekey = extract([copied], [], tmp_path / "cache", release="17")
    assert releasekey != newkey
    assert str(tmp_path).encode() not in changed.read_bytes()


def test_incremental_sphinx_source_add_remove_and_content(tmp_path):
    copied = tmp_path / "sources"
    shutil.copytree(SOURCES, copied)
    docs = project(tmp_path, copied)
    output = tmp_path / "out"
    build(docs, output)
    unchanged = build(docs, output)
    assert "0 changed" in unchanged
    source = copied / "demo/Widget.java"
    stat = source.stat()
    source.write_text(
        source.read_text().replace(
            "Converts a number to text.", "A newly changed description."
        )
    )
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    build(docs, output)
    assert (
        "A newly changed description."
        in (output / "api/type-demo.Widget.html").read_text()
    )
    assert len(list((output / ".doctrees/java-cache").glob("*.xml"))) == 1
    extra = copied / "demo/NewType.java"
    extra.write_text("package demo; /** Added later. */ public class NewType {}")
    build(docs, output)
    assert (output / "api/type-demo.NewType.html").exists()
    extra.unlink()
    build(docs, output)
    assert not (docs / "api/type-demo.NewType.rst").exists()
    with (output / "objects.inv").open("rb") as stream:
        inventory = InventoryFile.load(stream, "", lambda base, uri: uri)
    assert "demo.NewType" not in inventory["java:type"]


def test_dependency_classpath_and_invalidation(tmp_path):
    dependency = tmp_path / "dependency"
    dependency.mkdir()
    src = tmp_path / "Token.java"
    src.write_text("package vendor; public class Token {}")
    run(["javac", "-d", str(dependency), str(src)])
    source = tmp_path / "Use.java"
    source.write_text(
        "package client; /** Uses {@link vendor.Token}. */ public class Use { public vendor.Token token; }"
    )
    with pytest.raises(ExtensionError, match="compile classpath"):
        extract([source], [], tmp_path / "missing")
    path, key = extract([source], [dependency], tmp_path / "cache")
    assert read_model(path).find("type/doc/part/link").get("target") == "vendor.Token"
    cls = dependency / "vendor/Token.class"
    before = cls.stat()
    src.write_text("package vendor; public class Token { public int value; }")
    run(["javac", "-d", str(dependency), str(src)])
    os.utime(cls, ns=(before.st_atime_ns, before.st_mtime_ns))
    _, changed = extract([source], [dependency], tmp_path / "cache")
    assert changed != key


def test_diagnostics_and_strict_cli(tmp_path):
    source = tmp_path / "Bad.java"
    source.write_text("""package bad;
/** Missing {@link DoesNotExist}; {@snippet file="missing.java" :
 * int x = 1;
 * } */
public class Bad {
    /** {@inheritDoc} */ public void missing() {}
}""")
    path, _ = extract([source], [], tmp_path / "cache")
    messages = "\n".join(n.text for n in read_model(path).findall("diagnostic"))
    assert "Unresolved Javadoc reference DoesNotExist" in messages
    assert "Unsupported snippet" in messages
    assert "Cannot resolve inheritDoc" in messages
    output = tmp_path / "strict.xml"
    output.write_text("previous good model")
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx_java_autodoc",
            str(source),
            "-o",
            str(output),
            "--warnings-as-errors",
            "--cache",
            str(tmp_path / "cache"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1 and "warning:" in result.stderr
    assert output.read_text() == "previous good model"


def test_markdown_diagnostic(tmp_path):
    source = tmp_path / "Markdown.java"
    source.write_text("/// A **Markdown** comment.\npublic class Markdown {}\n")
    path, _ = extract([source], [], tmp_path / "cache")
    assert "Markdown documentation comments are not supported" in path.read_text()


def test_unresolved_and_ambiguous_sphinx_roles(site, tmp_path):
    source = project(tmp_path)
    with (source / "index.rst").open("a") as stream:
        stream.write(
            "\n:java:type:`absent.Type` and :java:method:`demo.Widget#convert`\n"
        )
    output = build(source, tmp_path / "out", success=False)
    assert "absent.Type" in output and "Ambiguous Java reference" in output


def test_visibility_selection_and_duplicate_excerpt(tmp_path):
    docs = project(tmp_path)
    with (docs / "index.rst").open("a") as stream:
        stream.write(
            "\n.. java:autoclass:: demo.Widget\n   :members: count; convert(int)\n   :visibility: public\n   :no-index:\n"
        )
    build(docs, tmp_path / "out")
    html = (tmp_path / "out/index.html").read_text()
    assert "Converts a number to text." in html
    assert "protected extension point" not in html
    assert "Combines array" not in html


def test_read_model_and_safe_generation(model, tmp_path):
    root, _, _ = model
    out = tmp_path / "api"
    generate_pages(root, out, "public")
    edited = out / "index.rst"
    edited.write_text(edited.read_text() + "My handwritten guide\n")
    with pytest.raises(ExtensionError, match="refusing to overwrite"):
        generate_pages(root, out, "public")
    assert "My handwritten guide" in edited.read_text()
    for content in (
        '<api schema="999"/>',
        '<!DOCTYPE api [<!ENTITY x "x">]><api schema="1"/>',
        '<api schema="1"><type/></api>',
    ):
        path = tmp_path / "bad.xml"
        path.write_text(content)
        with pytest.raises(ExtensionError, match="invalid model"):
            read_model(path)
    with pytest.raises(ExtensionError, match="source path does not exist"):
        extract([tmp_path / "absent"], [], tmp_path / "cache")
    with pytest.raises(ExtensionError, match="classpath entry does not exist"):
        extract([SOURCES], [tmp_path / "absent.jar"], tmp_path / "cache")


@pytest.mark.parametrize("release", ["17", "21", "25"])
def test_source_release_levels(tmp_path, release):
    path, _ = extract([SOURCES], [], tmp_path / "cache", release=release)
    assert element(read_model(path), "demo.Point").get("kind") == "record"


def test_text_builder(site, tmp_path):
    docs, _ = site
    build(docs, tmp_path / "text", "-b", "text")
    output = (tmp_path / "text/api/type-demo.Widget.txt").read_text()
    assert (
        "Transforms a value" in output
        and "String result = widget.convert(42);" in output
    )
    assert "First line\n" in output and "*Second line*\n" in output


def test_inheritance_search_order_omission_and_target(tmp_path):
    source = tmp_path / "Child.java"
    source.write_text("""package inherit;
interface Contract {
    /** From interface. @return interface result */
    String value();
}
class Base {
    /** From superclass.
     * @return superclass result
     */
    public String value() { return ""; }
}
public class Child extends Base implements Contract {
    /** {@inheritDoc} */
    public String value() { return ""; }
}""")
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    child = element(root, "inherit.Child#value()")
    assert "From superclass." in "".join(child.itertext())
    assert "superclass result" in "".join(child.itertext())
    assert "From interface" not in "".join(child.itertext())
    # Explicit supertype selection uses the named contract even with a superclass.
    source.write_text(
        source.read_text()
        .replace(
            "From interface. @return interface result",
            "From interface.\n     * @return interface result",
        )
        .replace("{@inheritDoc}", "{@inheritDoc Contract}")
    )
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    assert "From interface." in "".join(
        element(root, "inherit.Child#value()").itertext()
    )
    assert not root.findall("diagnostic")


def test_binary_ancestor_docs_warn_and_malformed_comments(tmp_path):
    source = tmp_path / "Binary.java"
    source.write_text("""public class Binary {
    /** {@inheritDoc} */
    @Override public String toString() { return ""; }
    /** Malformed {@link } */ public void bad() {}
}""")
    path, _ = extract([source], [], tmp_path / "cache")
    messages = "\n".join(d.text for d in read_model(path).findall("diagnostic"))
    assert "Cannot resolve inheritDoc" in messages
    assert "Malformed Javadoc" in messages


def test_concurrent_cache_publication(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [
            pool.submit(extract, [SOURCES], [], tmp_path / "cache") for _ in range(2)
        ]
        first, second = [future.result() for future in futures]
    assert first == second
    assert read_model(first[0]).find("type") is not None


def test_preextracted_model_requires_no_jdk(model, tmp_path):
    _, path, _ = model
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        f"extensions=['sphinx_java_autodoc']\njava_model={str(path)!r}\njava_jdk='/missing/jdk'\njava_generate='api'\njava_external_javadoc={{'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{{module}}/'}}\n"
    )
    (docs / "index.rst").write_text("API\n===\n\n.. toctree::\n\n   api/index\n")
    build(docs, tmp_path / "out")


def test_safe_html_and_native_lists():
    from docutils import nodes

    from sphinx_java_autodoc.render import comment

    part = ET.fromstring("""<part>
      <start name="ul"/><start name="li"/><text>Outer</text>
      <start name="ol"/><start name="li"/><text>Inner</text><end name="li"/><end name="ol"/>
      <end name="li"/><end name="ul"/>
      <start name="a"><attr name="href">javascript:alert(1)</attr></start><text>Unsafe</text><end name="a"/>
      <code>&lt;script&gt;alert(1)&lt;/script&gt;</code>
    </part>""")
    result = nodes.container("", *comment(part, None))
    assert len(list(result.findall(nodes.bullet_list))) == 1
    assert len(list(result.findall(nodes.enumerated_list))) == 1
    inner = next(result.findall(nodes.enumerated_list))
    assert isinstance(inner.parent, nodes.list_item)
    assert not list(result.findall(nodes.reference))
    assert "<script>alert(1)</script>" in result.astext()


def test_application_code_never_executes(tmp_path):
    source = tmp_path / "Dangerous.java"
    source.write_text("""/** A class whose initialization must never run. */
public class Dangerous {
    static { if (System.currentTimeMillis() > 0) throw new AssertionError("Executed application code"); }
    public Dangerous() { throw new AssertionError("Executed constructor"); }
}""")
    path, _ = extract([source], [], tmp_path / "cache")
    assert element(read_model(path), "Dangerous").get("kind") == "class"


def test_javadoc_fragments_match_standard_doclet(tmp_path):
    import html

    source = tmp_path / "Generic.java"
    source.write_text("""package fragments;
/** See {@link #Generic()}, {@link #take(Object[])}, {@link #arrays(Number[])}.
 * @param <T> stored type
 */
public class Generic<T> {
    /** Creates a value. */ public Generic() {}
    /** Accepts values. @param values the values */
    public void take(T... values) {}
    /** Accepts arrays.
     * @param <U> numeric type
     * @param values the values
     */
    public <U extends Number> void arrays(U[] values) {}
}""")
    path, _ = extract([source], [], tmp_path / "cache")
    standard = tmp_path / "standard"
    run(["javadoc", "-quiet", "-d", str(standard), str(source)])
    page = html.unescape((standard / "fragments/Generic.html").read_text())
    links = read_model(path).findall("type/doc/part/link")
    assert len(links) == 3
    for link in links:
        assert f'id="{link.get("fragment")}"' in page


def test_parallel_and_serial_inventories_match(site, tmp_path):
    docs, parallel = site
    serial = tmp_path / "serial"
    build(docs, serial, "-j", "1")
    assert (serial / "objects.inv").read_bytes() == (
        parallel / "objects.inv"
    ).read_bytes()


def test_jar_dependency(tmp_path):
    classes = tmp_path / "classes"
    run(
        [
            "javac",
            "-d",
            str(classes),
            str(ROOT / "examples/dependency/src/vendor/Token.java"),
        ]
    )
    jar = tmp_path / "dependency with spaces.jar"
    run(["jar", "--create", "--file", str(jar), "-C", str(classes), "."])
    source = tmp_path / "Use.java"
    source.write_text(
        "/** A dependency reference: {@link vendor.Token}. */ public class Use { public vendor.Token token; }"
    )
    path, _ = extract([source], [jar], tmp_path / "cache")
    assert (
        read_model(path).find("type/doc/part/link").get("path") == "vendor/Token.html"
    )


def test_type_annotations_do_not_change_identity(tmp_path):
    source = tmp_path / "Annotated.java"
    source.write_text("""import java.lang.annotation.*;
@Target(ElementType.TYPE_USE) @interface Flag {}
/** Type annotation fixture. */
public class Annotated {
    /** An annotated argument.
     * @param value text
     */
    public void accept(@Flag String value) {}
}""")
    path, _ = extract([source], [], tmp_path / "cache")
    member = element(read_model(path), "Annotated#accept(java.lang.String)")
    assert "@Flag" in signature(member)


def test_annotation_processors_are_not_executed(tmp_path):
    processor = tmp_path / "Trap.java"
    processor.write_text("""import java.util.Set;
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.TypeElement;
@SupportedAnnotationTypes("*")
@SupportedSourceVersion(SourceVersion.RELEASE_25)
public class Trap extends AbstractProcessor {
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment round) {
        throw new AssertionError("Annotation processor executed during extraction");
    }
}""")
    classes = tmp_path / "processor"
    run(["javac", "-proc:none", "-d", str(classes), str(processor)])
    service = classes / "META-INF/services/javax.annotation.processing.Processor"
    service.parent.mkdir(parents=True)
    service.write_text("Trap\n")
    source = tmp_path / "Application.java"
    source.write_text("/** An application. */ @Deprecated public class Application {}")
    path, _ = extract([source], [classes], tmp_path / "cache")
    assert element(read_model(path), "Application").get("kind") == "class"


def test_manual_external_role_preserves_varargs(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions=['sphinx_java_autodoc']\njava_external_javadoc={'vendor': 'https://example.test/api/'}\n"
    )
    (docs / "index.rst").write_text(
        "External\n========\n\n:java:method:`vendor.Service#consume(java.lang.String...)`\n"
    )
    build(docs, tmp_path / "out")
    assert (
        "https://example.test/api/vendor/Service.html#consume(java.lang.String...)"
        in (tmp_path / "out/index.html").read_text()
    )


@pytest.mark.parametrize("workers", ["1", "2"])
def test_incremental_role_only_page_detects_removed_member(tmp_path, workers):
    sources = tmp_path / "sources"
    shutil.copytree(SOURCES, sources)
    source = sources / "demo/Later.java"
    source.write_text("package demo; public class Later { public void value() {} }")
    docs = project(tmp_path, sources)
    with (docs / "index.rst").open("a") as stream:
        stream.write("\n:java:method:`demo.Later#value()`\n")
    output = tmp_path / "out"
    build(docs, output, "-j", workers)
    source.write_text("package demo; public class Later {}")
    messages = build(docs, output, "-j", workers, success=False)
    assert "demo.Later#value()" in messages
    assert anchor("demo.Later#value()") not in (output / "index.html").read_text()


@pytest.mark.parametrize("workers", ["1", "2"])
def test_incremental_missing_directive_recovers_when_type_is_added(tmp_path, workers):
    sources = tmp_path / "sources"
    shutil.copytree(SOURCES, sources)
    docs = project(tmp_path, sources)
    with (docs / "index.rst").open("a") as stream:
        stream.write("\n.. java:autoclass:: demo.Later\n   :no-index:\n")
    output = tmp_path / "out"
    build(docs, output, "-j", workers, success=False)
    (sources / "demo/Later.java").write_text(
        "package demo; /** Added API body. */ public class Later {}"
    )
    build(docs, output, "-j", workers)
    assert "Added API body." in (output / "index.html").read_text()


def test_html_attribute_entities_are_decoded_once(tmp_path):
    source = tmp_path / "Links.java"
    source.write_text(
        '/** <a href="https://example.test/?a=1&amp;b=2&#38;c=3&amp;amp;d=4">Query</a>. */ '
        "public class Links {}"
    )
    path, _ = extract([source], [], tmp_path / "cache")
    href = read_model(path).find("type/doc/part/start/attr")
    assert href.text == "https://example.test/?a=1&b=2&c=3&amp;d=4"


@pytest.mark.parametrize("explicit", [False, True])
@pytest.mark.parametrize("exception", ["IllegalArgumentException", "RuntimeException"])
def test_repeated_throws_preserves_all_descriptions_and_inheritance(
    tmp_path, explicit, exception
):
    source = tmp_path / "Child.java"
    comment = (
        "/** {@inheritDoc}\n"
        " * @param renamed {@inheritDoc}\n"
        " * @throws IllegalArgumentException {@inheritDoc}\n"
        " */"
        if explicit
        else ""
    )
    source.write_text(f"""interface Contract {{
    /** Validate the input.
     * @param value the input
     * @throws {exception} when value is negative; see {{@link String}}
     * @throws {exception} when value is too large
     */
    void validate(int value) throws {exception};
}}
public class Child implements Contract {{
    {comment}
    public void validate(int renamed) throws IllegalArgumentException {{}}
}}
""")
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    assert not root.findall("diagnostic")
    doc = element(root, "Child#validate(int)").find("doc")
    text = "".join(doc.itertext())
    assert text.index("when value is negative") < text.index("when value is too large")
    assert doc.find("part/link").get("target") == "java.lang.String"


def test_public_visibility_accounts_for_enclosing_types(tmp_path):
    source = tmp_path / "Outer.java"
    source.write_text("""public class Outer {
    protected static class Extension {
        public static class Nested { public int value; }
    }
}
""")
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    nested = element(root, "Outer.Extension.Nested")
    assert nested.get("visibility") == "protected"
    assert signature(nested).startswith("public static class")
    public = tmp_path / "public"
    generate_pages(root, public, "public")
    assert not (public / "type-Outer.Extension.Nested.rst").exists()
    protected = tmp_path / "protected"
    generate_pages(root, protected, "protected")
    assert (protected / "type-Outer.Extension.Nested.rst").exists()
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        f"extensions=['sphinx_java_autodoc']\njava_model={str(path)!r}\njava_visibility='public'\n"
    )
    (docs / "index.rst").write_text(
        "Public API\n==========\n\n.. java:autoclass:: Outer.Extension.Nested\n   :members:\n"
    )
    build(docs, tmp_path / "out")
    assert "Outer.Extension.Nested" not in (tmp_path / "out/index.html").read_text()


def test_line_breaks_preserve_inline_formatting_and_preformatted_text():
    from docutils import nodes

    from sphinx_java_autodoc.render import comment

    part = ET.fromstring("""<part>
      <text>First</text><start name="br"/>
      <start name="em"/><text>Second</text><start name="br" closed="true"/>
      <text>Third</text><end name="em"/><start name="br"/><start name="br"/>
      <text>Last</text>
      <start name="pre"/><text>Code</text><start name="br"/><text>continued</text><end name="pre"/>
    </part>""")
    result = nodes.container("", *comment(part, None))
    block = next(result.findall(nodes.line_block))
    assert [line.astext() for line in block.children] == [
        "First",
        "Second",
        "Third",
        "",
        "Last",
    ]
    assert isinstance(block.children[1][0], nodes.emphasis)
    assert isinstance(block.children[2][0], nodes.emphasis)
    assert next(result.findall(nodes.literal_block)).astext() == "Code\ncontinued"


def test_paragraph_boundaries_and_spaces_between_tokens():
    from docutils import nodes

    from sphinx_java_autodoc.render import comment

    part = ET.fromstring("""<part>
      <text> </text><code>public</code><text> </text>
      <link target="java.lang.reflect.Field" role="type"><text>Field</text></link>
      <start name="p"/><text>Closed</text><end name="p"/><text> after </text>
      <start name="h2"/><text>Heading</text><end name="h2"/><text>Text</text>
      <start name="ul"/><start name="li"/><code>a</code><text> </text><code>b</code>
      <end name="li"/><end name="ul"/>
    </part>""")
    result = nodes.container("", *comment(part, None))
    paragraphs = [p.astext().strip() for p in result.children[:4]]
    assert paragraphs == ["public Field", "Closed", "after", "Heading"]
    assert result.children[4].astext() == "Text"
    assert next(result.findall(nodes.list_item)).astext() == "a b"


def test_xml_invalid_characters_are_preserved_as_unicode_escapes(tmp_path):
    # javac translates \u0000 even inside comments; XML 1.0 cannot carry it.
    source = tmp_path / "Controls.java"
    source.write_text(
        "/** {@code \\u0000} is NUL; \\u0007 rings and"
        ' <a href="https://example.test/\\u0001">links</a> keep it. */\n'
        "public class Controls {}\n"
    )
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    assert not root.findall("diagnostic")
    part = element(root, "Controls").find("doc/part[@kind='body']")
    assert part.find("code").text == "\\u0000"
    assert "\\u0007 rings" in "".join(t.text for t in part.findall("text"))
    assert part.find("start/attr").text == "https://example.test/\\u0001"


def test_model_extractor_version_comes_from_the_package(tmp_path, monkeypatch):
    from sphinx_java_autodoc import extractor

    monkeypatch.setattr(extractor, "VERSION", "9.9.9")
    source = tmp_path / "Versioned.java"
    source.write_text("/** Versioned. */ public class Versioned {}\n")
    path, _ = extractor.extract([source], [], tmp_path / "cache")
    assert read_model(path).get("extractor") == "9.9.9"


def test_valueless_html_attributes_do_not_abort_extraction(tmp_path):
    source = tmp_path / "Compact.java"
    source.write_text("/** <ul compact><li>one</li></ul> */\npublic class Compact {}\n")
    path, _ = extract([source], [], tmp_path / "cache")
    root = read_model(path)
    start = element(root, "Compact").find("doc/part/start[@name='ul']")
    assert start.find("attr").get("name") == "compact"
    assert not start.find("attr").text
