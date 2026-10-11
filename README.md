# sphinx-java-autodoc

[![CI](https://github.com/r4sky0/sphinx-autodoc-java/actions/workflows/ci.yml/badge.svg)](https://github.com/r4sky0/sphinx-autodoc-java/actions/workflows/ci.yml)
[Documentation](https://r4sky0.github.io/sphinx-autodoc-java/)

Java source documentation rendered as native Sphinx pages, using JDK 25 compiler
and Javadoc APIs. Version 0.1.0 is an initial local release, not yet published.

See `docs/usage.rst` for installation and workflows, `docs/research.md` for the
backend comparison, and `docs/validation.md` for tested compatibility and limits.

```sh
uv sync --locked
uv run --locked sphinx-build -W --keep-going docs docs/_build/html
uv run --locked pytest
```

Requires JDK 25 (`java`, `javac`, `javadoc`), Python 3.12+, and Sphinx 9.1.x.
No application classes or annotation processors are executed. No Java dependencies
are downloaded by documentation builds. Bring your project's compile classpath.

```python
# conf.py
extensions = ["sphinx_java_autodoc"]
java_sources = ["../src/main/java"]
java_generate = "api"
```

```rst
.. java:autoclass:: com.example.Widget
   :members:

See :java:method:`com.example.Widget#find(java.lang.String)`.
```

MIT licensed. The extension ships its Java doclet source in the Python wheel.

Development and releases are documented in [CONTRIBUTING.md](CONTRIBUTING.md).
CI checks Python 3.12–3.14 on Linux and Python 3.12 on macOS and Windows, Ruff,
compiler warnings, built distributions, dependency vulnerabilities, both HTML
themes, the text builder, and Chromium browser interactions. Documentation deploys
after a successful CI run on `main`. Version tags run the full checks before PyPI
trusted publishing and a GitHub release.
