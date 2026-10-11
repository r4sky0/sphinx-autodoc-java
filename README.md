# sphinx-java-autodoc

[![CI](https://github.com/r4sky0/sphinx-autodoc-java/actions/workflows/ci.yml/badge.svg)](https://github.com/r4sky0/sphinx-autodoc-java/actions/workflows/ci.yml)
[Documentation](https://r4sky0.github.io/sphinx-autodoc-java/)

Render Java sources and Javadoc comments as native Sphinx pages, with searchable
API documentation, cross-references, and intersphinx inventories.

## Install

Requires Python 3.12+, **JDK 25** with `java`, `javac`, and `javadoc` on `PATH`,
and Sphinx 9.1.x. Installing the extension installs its compatible Sphinx dependency.

Version 0.1.0 has not been published to PyPI yet. From your own documentation or
Java project's root, install the extension from GitHub:

```sh
uv add "sphinx-java-autodoc @ git+https://github.com/r4sky0/sphinx-autodoc-java.git"
```

If you already have a virtual environment instead of a uv project:

```sh
uv pip install "git+https://github.com/r4sky0/sphinx-autodoc-java.git"
```

After the first PyPI release, installation will be `uv add sphinx-java-autodoc`
or `pip install sphinx-java-autodoc`.

## Use in Sphinx

For a project with Java files under `src/main/java/` and Sphinx files under `docs/`,
add this to **`docs/conf.py`**. Paths in `java_sources` are relative to that file:

```python
extensions = ["sphinx_java_autodoc"]
java_sources = ["../src/main/java"]
java_generate = "api"
```

If you already have an `extensions` list, append `"sphinx_java_autodoc"` to it.
The extension extracts Java API information and generates pages under `docs/api/`.
Include those pages in **`docs/index.rst`**:

```rst
My Java project
===============

.. toctree::
   :maxdepth: 2

   api/index
```

Build the site from your project root:

```sh
uv run sphinx-build -W --keep-going docs docs/_build/html
```

Open `docs/_build/html/index.html` to view it. Rebuild after editing Java sources;
the extension refreshes the generated API pages. Keep handwritten guides outside
`docs/api/`, which is managed by the extension.

You can also include a class in a handwritten `.rst` page and link to its methods:

```rst
.. java:autoclass:: com.example.Widget
   :members:
   :no-index:

See :java:method:`com.example.Widget#find(java.lang.String)`.
```

Replace the example names with your Java types. `:no-index:` lets this excerpt
coexist with the generated API pages without registering duplicate targets.
If your Java code depends on other libraries, configure `java_classpath` with
their JARs or class directories; see the [usage guide](docs/usage.rst) for options,
Maven/Gradle integration, and pre-extracted models.

No application classes or annotation processors are executed, and documentation
builds do not download Java dependencies. The Python wheel bundles the Java doclet
source. See [tested compatibility and limits](docs/validation.md) and the
[backend comparison](docs/research.md).

## Development

From a clone of this repository:

```sh
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
```

Development and releases are documented in [CONTRIBUTING.md](CONTRIBUTING.md).
CI checks Python 3.12–3.14 on Linux and Python 3.12 on macOS and Windows, Ruff,
compiler warnings, built distributions, dependency vulnerabilities, both HTML
themes, the text builder, and Chromium browser interactions. Documentation deploys
after a successful CI run on `main`. Version tags run the full checks before PyPI
trusted publishing and a GitHub release.

MIT licensed.
