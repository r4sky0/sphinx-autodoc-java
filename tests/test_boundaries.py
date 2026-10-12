from __future__ import annotations

import json
import xml.etree.ElementTree as ET

import pytest
from sphinx.errors import ExtensionError

from sphinx_java_autodoc import pages
from sphinx_java_autodoc.model import (
    PACKAGES,
    SYMBOLS,
    grouped,
    local_name,
    member_label,
    read_model,
    use_model,
    visible,
)


def published(name):
    """Three generated pages, as planned for one type named ``name``."""
    return {
        filename: f"{name}\n"
        for filename in ("index.rst", "package-demo.rst", f"type-demo.{name}.rst")
    }


def model(*names):
    root = ET.Element("api", schema="1")
    ET.SubElement(root, "package", name="demo")
    for name in names:
        declaration = ET.SubElement(
            root,
            "type",
            id=f"demo.{name}",
            name=name,
            kind="class",
            package="demo",
            visibility="public",
        )
        ET.SubElement(ET.SubElement(declaration, "sig"), "n").text = name
        member = ET.SubElement(
            declaration,
            "member",
            id=f"demo.{name}#run()",
            name="run",
            kind="method",
            package="demo",
            visibility="public",
        )
        ET.SubElement(ET.SubElement(member, "sig"), "n").text = "run"
    return root


@pytest.mark.parametrize(
    ("tag", "key", "value"),
    [
        ("type/member", "id", "broken"),
        ("type/member", "id", "demo.Other#run()"),
        ("type/member", "id", "demo.A#run(java.lang.String,)"),
        ("type/member", "kind", "class"),
        ("type/member", "package", "other"),
        ("type", "id", "other.A"),
        ("type", "name", "Other"),
        ("type", "kind", "method"),
        ("type", "line", "0"),
        ("type/member", "line", "12a"),
    ],
)
def test_model_rejects_invalid_declaration_contract(tmp_path, tag, key, value):
    root = model("A")
    path = tmp_path / "api.xml"
    root.find(tag).set(key, value)
    path.write_bytes(ET.tostring(root))
    with pytest.raises(ExtensionError, match="invalid model"):
        read_model(path)


@pytest.mark.parametrize("tag", ["type", "type/member"])
def test_model_rejects_missing_or_empty_signature(tmp_path, tag):
    path = tmp_path / "api.xml"
    for message, change in (
        ("missing sig", lambda node: node.remove(node.find("sig"))),
        ("empty declaration name or signature", lambda node: node.find("sig").clear()),
    ):
        root = model("A")
        change(root.find(tag))
        path.write_bytes(ET.tostring(root))
        with pytest.raises(ExtensionError, match=message):
            read_model(path)


def test_model_finds_symbols_and_labels():
    root = model("A", "B")
    root.find("type").set("visibility", "protected")
    use_model(root)
    a, run = SYMBOLS["demo.A"], SYMBOLS["demo.B#run()"]
    assert (a.tag, run.tag) == ("type", "member")
    assert "demo.Missing" not in SYMBOLS and set(PACKAGES) == {"demo"}
    assert not visible(a, "public") and visible(a, "protected")
    assert [local_name(a), local_name(run)] == ["A", "run()"]
    assert member_label("demo.A#<init>(java.lang.String,int[])") == "A(String, int[])"
    assert list(grouped(a.findall("member"))) == ["method"]


@pytest.mark.parametrize("failure", range(1, 6))
def test_generation_recovers_after_each_publication_step(
    tmp_path, monkeypatch, failure
):
    pages.publish_pages(tmp_path, published("Old"))
    write = pages.atomic_write
    calls = 0

    def interrupt(path, data):
        nonlocal calls
        calls += 1
        if calls == failure:
            raise OSError("interrupted")
        write(path, data)

    with monkeypatch.context() as patch:
        patch.setattr(pages, "atomic_write", interrupt)
        with pytest.raises(OSError, match="interrupted"):
            pages.publish_pages(tmp_path, published("New"))
    # Recovery also handles a different model on the next build.
    pages.publish_pages(tmp_path, published("Final"))
    assert {p.name for p in tmp_path.glob("*.rst")} == {
        "index.rst",
        "package-demo.rst",
        "type-demo.Final.rst",
    }
    pages.publish_pages(tmp_path, published("Final"))
    manifest = json.loads((tmp_path / ".java-autodoc-manifest.json").read_text())
    assert all(isinstance(value, str) for value in manifest.values())


def test_recovery_preserves_user_edits(tmp_path, monkeypatch):
    pages.publish_pages(tmp_path, published("Old"))
    write = pages.atomic_write
    calls = 0

    def interrupt(path, data):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise OSError("interrupted")
        write(path, data)

    with monkeypatch.context() as patch:
        patch.setattr(pages, "atomic_write", interrupt)
        with pytest.raises(OSError):
            pages.publish_pages(tmp_path, published("New"))
    edited = tmp_path / "type-demo.New.rst"
    edited.write_text("Handwritten content")
    with pytest.raises(ExtensionError, match="refusing to overwrite"):
        pages.publish_pages(tmp_path, published("Final"))
    assert edited.read_text() == "Handwritten content"


@pytest.mark.parametrize(
    "manifest", [[], {"../outside.rst": "a" * 64}, {"index.rst": []}, {"index.rst": 1}]
)
def test_invalid_manifest_is_rejected(tmp_path, manifest):
    (tmp_path / ".java-autodoc-manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ExtensionError, match="invalid generated-page manifest"):
        pages.publish_pages(tmp_path, published("A"))
    assert not list(tmp_path.glob("*.rst"))
