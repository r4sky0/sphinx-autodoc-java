"""The API model: one extraction's validated declarations, looked up by symbol."""

from __future__ import annotations

from pathlib import Path
import re
import xml.etree.ElementTree as ET

from sphinx.errors import ExtensionError

# Member groups in display order, as section headings of generated type pages.
MEMBER_GROUPS = {
    "constructor": "Constructors",
    "field": "Fields and constants",
    "method": "Methods",
}
TYPE_GROUPS = {
    "interface": "Interfaces",
    "class": "Classes",
    "enum": "Enums",
    "record": "Records",
    "annotation_type": "Annotation types",
}
# The extracted model, indexed by prepare() on every build. It stays out of the pickled
# environment; forked parallel workers inherit it.
SYMBOLS: dict[str, ET.Element] = {}
PACKAGES: dict[str, ET.Element] = {}
REFERENCES: dict[str, dict[str, str]] = {}


def read_model(path: Path) -> ET.Element:
    """Validates XML schema 1 at the process boundary and returns its root."""
    try:
        data = path.read_bytes().decode("utf-8")
        if "<!DOCTYPE" in data.upper() or "<!ENTITY" in data.upper():
            raise ValueError("DTD and entity declarations are not allowed")
        root = ET.fromstring(data)
        if root.tag != "api" or root.get("schema") != "1":
            raise ValueError(
                "expected API XML schema 1; regenerate with sphinx-java-autodoc"
            )
        packages = [p.get("name") for p in root.findall("package")]
        qualified = r"[\w$]+(?:\.[\w$]+)*"
        if any(p is None or (p and not re.fullmatch(qualified, p)) for p in packages):
            raise ValueError("invalid package name")
        if len(set(packages)) != len(packages):
            raise ValueError("duplicate package")
        owners = {id(m): t for t in root.findall("type") for m in t.findall("member")}
        ids = set()
        for node in root.findall("type") + root.findall("type/member"):
            for key in ("id", "name", "kind", "visibility", "package"):
                if key not in node.attrib:
                    raise ValueError(f"{node.tag} is missing {key}")
            if node.find("sig") is None:
                raise ValueError(f"{node.tag} is missing sig")
            if node.attrib["id"] in ids:
                raise ValueError(f"duplicate symbol {node.attrib['id']}")
            ids.add(node.attrib["id"])
            if node.get("visibility") not in {"public", "protected"}:
                raise ValueError("invalid visibility")
            symbol, name, kind, package = (
                node.get(key) for key in ("id", "name", "kind", "package")
            )
            if not name or not "".join(node.find("sig").itertext()).strip():
                raise ValueError("empty declaration name or signature")
            if package not in packages:
                raise ValueError(f"undeclared package {package!r} for {symbol}")
            if node.tag == "type":
                if kind not in {
                    "class",
                    "interface",
                    "enum",
                    "record",
                    "annotation_type",
                }:
                    raise ValueError(f"invalid type kind {kind!r}")
                local = symbol.removeprefix(package + ".") if package else symbol
                if (
                    not re.fullmatch(qualified, local)
                    or local.rsplit(".", 1)[-1] != name
                    or (package and not symbol.startswith(package + "."))
                ):
                    raise ValueError(f"invalid type identity {symbol!r}")
            else:
                owner = owners[id(node)]
                if package != owner.get("package") or not symbol.startswith(
                    owner.get("id") + "#"
                ):
                    raise ValueError(f"invalid member owner for {symbol!r}")
                suffix = symbol.split("#", 1)[1]
                if kind in {"method", "constructor"}:
                    parameter = qualified + r"(?:\[\])*"
                    pattern = (
                        re.escape(name) + rf"\((?:{parameter}(?:,{parameter})*)?\)"
                    )
                    valid = re.fullmatch(pattern, suffix) and (
                        name == "<init>"
                        if kind == "constructor"
                        else re.fullmatch(r"[\w$]+", name)
                    )
                else:
                    valid = (
                        kind in {"field", "enum_constant", "record_component"}
                        and suffix == name
                        and re.fullmatch(r"[\w$]+", name)
                    )
                if not valid:
                    raise ValueError(f"invalid member identity or kind for {symbol!r}")
        tokens = {"k", "kt", "t", "q", "n", "tv", "pname", "v", "r"}
        for sig in root.findall("type/sig") + root.findall("type/member/sig"):
            for token in sig.iter():
                if token is sig or token.tag == "param":
                    continue
                if token.tag == "params":
                    if any(child.tag != "param" for child in token):
                        raise ValueError("invalid signature parameter list")
                elif token.tag not in tokens or len(token):
                    raise ValueError(f"invalid signature token {token.tag!r}")
                elif token.tag == "r" and not re.fullmatch(
                    qualified, token.get("target", "")
                ):
                    raise ValueError("invalid signature type reference")
        return root
    except (OSError, ET.ParseError, ValueError) as exc:
        raise ExtensionError(f"Java autodoc: invalid model {path}: {exc}") from exc


def use_model(root: ET.Element) -> None:
    SYMBOLS.clear()
    SYMBOLS.update(
        (e.get("id"), e) for e in root.findall("type") + root.findall("type/member")
    )
    PACKAGES.clear()
    PACKAGES.update((p.get("name"), p) for p in root.findall("package"))
    REFERENCES.clear()
    REFERENCES.update((n.get("target"), dict(n.attrib)) for n in root.iter("link"))


def visible(element: ET.Element, visibility: str) -> bool:
    return visibility == "protected" or element.get("visibility") == "public"


def member_group(member: ET.Element) -> str:
    kind = member.get("kind")
    return kind if kind in {"constructor", "method"} else "field"


def grouped(members) -> dict[str, list[ET.Element]]:
    """Members by member group, in display order."""
    groups = {group: [] for group in MEMBER_GROUPS}
    for member in members:
        groups[member_group(member)].append(member)
    return {group: found for group, found in groups.items() if found}


def member_label(symbol: str) -> str:
    """A member's name with simple parameter types, as in Javadoc summaries."""
    owner, _, rest = symbol.partition("#")
    name, paren, parameters = rest.partition("(")
    if name == "<init>":
        name = owner.rpartition(".")[2]
    if not paren:
        return name
    simple = [p.rpartition(".")[2] for p in parameters.rstrip(")").split(",") if p]
    return f"{name}({', '.join(simple)})"


def local_name(element: ET.Element) -> str:
    """A type without its package, or a member's label."""
    symbol, package = element.get("id"), element.get("package")
    if element.tag == "member":
        return member_label(symbol)
    return symbol[len(package) + 1 :] if package else symbol
