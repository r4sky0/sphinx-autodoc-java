Compatibility and limits
========================

This page is the single record of what has been tested and what is not supported.
Configured CI jobs and recipes do not widen these claims until they have passed.

Requirements and tested versions
--------------------------------

**Projects targeting Java 17, 21 and 25 are tested. Documentation extraction
requires JDK 25**, even when your library builds and runs on an older Java release.
Your library's own toolchain can stay as it is.

.. list-table::
   :header-rows: 1
   :widths: 25 30 45

   * - Component
     - Requirement
     - Tested
   * - Extraction JDK
     - JDK 25 only
     - Temurin 25.0.3. Other JDK runtimes are rejected with an error.
   * - Source/API release
     - ``java_release``; empty uses the JDK default
     - 17, 21 and 25 through JDK 25's ``--release``, with the complete feature
       fixture. This does not test JDK 17 or 21 runtimes.
   * - Python
     - 3.12+
     - 3.12, 3.13 and 3.14
   * - Sphinx
     - 9.1.x
     - 9.1.0, with the Docutils version it installs (0.22.4)
   * - Operating system
     - Platform-neutral
     - Linux, macOS and Windows in GitHub Actions
   * - HTML themes
     - Native Sphinx nodes
     - Alabaster 1.0.0, Sphinx Classic, Furo 2025.12.19, Read the Docs 3.1.0, PyData
       0.23.0 and Lumina 2.9.9 in Chromium at desktop (1440px) and mobile (390px)
       widths. Classic keeps a minimum width on mobile; Read the Docs and PyData
       overflow on phones for native Sphinx objects too, and Java pages stay within that.
   * - Other builders
     - Native Sphinx nodes
     - Text builder
   * - Parallel builds
     - Sphinx ``-j``
     - ``-j 2``, with an inventory identical to ``-j 1``

Put JDK 25's ``java``, ``javac`` and ``javadoc`` on ``PATH``, or set ``java_jdk``
to its home directory. A site that only renders a pre-extracted model or consumes
another site's inventory needs no JDK.

Not tested
----------

* Other JDK runtimes, Sphinx releases, Firefox and WebKit, PDF/LaTeX and EPUB
  builders.
* The :doc:`Maven and Gradle recipes <build-integration>`: the example project
  files are complete, but neither build tool has run them.
* Large projects: there is no performance claim beyond the test fixtures.
* Availability of remote Javadoc sites behind ``java_external_javadoc`` URLs.

Known limits
------------

* Traditional Javadoc comments and plain inline ``{@snippet}`` bodies are
  supported; see :doc:`javadoc-support`. Markdown comments (``///``), external or
  hybrid snippets, snippet regions, IDs and markup, and unsupported tags warn. The
  HTML subset excludes definition lists, headings, images, presentational attributes,
  ``<th>`` styling outside table headers, and local documentation assets.
* Only declared members are shown. Non-overridden inherited methods stay on their
  ancestor's page. Compiler-generated record and enum methods are listed, but the
  standard doclet's generated prose for them is not synthesized.
* Signatures are display text rather than individually clickable type tokens.
  Links in comments and explicit Java roles are native references. Manual Java
  declaration directives are not provided.
* External links use the Javadoc 9+ URL structure; Javadoc 8 member anchors are not
  supported. Roles mapped to external Javadoc without compiler metadata cannot
  check that the symbol exists.
* JPMS ``module-info.java`` inputs are rejected; several non-modular source roots
  are supported. Annotation processors and Lombok-like transformations are not run.
* Any input change re-extracts the whole project, cache hits still hash all
  dependency bytes, and old cache entries are not evicted.
* Sphinx can leave obsolete HTML files after a type is removed, so publish from a
  clean output directory. Each generated-page directory must belong to one Sphinx
  process at a time; that process's own ``-j`` workers are supported.

Evidence
--------

The `CI workflow <https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml>`_
runs the operating system and Python matrix, the real JDK and Sphinx integration
tests, packaging checks against the installed wheel, strict builds in six themes
and the Chromium browser checks. Browser screenshots are kept as run artifacts.
The integration tests compare constructor, generic, array and varargs anchors with
actual standard Javadoc output, check byte-for-byte XML determinism across checkout
locations, and confirm that extraction executes neither static initializers nor
annotation processors.
