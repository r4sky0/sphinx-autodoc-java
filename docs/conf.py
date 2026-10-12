from importlib.metadata import version as distribution_version
import json
import os
from pathlib import Path

project = "Java autodoc"
release = distribution_version("sphinx-java-autodoc")
extensions = ["sphinx_java_autodoc", "sphinx.ext.intersphinx", "sphinx.ext.linkcode"]

# The feature gallery documents the fixture API that the tests and browser checks use.
java_sources = ["../examples/standalone/src"]
java_generate = "gallery/api"


def linkcode_resolve(domain, info):
    # shortcut: links follow main, so a pull request preview may point at older lines;
    # pass the built commit in if previews need exact lines.
    if domain == "java" and info["line"]:
        return (
            "https://github.com/r4sky0/sphinx-java-autodoc/blob/main/"
            f"examples/standalone/src/{info['source']}#L{info['line']}"
        )
    return None


# The Java API shown here is the Commons Lang showcase, published next to these docs
# at showcase/commons-lang/<theme>/; guides link to the Furo version. Its inventory
# comes from an explicit showcase build.
SHOWCASE_INVENTORY = (
    Path(__file__).parents[1] / "build/showcase/commons-lang/html/furo/objects.inv"
)
if not SHOWCASE_INVENTORY.is_file():
    raise RuntimeError(
        f"Missing {SHOWCASE_INVENTORY}; build the showcase first with "
        "`uv run --locked python showcase/build.py`."
    )
intersphinx_mapping = {
    "commons-lang": ("showcase/commons-lang/furo/", str(SHOWCASE_INVENTORY)),
}
java_external_javadoc = {
    "java": "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/",
}
html_theme = os.environ.get("JAVA_AUTODOC_THEME", "alabaster")
exclude_patterns = ["_build", "*.md"]
nitpicky = True
html_static_path = []

# Showcase facts come from its recorded baseline, so the page cannot drift from CI.
showcase = json.loads(
    (Path(__file__).parents[1] / "showcase/commons-lang/showcase.json").read_text()
)
warnings = showcase["warnings"]
rst_epilog = "\n".join(
    [
        f".. |showcase-version| replace:: {showcase['version']}",
        f".. |showcase-commit| replace:: ``{showcase['commit'][:12]}``",
        f".. |showcase-total| replace:: {sum(warnings.values())}",
        ".. |showcase-ref| replace:: "
        + str(sum(n for c, n in warnings.items() if c.startswith("ref."))),
        *(
            f".. |showcase-{category}| replace:: {count}"
            for category, count in warnings.items()
        ),
    ]
)
