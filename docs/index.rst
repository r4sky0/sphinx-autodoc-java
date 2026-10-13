Publish your Java library with Sphinx
=====================================

``sphinx-java-autodoc`` puts your handwritten guides and an API reference generated
from your Java sources and Javadoc into one searchable Sphinx site.

**See the result first:** the :doc:`example <showcase>` is the complete public API
of Apache Commons Lang, generated from its unmodified sources. Open
:java:type:`StringUtils <org.apache.commons.lang3.StringUtils>` to see overloads,
HTML tables, ``{@value}`` constants and links to JDK types. The
:doc:`feature gallery <gallery/index>` shows each feature next to its source, and
:doc:`alternatives` compares other tools.

To adopt the extension, follow three steps:

1. :doc:`getting-started` from your sources.
2. :doc:`guide` that links into the reference.
3. :doc:`build-integration` from CI.

Extraction requires JDK 25; your library can still target Java 17 or 21. It never
runs application classes or annotation processors, and never downloads Java
dependencies. Settings, roles and limits are under **Reference**.

.. toctree::
   :caption: Evaluate
   :maxdepth: 1

   showcase
   gallery/index
   alternatives

.. toctree::
   :caption: Adopt
   :maxdepth: 1

   getting-started
   guide
   build-integration

.. toctree::
   :caption: Reference
   :maxdepth: 1

   usage
   javadoc-support
   compatibility
   troubleshooting

.. toctree::
   :caption: Project
   :maxdepth: 1

   performance
   design
