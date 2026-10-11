# sphinx-java-autodoc

[![CI](https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml/badge.svg)](https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml)
[Documentation](https://r4sky0.github.io/sphinx-java-autodoc/)

Publish your Java library's guides and API reference in one searchable Sphinx
site. Keep API contracts in Java sources and Javadoc; write guides that help
your users choose an API and complete a task.

`sphinx-java-autodoc` reads Java sources and Javadoc comments with the JDK compiler
APIs and renders them as native Sphinx content:

- Generated, searchable pages for classes, interfaces, enums, records, annotation
  types and nested types.
- Signatures, overloads, Javadoc links and inherited method documentation.
- Class excerpts in handwritten guides, and links between projects through intersphinx.
- Pages that refresh when sources change, with content-based extraction caching.

Extraction never executes application classes or annotation processors, and never
downloads Java dependencies. See the [example API](https://r4sky0.github.io/sphinx-java-autodoc/api/)
for what the output looks like.

## Requirements

Python 3.12+, Sphinx 9.1.x, and **JDK 25 for extraction**. Your library can keep
targeting Java 17 or 21. See [compatibility and limits](docs/compatibility.rst)
for the tested versions.

## Quick start

```sh
uv add "sphinx-java-autodoc @ git+https://github.com/r4sky0/sphinx-java-autodoc.git"
```

In `docs/conf.py`:

```python
extensions = ["sphinx_java_autodoc"]
java_sources = ["../src/main/java"]
java_release = "17"
java_generate = "api"
java_visibility = "public"
```

Add `api/index` to the toctree in `docs/index.rst`, then build:

```sh
uv run sphinx-build -W --keep-going -n docs docs/_build/html
```

[Publish your first API pages](docs/getting-started.rst) walks through these steps.
Then continue with:

- [Write a guide your users can follow](docs/guide.rst)
- [Build with dependencies and CI](docs/build-integration.rst): Maven/Gradle
  classpaths, pre-extracted models and publishing to GitHub Pages
- [Configuration and reference](docs/usage.rst) and [supported Javadoc](docs/javadoc-support.rst)
- [Troubleshooting](docs/troubleshooting.rst)
- [How it works](docs/design.rst) and the [architecture decision](docs/adr-001.md)

## Development

From a clone of this repository:

```sh
uv sync --locked
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
uv run --locked pytest
uv run --locked sphinx-build -W --keep-going -n docs docs/_build/html
```

Development and releases are documented in [CONTRIBUTING.md](CONTRIBUTING.md).
CI covers lint, compiler warnings, integration tests, built distributions,
dependency vulnerabilities, Alabaster and Classic, the text builder, and Chromium
browser interactions.

[MIT licensed](LICENSE).
