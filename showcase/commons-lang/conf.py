"""Sphinx configuration for the Commons Lang showcase; built by showcase/build.py."""

import json
import os
from pathlib import Path

showcase = json.loads((Path(__file__).parent / "showcase.json").read_text())
theme = os.environ.get("SHOWCASE_THEME", "furo")
THEMES = {
    "furo": "furo",
    "rtd": "sphinx_rtd_theme",
    "alabaster": "alabaster",
    "lumina": "lumina",
}

project = "Commons Lang"
release = showcase["version"]
extensions = ["sphinx_java_autodoc", "sphinx.ext.linkcode"]
java_sources = ["../upstream/src/main/java"]
java_release = "17"
java_generate = "api"
java_external_javadoc = {
    "java": "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/",
}


def linkcode_resolve(domain, info):
    # Links name the pinned commit, so they keep pointing at the documented lines.
    if domain == "java" and info["line"]:
        repository = showcase["repository"].removesuffix(".git")
        return (
            f"{repository}/blob/{showcase['commit']}/src/main/java/"
            f"{info['source']}#L{info['line']}"
        )
    return None


html_theme = THEMES[theme]
html_title = f"Commons Lang {showcase['version']}"
html_baseurl = f"{showcase['site']}{theme}/"
html_static_path = []
others = ", ".join(
    f"`{label} <../{key}/index.html>`__"
    for key, label in showcase["themes"].items()
    if key != theme
)
rst_epilog = f"""
.. |version| replace:: {showcase["version"]}
.. |commit| replace:: ``{showcase["commit"][:12]}``
.. |theme| replace:: {showcase["themes"][theme]}
.. |themes| replace:: {others}
"""
