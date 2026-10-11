# Compatibility and release validation

Validation completed: **2026-10-11** (research dated 2026-10-10). Local release 0.1.0; no PyPI publication.

## Declared baseline and tested matrix

| Component | Baseline | Executed here | Qualification |
|---|---|---|---|
| JDK runtime | JDK 25 only | Temurin 25.0.3 | Other JDK runtimes are rejected, not claimed compatible |
| Java source/API release | Selected JDK's `--release` | 17, 21, 25 with the complete feature fixture | Cross-compilation on JDK 25 is not testing JDK 17/21 runtimes |
| Python | 3.12+ | CPython 3.12.13 and 3.14.5 | Minimum/current endpoints selected; 3.13 and future Python versions not run |
| Sphinx | `>=9.1,<9.2` | 9.1.0 | Other Sphinx releases not tested or advertised |
| Docutils | Through Sphinx | 0.22.4 | No separate broader promise |
| Platform | Platform-neutral Python/JDK implementation | macOS 26.4.1, arm64 | Linux/macOS/Windows CI configured; remote matrix not executed here |
| HTML themes | Native Sphinx nodes | Alabaster 1.0.0 and Sphinx Classic build | Browser visual inspection blocked; no visual compatibility claim |
| Other builders | Native nodes | Sphinx text builder | PDF/LaTeX, EPUB and other builders untested |
| Build parallelism | Sphinx parallel read/write hooks | `-j 2`, inventory compared with `-j 1` | Separate simultaneous Sphinx processes sharing generated directories unsupported |

The runtime range is intentionally narrow: only one JDK and one Sphinx release were
available. Two Python endpoints were available. Network restrictions prevented fresh
registry installation of several packages, so validation environments reused locally
installed dependency files (Sphinx, Docutils, Jinja2, pytest); Python 3.12 uses
MarkupSafe's pure-Python fallback. Unrelated pytest plugin auto-loading was disabled
on Python 3.12 to avoid another project's Python-3.14-only Playwright/greenlet binary.
The extension itself has no Python native dependency.

## Automated checks

Final local results: **27 tests passed on Python 3.12.13** (37.13 seconds), and
**27 passed on Python 3.14.5** (33.01 seconds). The doclet also compiled with
`javac -Xlint:all -Werror -proc:none`. Alabaster, Classic and text builds passed
with warnings treated as errors. A separately installed wheel successfully ran
strict extraction and a parallel Sphinx build; its bundled doclet was verified.
A wheel rebuilt from the source archive had identical file contents to the workspace
wheel. The source archive includes the extraction experiment, fixtures and tests.
These timings describe the test suite, not extraction performance benchmarks.

`tests/test_integration.py` exercises real JDK and Sphinx subprocesses:

- Classes, interfaces, enums/constants, records, annotation interfaces and defaults,
  constructors, fields, nested types, generics/bounds/wildcards, arrays and varargs.
- Declaration and type-use annotations; type annotations do not change symbol IDs.
- Inherited body/parameter/return/throws text, positional renamed parameters,
  superclass/interface precedence and explicit ancestor selection.
- Missing ancestor source documentation, malformed comments, unresolved Java links,
  unsupported snippet/Markdown diagnostics and strict CLI output preservation.
- Native HTML lists/emphasis/code, literal escaping, safe external URLs, internal
  overload anchors, external JDK links, and external nested-type paths.
- Constructor/generic/array/varargs fragments checked against **actual standard
  Javadoc output**, not hand-written expected anchors.
- Native object inventory, local cross-project intersphinx links, parallel versus
  serial inventory equality, text output, and search-index contents.
- Public/protected filtering, selected members, unindexed repeated excerpts, and
  generated-page overwrite protection.
- Source modification while preserving mtime, addition/removal, classpath content
  changes, real dependency class directories and JARs (including spaces in paths).
- Byte-for-byte XML determinism across checkout locations, cache hits, concurrent
  cache publication, invalid schema rejection, and pre-extracted models without a JDK.
- Extraction of a class whose static initializer and constructor throw if executed.
- An annotation processor trap confirms extraction does not execute processors.

Reproduce (after normal installation):

```sh
python -m pytest -q
sphinx-build -W --keep-going -j 2 docs docs/_build/html
JAVA_AUTODOC_THEME=classic sphinx-build -W --keep-going -j 2 docs docs/_build/classic
sphinx-build -W -b text docs docs/_build/text
python -m build
```

Build products are `dist/sphinx_java_autodoc-0.1.0-py3-none-any.whl`, the source archive,
and the built sites under `docs/_build/`. The wheel bundles the doclet source; no
Java build tool or downloaded doclet JAR is needed. Generated XML has no build date
or absolute checkout paths. Standard Javadoc HTML used as a test oracle is not a
published artifact and is not expected to be deterministic.

## Checks that could not run

- Chromium failed at macOS `bootstrap_check_in` / `MachPortRendezvousServer` with
  permission denied. Firefox aborted at startup under the same sandbox. No rendered
  screenshot was obtained. Both themes' HTML builds and structural checks passed,
  but navigation interaction, live search, viewport overflow, long-signature layout
  and screenshot review remain **unverified**. `tests/visual_check.py` provides the
  repeatable browser checks/screenshots for an unrestricted environment.
- Maven and Gradle executables were absent. Complete minimal project files and
  documented classpath-export commands are supplied, but those commands were not run.
- Direct PyPI project/JSON retrieval and a clean online dependency resolution were
  unavailable. Package-name availability remains provisional.
- No other JDK runtime, Sphinx version, OS, browser engine, large-project performance
  workload, or remote Javadoc link availability was tested.

## Known first-release limits

- Traditional comments only; Markdown/snippets and unsupported tags warn. The HTML
  subset excludes tables, definition lists, headings, images, attributes other than
  absolute link `href`, and local documentation assets. No raw HTML is emitted.
- Declared members are shown. Non-overridden inherited methods stay on ancestor
  pages; no copied inherited-member catalogue. Compiler-generated record/enum methods
  are listed but standard-doclet-generated prose is not synthesized.
- Inheritance does not implement generic exception-type substitution across an
  overridden method; unresolved parts warn. Ordinary exact/subtype exception matching
  is implemented. Annotation processors/Lombok transformations are not executed.
- Signatures preserve type spelling/annotations but are display text, not individual
  clickable type tokens. Semantic links in comments and explicit Java roles are native
  references. Arbitrary/manual Java declaration directives are not supplied.
- Javadoc 9+ URL structure only; Javadoc 8 member anchors are deferred. Manually mapped
  external roles without compiler metadata cannot validate symbol existence.
- JPMS inputs are rejected; multiple non-modular source roots are supported. Source
  roots supplied to make inherited dependency docs available are also extractable API
  roots. Use explicit directives when only a subset should appear.
- Whole-project extraction on input change, all dependency bytes hashed on cache hits,
  and no cache eviction. No performance claim beyond the small fixture tests.
- Sphinx may leave obsolete HTML files after source removal; use a clean output
  directory for publication. One generated source directory must have one Sphinx
  process owner at a time. Its own `-j` workers are supported.
