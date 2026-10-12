from __future__ import annotations

import os
import subprocess
import sys

import pytest
from sphinx.errors import ExtensionError
from test_integration import build, element

from sphinx_java_autodoc.extractor import extract, read_model


def sources(tmp_path):
    lookup = tmp_path / "lookup"
    dependency = lookup / "vendor" / "Parent.java"
    dependency.parent.mkdir(parents=True)
    dependency.write_text("""package vendor;
public class Parent {
    /** Parent description.
     * @param input original input
     * @return original result
     */
    public String run(String input) { return input; }
}
""")
    source = tmp_path / "Child.java"
    source.write_text("""public class Child extends vendor.Parent {
    @Override public String run(String renamed) { return renamed; }
}
""")
    return source, lookup, dependency


def test_lookup_sources_are_not_published_and_invalidate_by_content(tmp_path):
    source, lookup, dependency = sources(tmp_path)
    cache = tmp_path / "cache"
    path, fingerprint = extract([source], [], cache, sourcepath=[lookup])
    root = read_model(path)
    assert [t.get("id") for t in root.findall("type")] == ["Child"]
    assert not root.findall("diagnostic")
    assert "original result" in "".join(
        element(root, "Child#run(java.lang.String)").itertext()
    )
    assert extract([source], [], cache, sourcepath=[lookup]) == (path, fingerprint)
    stamp = dependency.stat()
    dependency.write_text(
        dependency.read_text().replace("original result", "updated result")
    )
    os.utime(dependency, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    changed, new_fingerprint = extract([source], [], cache, sourcepath=[lookup])
    assert new_fingerprint != fingerprint
    assert "updated result" in "".join(read_model(changed).itertext())
    dependency.unlink()
    with pytest.raises(ExtensionError, match="failed"):
        extract([source], [], cache, sourcepath=[lookup])


def test_cli_and_sphinx_lookup_configuration(tmp_path):
    source, lookup, _ = sources(tmp_path)
    model = tmp_path / "api.xml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx_java_autodoc",
            str(source),
            "--sourcepath",
            str(lookup),
            "--warnings-as-errors",
            "--cache",
            str(tmp_path / "cache"),
            "-o",
            str(model),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "conf.py").write_text(
        "extensions = ['sphinx_java_autodoc']\n"
        "java_sources = ['../Child.java']\njava_sourcepath = ['../lookup']\njava_generate = 'api'\n"
    )
    (docs / "index.rst").write_text("API\n===\n\n.. toctree::\n\n   api/index\n")
    build(docs, tmp_path / "html", "-j", "2")
    assert not (docs / "api/type-vendor.Parent.rst").exists()
    assert "original result" in (tmp_path / "html/api/type-Child.html").read_text()


def test_lookup_requires_a_directory(tmp_path):
    source, _, _ = sources(tmp_path)
    with pytest.raises(ExtensionError, match="source lookup directory"):
        extract([source], [], tmp_path / "cache", sourcepath=[source])
