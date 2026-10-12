from __future__ import annotations

import subprocess
import sys

import pytest
from sphinx.errors import ExtensionError

from sphinx_java_autodoc.extractor import extract, read_model


def packages(tmp_path):
    root = tmp_path / "src"
    for name in ("app", "app.internal", "app.internal.deep", "application"):
        directory = root.joinpath(*name.split("."))
        directory.mkdir(parents=True)
        (directory / "Type.java").write_text(
            f"package {name};\n/** In {name}. */\npublic class Type {{}}\n"
        )
    return root


def test_excluded_packages_and_subpackages_are_omitted(tmp_path):
    source = packages(tmp_path)
    cache = tmp_path / "cache"
    included = extract([source], [], cache)
    excluded = extract([source], [], cache, exclude_packages=["app.internal"])
    assert included.fingerprint != excluded.fingerprint
    assert [t.get("id") for t in excluded.root.findall("type")] == [
        "app.Type",
        "application.Type",
    ]
    assert [p.get("name") for p in excluded.root.findall("package")] == [
        "app",
        "application",
    ]
    assert not excluded.root.findall("diagnostic")


def test_unmatched_and_invalid_excluded_packages(tmp_path):
    source = packages(tmp_path)
    root = extract([source], [], tmp_path / "cache", exclude_packages=["app.gone"]).root
    assert [d.text for d in root.findall("diagnostic")] == [
        "Excluded package app.gone matches no source package."
    ]
    with pytest.raises(ExtensionError, match="not a package name"):
        extract([source], [], tmp_path / "cache", exclude_packages=["app/internal"])


def test_source_encoding_is_configurable(tmp_path):
    source = tmp_path / "Latin.java"
    source.write_bytes("/** Café. */\npublic class Latin {}\n".encode("latin-1"))
    with pytest.raises(ExtensionError, match="javadoc failed"):
        extract([source], [], tmp_path / "cache")
    root = extract([source], [], tmp_path / "cache", encoding="ISO-8859-1").root
    assert root.find("type/doc/part/text").text == "Café."


def test_cli_passes_encoding_and_exclusions(tmp_path):
    source = packages(tmp_path)
    (source / "app" / "Type.java").write_bytes(
        "package app;\n/** Café. */\npublic class Type {}\n".encode("latin-1")
    )
    output = tmp_path / "api.xml"
    subprocess.run(
        [
            sys.executable,
            "-m",
            "sphinx_java_autodoc",
            str(source),
            "-o",
            str(output),
            "--cache",
            str(tmp_path / "cache"),
            "--encoding",
            "ISO-8859-1",
            "--exclude-package",
            "app.internal",
            "--exclude-package",
            "application",
            "--warnings-as-errors",
        ],
        check=True,
    )
    root = read_model(output)
    assert [t.get("id") for t in root.findall("type")] == ["app.Type"]
    assert root.find("type/doc/part/text").text == "Café."
