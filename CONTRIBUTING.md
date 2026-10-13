# Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Temurin
JDK 25, with `java`, `javac` and `javadoc` on `PATH`.

```sh
uv sync --locked
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
uv run --locked pytest -q
uv run --locked --group showcase python showcase/build.py
uv run --locked sphinx-build -W --keep-going -n docs docs/_build/html
uv build
uv run --locked twine check --strict dist/*
```

Build the showcase before the docs, because the docs link into it.
`showcase/build.py` fetches the pinned Apache Commons Lang commit, builds it in
Furo, Read the Docs, Alabaster and Lumina under `build/showcase/commons-lang/html/<theme>/`,
and fails when a warning category exceeds the baseline in
`showcase/commons-lang/showcase.json`. Record lower counts with `--update-baseline`;
an increase needs a deliberate baseline update in the same change.

The pre-commit hooks also run in CI. They cover Ruff, google-java-format for the
doclet, `javac -Xlint:all -Werror`, actionlint, zizmor, typos, RST checks and
`uv.lock` freshness. Commit messages need conventional prefixes (`feat:`, `fix:`,
`docs:`), and direct commits to `main` are rejected. Hooks with `--fix` rewrite
files; review and stage their changes.

Update dependencies with `uv lock --upgrade` and commit `uv.lock` together with
`pyproject.toml`. Dependabot opens weekly updates after a seven-day cooldown.

## Browser checks

```sh
uv sync --locked --extra test --group showcase
uv run --locked --extra test --group showcase playwright install chromium
for theme in alabaster classic furo sphinx_rtd_theme lumina; do
  output=$theme; [ "$theme" = alabaster ] && output=html
  uv run --locked --extra test --group showcase sphinx-build -W --keep-going -n \
    -D "html_theme=$theme" examples/standalone/docs "examples/standalone/docs/_build/$output"
done
uv run --locked --extra test --group showcase python tests/visual_check.py
```

The checks render `examples/standalone/docs` at desktop and mobile widths in each
theme, including the search page, and fail on page errors or when API pages are
wider than the theme's own layout (measured on `reference.rst`).

## Other checks

- `uv run --locked python tests/build_tools_check.py` runs the Maven and Gradle
  consumer builds. It needs both tools on `PATH`, or `--maven`/`--gradle` paths.
- `uv run --locked python tests/benchmark.py /prepared/source/root` times a real
  project; see `docs/performance.rst`.

The required `All checks` status covers all of the above except the benchmark.
Passing CI does not widen `docs/compatibility.rst`; update that page only when a
new environment has actually passed.

# Releases

[Release Please](https://github.com/googleapis/release-please) opens a release PR
from the conventional commits on `main`. The PR bumps the version in
`pyproject.toml`, `src/sphinx_java_autodoc/extractor.py` and `uv.lock`, and updates
`CHANGELOG.md`. Before 1.0, `feat:` and breaking changes bump the minor version.
A `Release-As: 0.3.0` commit footer sets the version explicitly.

To release, merge the release PR once `All checks` passes. Release Please tags the
merge commit and dispatches the Release workflow, which reruns CI on the tag,
publishes to PyPI with attestations and publishes the GitHub release. Published
versions are immutable; fix a bad release with a new version. To retry, rerun the
failed jobs, or dispatch Release manually on the existing tag.

PyPI accepts uploads through a
[trusted publisher](https://docs.pypi.org/trusted-publishers/adding-a-publisher/),
so no API token is stored:

| Field | Value |
| --- | --- |
| PyPI project name | `sphinx-java-autodoc` |
| GitHub owner | `r4sky0` |
| Repository | `sphinx-java-autodoc` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

GitHub Pages publishes the docs from each successful `main` build. Same-repository
PRs get a preview at `pr-preview/pr-<number>/` after CI passes.
