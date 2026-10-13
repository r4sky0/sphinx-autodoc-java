# Examples

Test fixtures for extraction and rendering, not a library for end users. To
document your own sources, start with the
[walkthrough](https://r4sky0.github.io/sphinx-java-autodoc/getting-started.html).

- `standalone/src`: the Java fixture, shared by every example.
- `standalone/docs`: a Sphinx site with a handwritten guide and generated `api/`
  pages, used by the browser checks.
- `maven/` and `gradle/`: minimal projects that add `build-consumer/src`, resolve
  Commons Lang and generate `demo.BuildInfo` before extraction.
- `dependency/src`: a separate library used as a compiled dependency.

Run the Maven and Gradle builds with:

```sh
uv run --locked python tests/build_tools_check.py
```

Pass `--maven` and `--gradle` paths for tools outside `PATH`. The check extracts
with the exported classpath and renders the XML with an empty `PATH` to verify that
publication needs no JDK. See
[dependencies and publishing](https://r4sky0.github.io/sphinx-java-autodoc/build-integration.html)
for the commands.
