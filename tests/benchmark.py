"""Opt-in cold/cache/edit measurements on a copied, locally prepared source tree.

Runs real extraction and HTML builds. Does not download dependencies or change
input sources. Warnings are counted, not suppressed: timings do not certify fidelity.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from time import perf_counter

import sphinx

from sphinx_java_autodoc.extractor import VERSION, extract, run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--classpath", default="")
    args = parser.parse_args()
    if not args.source.is_dir():
        parser.error("source must be a prepared Java source directory")
    classpath = [Path(p).resolve() for p in args.classpath.split(os.pathsep) if p]
    report = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "sphinx": sphinx.__version__,
        "extension": VERSION,
        "java": run(["java", "-version"]).splitlines()[0],
        "phases": [],
    }
    with tempfile.TemporaryDirectory(prefix="java-autodoc-benchmark-") as directory:
        work = Path(directory)
        source = work / "source"
        shutil.copytree(args.source, source)
        files = sorted(source.rglob("*.java"))
        assert files, "No Java source files"
        report["source_files"] = len(files)
        report["source_bytes"] = sum(p.stat().st_size for p in files)
        digest = hashlib.sha256()
        for path in files:
            digest.update(path.relative_to(source).as_posix().encode())
            digest.update(path.read_bytes())
        report["source_sha256"] = digest.hexdigest()
        docs = work / "docs"
        docs.mkdir()
        (docs / "conf.py").write_text(
            "extensions = ['sphinx_java_autodoc']\njava_generate = 'api'\n"
            f"java_sources = [{str(source)!r}]\njava_classpath = {[str(p) for p in classpath]!r}\n"
        )
        (docs / "index.rst").write_text(
            "Benchmark\n=========\n\n.. toctree::\n\n   api/index\n"
        )
        cache = work / "html/.doctrees/java-cache"
        original = None
        model_bytes = None
        for phase in ("cold", "cache_hit", "comment_edit"):
            if phase == "comment_edit":
                candidate = next(
                    (
                        p
                        for p in files
                        if p.name == "package-info.java" and "/**" in p.read_text()
                    ),
                    None,
                )
                if candidate is None:
                    candidate = next(p for p in files if "/**" in p.read_text())
                stamp = candidate.stat()
                candidate.write_text(
                    candidate.read_text().replace("/**", "/** Benchmark edit. ", 1)
                )
                os.utime(candidate, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
            start = perf_counter()
            model, path, fingerprint = extract([source], classpath, cache)
            extraction = perf_counter() - start
            if phase == "cold":
                original = fingerprint
                model_bytes = path.read_bytes()
                report["types"] = len(model.findall("type"))
                report["members"] = len(model.findall("type/member"))
                report["xml_bytes"] = path.stat().st_size
            elif phase == "cache_hit":
                assert fingerprint == original and path.read_bytes() == model_bytes
            else:
                assert fingerprint != original and path.read_bytes() != model_bytes
            start = perf_counter()
            result = subprocess.run(
                [sys.executable, "-m", "sphinx", "-q", str(docs), str(work / "html")],
                text=True,
                capture_output=True,
                timeout=600,
            )
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
            assert (work / "html/objects.inv").is_file()
            report["phases"].append(
                {
                    "phase": phase,
                    "extract_seconds": round(extraction, 3),
                    "sphinx_seconds_including_cache_check": round(
                        perf_counter() - start, 3
                    ),
                    "extraction_diagnostics": len(model.findall("diagnostic")),
                    "sphinx_warning_lines": result.stderr.count("WARNING:"),
                }
            )
        if sys.platform != "win32":
            import resource

            scale = 1024 * 1024 if sys.platform == "darwin" else 1024
            report["peak_child_rss_mib"] = round(
                resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / scale, 1
            )
            report["peak_python_rss_mib"] = round(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / scale, 1
            )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
