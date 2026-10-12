Publish your Java library with Sphinx
=====================================

Your library already has Java sources and Javadoc comments. Your users also need
examples that explain where to start and which API to choose.
``sphinx-java-autodoc`` brings both into one searchable Sphinx site: write the
guides yourself and generate the API reference from the same sources you maintain.

**See the result first:** the :doc:`example API <showcase>` is the complete
public API of Apache Commons Lang, generated from its unmodified sources and
Javadoc comments without running the library. Open
:java:type:`StringUtils <org.apache.commons.lang3.StringUtils>` to see overloads,
HTML tables, ``{@value}`` constants and links to standard Java types.

These docs are for **Java library maintainers adopting the extension**:

1. :doc:`getting-started`: install the extension and generate API pages from
   your sources.
2. :doc:`guide`: help a reader pick an API and complete a task, linking into
   the reference.
3. :doc:`build-integration`: add dependencies and generated sources, then
   publish the site from CI.

Extraction requires JDK 25; your library can still target Java 17 or 21. See
:doc:`compatibility` for tested versions and known limits. The extension never
runs application classes or annotation processors, and never downloads Java
dependencies.

.. toctree::
   :caption: Publish your documentation
   :maxdepth: 1

   getting-started
   guide
   build-integration

.. toctree::
   :caption: Reference and help
   :maxdepth: 1

   usage
   javadoc-support
   compatibility
   performance
   troubleshooting

.. toctree::
   :caption: Live example
   :maxdepth: 1

   showcase

.. toctree::
   :caption: Project internals
   :maxdepth: 1

   design
