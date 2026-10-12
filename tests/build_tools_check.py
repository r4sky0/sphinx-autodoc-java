"""Opt-in Maven/Gradle consumer checks; build tools may download declared inputs."""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import tempfile

from sphinx_java_autodoc.extractor import read_model

ROOT = Path(__file__).resolve().parents[1]


def run(args, **kwargs):
    result = subprocess.run(
        args, cwd=ROOT, text=True, capture_output=True, timeout=600, **kwargs
    )
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--maven", default="mvn")
    parser.add_argument("--gradle", default="gradle")
    args = parser.parse_args()
    run(
        [
            args.maven,
            "-B",
            "-ntp",
            "-f",
            "examples/maven/pom.xml",
            "compile",
            "org.apache.maven.plugins:maven-dependency-plugin:3.11.0:build-classpath",
            "-Dmdep.includeScope=compile",
            "-Dmdep.outputFile=target/classpath.txt",
        ]
    )
    print("Maven compiled dependency and generated-source fixture", flush=True)
    run(
        [
            args.gradle,
            "--no-daemon",
            "-p",
            "examples/gradle",
            "classes",
            "writeJavaAutodocClasspath",
        ]
    )
    print("Gradle compiled dependency and generated-source fixture", flush=True)
    for tool, generated, classpath in (
        ("maven", "target/generated-sources/java-autodoc", "target/classpath.txt"),
        (
            "gradle",
            "build/generated/sources/java-autodoc",
            "build/java-autodoc-classpath.txt",
        ),
    ):
        base = ROOT / "examples" / tool
        assert "commons-lang3" in (base / classpath).read_text()
        with tempfile.TemporaryDirectory(prefix=f"java-autodoc-{tool}-") as directory:
            work = Path(directory)
            model = work / "api.xml"
            run(
                [
                    sys.executable,
                    "-m",
                    "sphinx_java_autodoc",
                    "examples/standalone/src",
                    "examples/build-consumer/src",
                    str(base / generated),
                    "--release",
                    "17",
                    "--classpath-file",
                    str(base / classpath),
                    "--warnings-as-errors",
                    "--cache",
                    str(work / "cache"),
                    "-o",
                    str(model),
                ]
            )
            root = read_model(model)
            ids = {t.get("id") for t in root.findall("type")}
            assert {"demo.Consumer", "demo.BuildInfo"} <= ids
            assert "org.apache.commons.lang3.tuple.Pair" not in ids
            docs = work / "docs"
            docs.mkdir()
            (docs / "conf.py").write_text(
                "extensions = ['sphinx_java_autodoc']\njava_generate = 'api'\n"
                f"java_model = {str(model)!r}\n"
                "java_external_javadoc = {\n"
                "    'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{module}/',\n"
                "    'org.apache.commons.lang3': 'https://commons.apache.org/proper/commons-lang/apidocs/',\n"
                "}\n"
            )
            (docs / "index.rst").write_text(
                "Consumer\n========\n\n.. toctree::\n\n   api/index\n"
            )
            run(
                [
                    sys.executable,
                    "-m",
                    "sphinx",
                    "-W",
                    "-n",
                    "-j",
                    "2",
                    str(docs),
                    str(work / "html"),
                ],
                env={**os.environ, "PATH": ""},
            )
            html = (work / "html/api/type-demo.Consumer.html").read_text()
            assert "labelled" in html and "org.apache.commons.lang3.tuple.Pair" in html
            assert (work / "html/api/type-demo.BuildInfo.html").exists()
            print(
                f"{tool}: strict extraction and JDK-free Sphinx rendering passed",
                flush=True,
            )


if __name__ == "__main__":
    main()
