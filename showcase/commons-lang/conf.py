"""Sphinx configuration for the Commons Lang showcase; built by showcase/build.py."""

import json
from pathlib import Path

showcase = json.loads((Path(__file__).parent / "showcase.json").read_text())

project = f"{showcase['name']} (sphinx-java-autodoc showcase)"
release = showcase["version"]
extensions = ["sphinx_java_autodoc"]
java_sources = ["../upstream/src/main/java"]
java_release = "17"
java_generate = "api"
java_external_javadoc = {
    "java": "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/",
}
html_theme = "alabaster"
html_static_path = []
rst_epilog = f"""
.. |version| replace:: {showcase["version"]}
.. |commit| replace:: ``{showcase["commit"][:12]}``
"""
