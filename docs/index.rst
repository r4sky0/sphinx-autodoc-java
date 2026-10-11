Publish your Java library with Sphinx
=====================================

Your library already has Java sources and Javadoc comments. Your users also need
examples that explain where to start and which API to choose.
``sphinx-java-autodoc`` brings both into one searchable Sphinx site: write the
guides yourself and generate the API reference from the same sources you maintain.

These docs are for **Java library maintainers adopting the extension**. Start
with :doc:`getting-started` to publish your first API pages, then follow
:doc:`guide` to connect those pages to a reader's task.

How it fits your project
------------------------

1. Keep signatures and API contracts in Java sources and traditional Javadoc.
2. Configure Sphinx with the source roots and any existing dependencies.
3. Write guides that show a task and link to the generated API for details.

Extraction requires JDK 25; your library can still target Java 17 or 21. Python
3.12+ and Sphinx 9.1.x are required. The extension never runs application classes
or annotation processors, and never downloads Java dependencies.

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
   troubleshooting

Explore the result
------------------

The :doc:`example API <api/index>` is generated from the small ``demo`` package
in this repository. Start with :java:type:`Widget <demo.Widget>` to see overloads,
inherited comments and links to standard Java types. This is a feature fixture,
not a library you need to install or use in your project.

.. toctree::
   :caption: Live example
   :maxdepth: 1

   Example Java API <api/index>

.. toctree::
   :caption: Project internals
   :maxdepth: 1

   design
