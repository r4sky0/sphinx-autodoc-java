# Working in this repository

Build dependable Java API documentation inside Sphinx while reusing Java sources
and standard Javadoc comments. Prefer small, complete changes and established JDK
and Sphinx APIs. Read the affected code and preserve unrelated work.

## Architecture and code map

The pipeline is Java source → JDK doclet → versioned XML → native Sphinx nodes.
Read [the architecture decision](docs/adr/0001-jdk-doclet-xml-sphinx-domain.md) before changing this boundary.

- `src/sphinx_java_autodoc/java/SphinxDoclet.java`: declarations, semantic links,
  signatures, comment tokens and documentation inheritance.
- `src/sphinx_java_autodoc/extractor.py`: subprocesses, model validation and caching.
- `src/sphinx_java_autodoc/render.py`: comment tokens to docutils/Sphinx nodes.
- `src/sphinx_java_autodoc/domain.py`: directives, roles, anchors and inventories.
- `src/sphinx_java_autodoc/__init__.py`: configuration, generated pages and build hooks.
- `src/sphinx_java_autodoc/__main__.py`: extraction CLI.
- `tests/test_integration.py`: real JDK/Sphinx integration tests.
- `tests/visual_check.py`: opt-in browser checks for Alabaster and Classic.
- `examples/`: standalone, Maven, Gradle and dependency fixtures.
- `docs/`: user guides, reference, compatibility record and design notes.

## Implementation rules

- Keep one compiler-backed extraction backend. Do not introduce a handwritten Java
  parser or parse generated Javadoc HTML for production extraction.
- Never execute application code or annotation processors to extract documentation.
  Documentation builds must not download Java dependencies implicitly.
- Render comments as native nodes. Do not interpret source comments as
  reStructuredText or inject raw HTML. Generated RST is for page skeletons only.
- Preserve semantic targets separately from display text, stable overload/nested-type
  identifiers, and inventory entries. Canonical erased IDs and external Javadoc URL
  fragments have different rules; test both when changing reference handling.
- Treat XML as a process boundary: validate inputs and update `docs/schema.md` and
  schema versioning deliberately when changing the contract.
- Keep output deterministic, without timestamps or machine-specific paths. Cache
  invalidation must include source/dependency contents, options and extractor/JDK
  identity. Preserve atomic publication and generated-page overwrite protection.
- Use subprocess argument lists, not shell interpolation. Preserve actionable
  diagnostics; unsupported content and unresolved inheritance must not silently pass.
- Extend the existing fixtures and integration tests for behavior changes. Keep
  source removal, incremental builds and Sphinx parallel workers in mind.

## Development and checks

Use JDK 25 (`java`, `javac`, `javadoc` on `PATH`), Python 3.12+, and Sphinx 9.1.x.
The exact tested range and known limits live in [docs/compatibility.rst](docs/compatibility.rst);
configured CI jobs are not evidence that an environment has passed.

```sh
uv sync --locked
uv run --locked pre-commit run --all-files
uv run --locked pytest -q
uv run --locked sphinx-build -W --keep-going -n docs docs/_build/html
```

The pre-commit hooks run Ruff, google-java-format, `javac -Xlint:all -Werror` on the
doclet, actionlint, zizmor, typos and file checks. Keep the doclet formatted with
google-java-format; don't hand-format it. Commit messages need conventional prefixes.

Run checks appropriate to the change. For rendering changes, build both themes and
run the browser checks described in [CONTRIBUTING.md](CONTRIBUTING.md). For workflow
changes, the pre-commit hooks run actionlint and zizmor. For packaging changes, run `uv build` and
`uv run --locked twine check --strict dist/*`, and validate the installed wheel.
Report blocked or unexecuted checks explicitly; do not broaden compatibility claims
without testing.

## Files and release consistency

- Edit source fixtures and guides, not generated `docs/api/`, `docs/_build/`,
  `build/`, `dist/` or `.java-autodoc-cache/` contents.
- Keep `uv.lock` consistent with dependency metadata changes. Avoid unrelated
  dependency upgrades.
- Keep the project version in `pyproject.toml` and `VERSION` in `extractor.py` in
  sync when preparing a release. Follow `CONTRIBUTING.md` for release procedures.
- Update usage documentation and recorded limitations when behavior changes.
  Rejected alternatives are in `docs/adr/0001-jdk-doclet-xml-sphinx-domain.md`; deferred work is in `docs/roadmap.md`.

## Agent skills

### Issue tracker

GitHub Issues in `r4sky0/sphinx-java-autodoc`, managed with the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: a root `CONTEXT.md`, created when first needed, plus ADRs in `docs/adr/`. See `docs/agents/domain.md`.
