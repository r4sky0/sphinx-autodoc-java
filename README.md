# sphinx-java-autodoc

[![CI](https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml/badge.svg)](https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/sphinx-java-autodoc)](https://pypi.org/project/sphinx-java-autodoc/)
[Documentation](https://r4sky0.github.io/sphinx-java-autodoc/)

Publish your Java library's guides and API reference in one searchable Sphinx
site. `sphinx-java-autodoc` reads your Java sources and Javadoc comments with the
JDK compiler APIs and renders them as native Sphinx content:

- Generated pages for classes, interfaces, enums, records, annotation types and
  nested types.
- Signatures, overloads, Javadoc links and inherited method documentation.
- Class excerpts in handwritten guides, and cross-project links through intersphinx.
- Content-based caching: pages refresh when sources change.

Extraction never runs application classes or annotation processors, and never
downloads Java dependencies. See the
[Apache Commons Lang example](https://r4sky0.github.io/sphinx-java-autodoc/showcase/commons-lang/alabaster/)
for the output.

## Requirements

Python 3.12+, Sphinx 9.1.x, and **JDK 25 for extraction**. Your library can keep
targeting Java 17 or 21. See
[compatibility and limits](https://r4sky0.github.io/sphinx-java-autodoc/compatibility.html).

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

Next: [the first-build walkthrough](https://r4sky0.github.io/sphinx-java-autodoc/getting-started.html),
[writing guides](https://r4sky0.github.io/sphinx-java-autodoc/guide.html),
[dependencies and CI](https://r4sky0.github.io/sphinx-java-autodoc/build-integration.html) and the
[configuration reference](https://r4sky0.github.io/sphinx-java-autodoc/usage.html).

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). [MIT licensed](LICENSE).
