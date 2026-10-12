"""One compiler invocation per content fingerprint; no application code execution."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from sphinx.errors import ExtensionError

VERSION = "0.1.0"
DOCLET = Path(__file__).parent / "java" / "SphinxDoclet.java"


def run(arguments: list[str], *, cwd: Path | None = None) -> str:
    try:
        result = subprocess.run(
            arguments,
            cwd=cwd,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=180,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ExtensionError(
            f"Java autodoc: could not run {arguments[0]}: {exc}"
        ) from exc
    if result.returncode:
        raise ExtensionError(
            f"Java autodoc: {Path(arguments[0]).name} failed (exit {result.returncode}). "
            "Check JDK 25, source paths, --release and the compile classpath.\n"
            + result.stdout
            + result.stderr
        )
    return result.stdout + result.stderr


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() == data:
        return
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            stream.close()
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)


def read_model(path: Path) -> ET.Element:
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
            for key in ("id", "name", "kind", "visibility", "package", "signature"):
                if key not in node.attrib:
                    raise ValueError(f"{node.tag} is missing {key}")
            if node.attrib["id"] in ids:
                raise ValueError(f"duplicate symbol {node.attrib['id']}")
            ids.add(node.attrib["id"])
            if node.get("visibility") not in {"public", "protected"}:
                raise ValueError("invalid visibility")
            symbol, name, kind, package = (
                node.get(key) for key in ("id", "name", "kind", "package")
            )
            if not name or not node.get("signature").strip():
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
        return root
    except (OSError, ET.ParseError, ValueError) as exc:
        raise ExtensionError(f"Java autodoc: invalid model {path}: {exc}") from exc


def extract(
    sources: list[Path],
    classpath: list[Path],
    cache: Path,
    *,
    jdk: str = "",
    release: str = "",
) -> tuple[Path, str]:
    """Return immutable XML path and input fingerprint. All inputs are content hashed."""
    roots = [p.resolve() for p in sources]
    dependencies = [p.resolve() for p in classpath]
    files: set[Path] = set()
    for path in roots:
        if not path.exists():
            raise ExtensionError(f"Java autodoc: source path does not exist: {path}")
        found = list(path.rglob("*.java")) if path.is_dir() else [path]
        if not found or any(p.suffix != ".java" for p in found):
            raise ExtensionError(f"Java autodoc: no Java source files in {path}")
        files.update(found)
    if not files:
        raise ExtensionError(
            "Java autodoc: no sources configured; set java_sources or java_model."
        )
    if any(p.name == "module-info.java" for p in files):
        raise ExtensionError(
            "Java autodoc: JPMS module-info.java inputs are deferred; supply non-modular source roots or individual Java files and a compile classpath."
        )
    for path in dependencies:
        if not path.exists():
            raise ExtensionError(
                f"Java autodoc: classpath entry does not exist: {path}"
            )
    tools = {}
    for name in ("java", "javac", "javadoc"):
        executable = str(Path(jdk) / "bin" / name) if jdk else shutil.which(name)
        if not executable:
            raise ExtensionError(
                f"Java autodoc: {name} not found; install JDK 25 and set java_jdk."
            )
        tools[name] = executable
    identity = run([tools["java"], "-XshowSettings:properties", "-version"])
    # Use the actual runtime home, avoiding mixed tools from PATH and macOS launchers.
    home = next(
        (
            line.split("=", 1)[1].strip()
            for line in identity.splitlines()
            if line.strip().startswith("java.home =")
        ),
        "",
    )
    version = next(
        (
            line.split("=", 1)[1].strip()
            for line in identity.splitlines()
            if line.strip().startswith("java.version =")
        ),
        "",
    )
    if version.split(".")[0] != "25":
        raise ExtensionError(
            f"Java autodoc: JDK 25 is required for this release; found {version or 'unknown'}."
        )
    if home:
        tools = {name: str(Path(home) / "bin" / name) for name in tools}
    digest = hashlib.sha256()

    def update(data: bytes) -> None:
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)

    update(
        json.dumps(
            [
                VERSION,
                version,
                home,
                release,
                [str(p) for p in roots],
                [str(p) for p in dependencies],
            ]
        ).encode()
    )
    update(DOCLET.read_bytes())
    update(Path(__file__).read_bytes())
    for path in sorted(files):
        update(str(path).encode())
        update(path.read_bytes())
    for path in dependencies:
        for entry in sorted(path.rglob("*")) if path.is_dir() else [path]:
            if entry.is_file():
                update(str(entry).encode())
                update(entry.read_bytes())
    # JDK replacement at the same path must not reuse an old compiler result.
    for name in ("release", "lib/modules"):
        path = Path(home) / name
        if path.is_file():
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024):
                    digest.update(block)
    fingerprint = digest.hexdigest()
    cache.mkdir(parents=True, exist_ok=True)
    destination = cache / f"{fingerprint}.xml"
    if destination.exists():
        read_model(destination)
        return destination, fingerprint
    with tempfile.TemporaryDirectory(prefix="extract-", dir=cache) as directory:
        work = Path(directory)
        classes = work / "classes"
        run(
            [
                tools["javac"],
                "-encoding",
                "UTF-8",
                "-proc:none",
                "-d",
                str(classes),
                str(DOCLET),
            ]
        )
        output = work / "api.xml"
        args = [
            "-locale",
            "en_US",
            "-quiet",
            "-encoding",
            "UTF-8",
            "-protected",
            "-doclet",
            "sphinxjava.SphinxDoclet",
            "-docletpath",
            str(classes),
            "--sphinx-output",
            str(output),
        ]
        if release:
            args += ["--release", str(release)]
        # An explicit empty classpath avoids implicitly reading classes from cwd.
        empty = work / "empty"
        empty.mkdir()
        args += ["-classpath", os.pathsep.join(map(str, dependencies)) or str(empty)]
        args += [
            "-sourcepath",
            os.pathsep.join(str(p) for p in roots if p.is_dir()) or str(empty),
        ]
        args += [str(p) for p in sorted(files)]
        # JDK argument files avoid command length limits; no shell interpolation.
        argfile = work / "javadoc.args"
        argfile.write_text(
            "\n".join(
                '"'
                + s.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                + '"'
                for s in args
            ),
            encoding="utf-8",
        )
        diagnostics = run([tools["javadoc"], "@" + str(argfile)], cwd=work)
        root = read_model(output)
        root.set("extractor", VERSION)
        if diagnostics.strip():
            # Compiler warnings must remain visible on cache hits too.
            message = diagnostics.strip().replace(str(work), "<extract>")
            for index, source in enumerate(roots):
                message = message.replace(str(source), f"<source:{index}>")
            for index, entry in enumerate(dependencies):
                message = message.replace(str(entry), f"<classpath:{index}>")
            ET.SubElement(root, "diagnostic").text = message
        atomic_write(
            destination, ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
    return destination, fingerprint
