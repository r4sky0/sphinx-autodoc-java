# Examples

All three workflows use `standalone/src`, keeping one Java fixture to maintain.
Maven and Gradle files are complete minimal projects; neither build tool is invoked
by the Sphinx extension. See [build integration](../docs/build-integration.rst)
for commands, classpaths, generated sources and multi-module inputs.
`dependency/src/vendor/Token.java` is a separate
library source used to illustrate compiling a dependency before extraction.

The Sphinx example is `../docs`: handwritten guides plus generated `api/` pages.
These sources exercise extraction and rendering features; they are not a library
for end users. Start with the [first-build tutorial](../docs/getting-started.rst)
to document your own sources, and the [guide-writing example](../docs/guide.rst)
to connect a reader's task to API details.
