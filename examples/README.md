# Examples

All three workflows use `standalone/src`, keeping one Java fixture to maintain.
Maven and Gradle files are complete minimal projects; neither build tool is invoked
by the Sphinx extension. See `../docs/usage.rst` for commands, classpaths, generated
sources and multi-module inputs. `dependency/src/vendor/Token.java` is a separate
library source used to illustrate compiling a dependency before extraction.

The Sphinx example is `../docs`: handwritten guides plus generated `api/` pages.
