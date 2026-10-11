"""Sphinx site for the standalone fixture, used by the browser checks."""

import os

project = "Standalone fixture"
extensions = ["sphinx_java_autodoc"]
java_sources = ["../src"]
java_generate = "api"
java_external_javadoc = {
    "java": "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/",
}
html_theme = os.environ.get("JAVA_AUTODOC_THEME", "alabaster")
exclude_patterns = ["_build"]
nitpicky = True
html_static_path = []
