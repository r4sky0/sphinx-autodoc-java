How it works
============

Sphinx runs a small JDK doclet over your sources before reading documents. The
doclet uses the compiler's view of declarations, overloads and Javadoc links and
writes a versioned XML model. The extension turns that model into native Sphinx
objects, cross-references and inventory entries. Source comments are never
interpreted as reStructuredText, and no raw HTML is emitted.

The extractor never loads application classes, so static initializers and
annotation processors do not run. Results are cached by the content of sources,
dependencies, options and the JDK, so any change re-extracts the whole project.

Design records
--------------

* `Architecture decision and alternatives considered
  <https://github.com/r4sky0/sphinx-java-autodoc/blob/main/docs/adr/0001-jdk-doclet-xml-sphinx-domain.md>`_
* `XML model schema
  <https://github.com/r4sky0/sphinx-java-autodoc/blob/main/docs/schema.md>`_

Contribute
----------

The `contributor guide
<https://github.com/r4sky0/sphinx-java-autodoc/blob/main/CONTRIBUTING.md>`_ covers
local setup, checks, browser validation and releases.
