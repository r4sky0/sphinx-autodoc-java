# Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and Temurin
JDK 25. Ensure `java`, `javac`, and `javadoc` are on `PATH`.

```sh
uv sync --locked
uv run --locked pre-commit install
uv run --locked pre-commit run --all-files
uv run --locked pytest -q
uv run --locked sphinx-build -W --keep-going -n docs docs/_build/html
uv build
uv run --locked twine check --strict dist/*
```

`pre-commit install` sets up the commit and commit-message hooks; CI runs the same
hooks in the Lint job. They cover Ruff lint and formatting, google-java-format for
the doclet (the formatter Spotless uses for Java, pinned by checksum),
`javac -Xlint:all -Werror`, actionlint, zizmor, typos, `pyproject.toml`
validation, RST pitfalls, `uv.lock` freshness and basic file hygiene. Commit
messages must use conventional prefixes such as `feat:`, `fix:` or `docs:`, and
direct commits to `main` are rejected. Hooks with `--fix`/`--autofix` rewrite
files; review and stage their changes. Python tools run through `uv run --locked`,
so their versions come from `uv.lock`.

Update dependencies with `uv lock --upgrade`, and commit `uv.lock` with changes to
`pyproject.toml`. CI uses `--locked` so a stale lockfile fails. Dependabot opens
weekly updates, after a seven-day cooldown, for Python packages, pinned GitHub
Actions and pre-commit hook revisions. To update hooks by hand, run
`uv run --locked pre-commit autoupdate --freeze`.

For the browser checks:

```sh
uv sync --locked --extra test
uv run --locked --extra test playwright install chromium
uv run --locked sphinx-build -W --keep-going -D html_theme=classic docs docs/_build/classic
uv run --locked --extra test python tests/visual_check.py
```

Build the default HTML site first using the command above. Browser checks cover
desktop/mobile layouts, Java API structure, navigation, and search for Alabaster
and Classic. CI retains screenshots and a JSON report, including on failures.
API pages must not add horizontal overflow beyond the theme's normal layout;
Classic retains its fixed sidebar and minimum page width on mobile.

The required `All checks` status covers lint, compiler warnings, the test matrix,
source/wheel packaging, strict docs, browser checks, and dependency auditing.
Package checks install the wheel built from the source archive and run the real
integration suite against that installation. Weekly CI also detects newly
reported vulnerabilities. The application remains an initial release; passing CI
does not extend the compatibility promises in `docs/validation.md`.

# Releases

One-time PyPI setup must be completed by the PyPI account owner. Register a
[pending trusted publisher](https://pypi.org/manage/account/publishing/) with:

| Field | Value |
| --- | --- |
| PyPI project name | `sphinx-java-autodoc` |
| GitHub owner | `r4sky0` |
| Repository | `sphinx-java-autodoc` |
| Workflow filename | `release.yml` |
| Environment | `pypi` |

The GitHub repository and the Python distribution share the name
`sphinx-java-autodoc`. If the project already exists on PyPI, add the publisher in that project's Publishing settings instead. No PyPI
API token or repository deploy key is needed. See the
[PyPI trusted publisher documentation](https://docs.pypi.org/trusted-publishers/adding-a-publisher/).

To release:

1. Update `[project].version` in `pyproject.toml` and `VERSION` in
   `src/sphinx_java_autodoc/extractor.py` to the same value. Run `uv lock` and
   include the lockfile update in the release PR.
2. Merge the PR after `All checks` passes. Pull the updated `main` locally.
3. Create and push the matching version tag, for example:

   ```sh
   git tag -a v0.1.0 -m "Release 0.1.0"
   git push origin v0.1.0
   ```

The Release workflow rejects branches, tags that disagree with either version,
and commits outside `main`. It reruns CI on the tagged commit, publishes the
tested wheel and sdist using PyPI OIDC with attestations, and creates a GitHub
release with generated notes and distribution attachments. Published versions
are immutable; fix a bad release with a new version. For prereleases, use a PEP
440 version such as `0.2.0rc1` and the matching tag `v0.2.0rc1`.

To retry a failed release, rerun failed jobs in GitHub Actions. If publishing has
not succeeded, you can also dispatch Release manually and select the existing
tag. Dispatching against a branch deliberately fails validation.

GitHub Pages uses the built documentation artifact from a successful `main` push.
PRs build docs for validation without deploying. GitHub environments restrict
Pages to `main` and PyPI publishing to `v*` tags.
