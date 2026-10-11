# sphinx-java-autodoc

[![CI](https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml/badge.svg)](https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml)
[Documentation](https://r4sky0.github.io/sphinx-java-autodoc/)

Bring Java API documentation and handwritten guides into one Sphinx site.
`sphinx-java-autodoc` reads Java sources and Javadoc comments with the JDK compiler
APIs and renders them as native Sphinx content.

- Generate searchable API pages for classes, interfaces, enums, records, annotation
  types, and nested types.
- Preserve signatures, overloads, Javadoc links, and inherited method documentation.
- Include selected classes in guides and link between projects with intersphinx.
- Refresh generated pages when sources change, with content-based extraction caching.

Extraction does not execute application classes or annotation processors, and it
does not download Java dependencies. The wheel bundles the Java doclet source.

## Requirements and tested Java versions

**Projects targeting Java 17, 21, and 25 are tested. Documentation extraction
requires JDK 25**, even when the application builds and runs on an older Java version.
Your application's Java toolchain can stay as it is.

| Component | Requirement / tested coverage |
| --- | --- |
| Extraction JDK | JDK 25 only; tested with Temurin 25.0.3 |
| Project source/API release | Java 17, 21, and 25, tested using JDK 25's `--release` |
| Python | 3.12+; tested versions: 3.12, 3.13, and 3.14 |
| Sphinx | 9.1.x; tested with 9.1.0 |
| justhtml | 3.x (≥ 3.13); tested with 3.13.0 |

The [integration test](tests/test_integration.py) extracts the complete source
fixture at each of the three Java release levels. This verifies older source/API
releases on JDK 25; extraction on JDK 17 or 21 is unsupported and explicitly rejected.
Other source release levels have not been tested. See the
[validation report](docs/validation.md) for environment details and test evidence.

Put JDK 25's `java`, `javac`, and `javadoc` on `PATH`, or set `java_jdk` to its home
directory in Sphinx's `conf.py`. Installing the extension installs its compatible
Sphinx dependency and the pure-Python HTML5 parser `justhtml`.

## Install

From your documentation or Java project's root, install from GitHub:

```sh
uv add "sphinx-java-autodoc @ git+https://github.com/r4sky0/sphinx-java-autodoc.git"
```

With an existing virtual environment:

```sh
uv pip install "git+https://github.com/r4sky0/sphinx-java-autodoc.git"
```

## Quick start

For a project with Java files under `src/main/java/` and Sphinx files under `docs/`,
add this to **`docs/conf.py`**. Paths in `java_sources` are relative to that file:

```python
extensions = ["sphinx_java_autodoc"]
java_sources = ["../src/main/java"]
java_release = "17"  # use "21" or "25" for those source/API releases
java_generate = "api"
```

If you already have an `extensions` list, append `"sphinx_java_autodoc"` to it.
Set `java_release` to your project's target version; omitting it uses the
selected JDK's default release. If JDK 25 is not on `PATH`, also set
`java_jdk = "/path/to/jdk-25"`.

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

## Include API documentation in guides

Include a class in a handwritten `.rst` page and link to its methods:

```rst
.. java:autoclass:: com.example.Widget
   :members:
   :no-index:

See :java:method:`com.example.Widget#find(java.lang.String)`.
```

Replace the example names with your Java types. `:no-index:` lets this excerpt
coexist with the generated API pages without registering duplicate targets.
If your Java code depends on other libraries, configure `java_classpath` with
their JARs or class directories in `docs/conf.py`:

```python
java_classpath = ["../lib/dependency.jar", "../other-module/target/classes"]
```

Paths are relative to `conf.py`. Resolve dependencies and produce generated Java
sources before building documentation. The extension does not invoke Maven or Gradle.

## Current limits and further reading

- JPMS `module-info.java` inputs and Lombok-like compiler transformations are unsupported.
- Plain inline `{@snippet}` bodies render as native code blocks with optional `lang`;
  HTML tables render as native tables and `{@value}` shows constant values.
  External/hybrid snippets, regions, IDs and markup actions remain unsupported.
- Markdown Javadoc comments (`///`) and unsupported tags or HTML
  produce warnings; full standard Javadoc rendering is not implemented.
- Maven and Gradle integration recipes are provided but have not been executed in
  the recorded validation environment.

See the [usage guide](docs/usage.rst) for directive options, external Javadoc links,
intersphinx, Maven/Gradle recipes, and pre-extracted XML models. Rendering a
pre-extracted model requires no JDK; creating it still requires JDK 25.
The [validation report](docs/validation.md) records tested behavior and known limits;
the [architecture decision](docs/adr-001.md) and [backend comparison](docs/research.md)
explain the implementation choices.

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
