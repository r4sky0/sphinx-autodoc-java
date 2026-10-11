from importlib.metadata import version as distribution_version
import os

project = "Java autodoc"
release = distribution_version("sphinx-java-autodoc")
extensions = ["sphinx_java_autodoc", "sphinx.ext.intersphinx"]
java_sources = ["../examples/standalone/src"]
java_generate = "api"
java_external_javadoc = {
    "java": "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/",
}
html_theme = os.environ.get("JAVA_AUTODOC_THEME", "alabaster")
exclude_patterns = ["_build", "*.md"]
nitpicky = True
html_static_path = []
