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

from .model import Model, read_model

VERSION = "0.4.0"  # x-release-please-version
DOCLET = Path(__file__).parent / "java" / "SphinxDoclet.java"
PACKAGE = re.compile(r"[^\W\d]\w*(?:\.[^\W\d]\w*)*")


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


def extract(
    sources: list[Path],
    classpath: list[Path],
    cache: Path,
    *,
    jdk: str = "",
    release: str = "",
    sourcepath: list[Path] | None = None,
    encoding: str = "UTF-8",
    exclude_packages: list[str] | None = None,
) -> Model:
    """Returns the validated model, cached by a content hash of all inputs."""
    roots = [p.resolve() for p in sources]
    dependencies = [p.resolve() for p in classpath]
    lookup = [p.resolve() for p in sourcepath or []]
    excluded = sorted(set(exclude_packages or []))
    for name in excluded:
        if not PACKAGE.fullmatch(name):
            raise ExtensionError(
                f"Java autodoc: excluded package is not a package name: {name!r}"
            )
    for path in lookup:
        if not path.is_dir():
            raise ExtensionError(
                f"Java autodoc: source lookup directory does not exist: {path}"
            )
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
    semantic_files = files | {p for root in lookup for p in root.rglob("*.java")}
    if any(p.name == "module-info.java" for p in semantic_files):
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
                [str(p) for p in lookup],
                encoding,
                excluded,
            ]
        ).encode()
    )
    update(DOCLET.read_bytes())
    update(Path(__file__).read_bytes())
    for path in sorted(semantic_files):
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
        return Model(read_model(destination), destination, fingerprint)
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
            encoding,
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
        if excluded:
            args += ["--sphinx-exclude", ",".join(excluded)]
        # An explicit empty classpath avoids implicitly reading classes from cwd.
        empty = work / "empty"
        empty.mkdir()
        args += ["-classpath", os.pathsep.join(map(str, dependencies)) or str(empty)]
        args += [
            "-sourcepath",
            os.pathsep.join(
                str(p) for p in dict.fromkeys([p for p in roots if p.is_dir()] + lookup)
            )
            or str(empty),
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
            labels = {str(work): "<extract>"}
            for name, paths in (
                ("source", roots),
                ("sourcepath", lookup),
                ("classpath", dependencies),
            ):
                for index, path in enumerate(paths):
                    labels.setdefault(str(path), f"<{name}:{index}>")
            message = diagnostics.strip()
            # Longest first, so a root like src does not relabel part of src-gen.
            for path in sorted(labels, key=len, reverse=True):
                message = message.replace(path, labels[path])
            ET.SubElement(root, "diagnostic").text = message
        atomic_write(
            destination, ET.tostring(root, encoding="utf-8", xml_declaration=True)
        )
    return Model(root, destination, fingerprint)
