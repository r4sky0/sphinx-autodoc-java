Design and release evidence
===========================

For contributors and maintainers evaluating the implementation. To use the
extension in your library, start with :doc:`getting-started`.

Compatibility and limits
------------------------

The :download:`validation report <validation.md>` records the tested environments,
supported behavior and known limits. Extraction requires JDK 25, independently
of the source/API release your library targets. Maven/Gradle recipes and untested
builders or browsers do not expand those compatibility claims.

Implementation records
----------------------

The release keeps one extraction backend and renders native Sphinx nodes. These
research and implementation records are provided as readable Markdown downloads:

* :download:`Research comparison and primary sources <research.md>`
* :download:`Architecture decision <adr-001.md>`
* :download:`Extraction experiment <experiment.md>`
* :download:`Versioned XML model <schema.md>`
* :download:`Compatibility, validation and limitations <validation.md>`
* :download:`Prioritized roadmap <roadmap.md>`

Contribute or prepare a release
-------------------------------

Use the :download:`contributor guide <../CONTRIBUTING.md>` for local setup,
checks, browser validation and the release procedure.
