Compatibility and limits
========================

What has been tested, and what is not supported. A configured CI job does not
count until it has passed.

Requirements and tested versions
--------------------------------

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
     - 8.2.x and 9.1.x
     - 9.1.0, with the Docutils version it installs (0.22.4); the test suite on 8.2.3
   * - Operating system
     - Platform-neutral
     - Linux, macOS and Windows in GitHub Actions
   * - HTML themes
     - Native Sphinx nodes
     - Alabaster 1.0.0, Sphinx Classic, Furo 2025.12.19, Read the Docs 3.1.0 and
       Lumina 2.9.11 in Chromium at desktop (1440px) and mobile (390px) widths.
       Classic keeps a minimum width on mobile; Read the Docs overflows on phones
       for native Sphinx objects too, and Java pages stay within that.
   * - Other builders
     - Native Sphinx nodes
     - Text builder
   * - Parallel builds
     - Sphinx ``-j``
     - ``-j 2``, with an inventory identical to ``-j 1``

Not tested
----------

* Other JDK runtimes, Sphinx releases, Firefox and WebKit, PDF/LaTeX and EPUB
  builders.
* Large multi-module projects. :doc:`performance` records one single-library run.
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
* Manual Java declaration directives are not provided; declarations come only
  from the extracted model through the ``java:auto*`` directives.
* External links use the Javadoc 9+ URL structure; Javadoc 8 member anchors are not
  supported. Roles mapped to external Javadoc without compiler metadata cannot
  check that the symbol exists.
* JPMS ``module-info.java`` inputs are rejected; several non-modular source roots
  are supported. Annotation processors and Lombok-like transformations are not run.
* Any input change re-extracts the whole project, and cache hits still hash all
  dependency bytes. Sphinx keeps only the current model in its cache; the CLI's
  ``--cache`` directory does not evict old entries.
* Sphinx can leave obsolete HTML files after a type is removed, so publish from a
  clean output directory. Each generated-page directory must belong to one Sphinx
  process at a time; that process's own ``-j`` workers are supported.

Evidence
--------

The `CI workflow <https://github.com/r4sky0/sphinx-java-autodoc/actions/workflows/ci.yml>`_
runs the operating system and Python matrix, the JDK and Sphinx integration tests
against the installed wheel, strict builds and Chromium checks in five themes. The
tests compare anchors with real standard-doclet output, check that the XML is
byte-identical across checkout locations, and check that extraction runs neither
static initializers nor annotation processors.

The Maven and Gradle consumers last passed on 2026-10-11 with Maven 3.10.0,
Gradle 9.1.0, Temurin 25.0.3, Python 3.12.13 and Sphinx 9.1.0 on macOS 26.4.1
arm64, including a strict parallel Sphinx build with an empty ``PATH``.
