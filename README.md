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
downloads Java dependencies. See the [Apache Commons Lang example](https://r4sky0.github.io/sphinx-java-autodoc/showcase/commons-lang/furo/)
for what the output looks like.

## Requirements

Python 3.12+, Sphinx 9.1.x, and **JDK 25 for extraction**. Your library can keep
targeting Java 17 or 21. See [compatibility and limits](https://r4sky0.github.io/sphinx-java-autodoc/compatibility.html)
for the tested versions.

## Quick start

```sh
uv add sphinx-java-autodoc
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

[Publish your first API pages](https://r4sky0.github.io/sphinx-java-autodoc/getting-started.html) walks through these steps.
Then continue with:

- [Write a guide your users can follow](https://r4sky0.github.io/sphinx-java-autodoc/guide.html)
- [Build with dependencies and CI](https://r4sky0.github.io/sphinx-java-autodoc/build-integration.html): Maven/Gradle
  classpaths, pre-extracted models and publishing to GitHub Pages
- [Configuration and reference](https://r4sky0.github.io/sphinx-java-autodoc/usage.html) and [supported Javadoc](https://r4sky0.github.io/sphinx-java-autodoc/javadoc-support.html)
- [Troubleshooting](https://r4sky0.github.io/sphinx-java-autodoc/troubleshooting.html)
- [How it works](https://r4sky0.github.io/sphinx-java-autodoc/design.html) and the [architecture decision](docs/adr/0001-jdk-doclet-xml-sphinx-domain.md)

## Development

From a clone of this repository:

```sh
uv sync --locked
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
uv run --locked pytest
uv run --locked --group showcase python showcase/build.py
uv run --locked sphinx-build -W --keep-going -n docs docs/_build/html
```

Development and releases are documented in [CONTRIBUTING.md](CONTRIBUTING.md).
CI covers lint, compiler warnings, integration tests, built distributions,
dependency vulnerabilities, six HTML themes, the text builder, and Chromium
browser interactions.

[MIT licensed](LICENSE).
