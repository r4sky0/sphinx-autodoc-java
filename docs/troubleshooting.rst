Troubleshoot a documentation build
==================================

Run ``sphinx-build -W --keep-going -n docs docs/_build/html`` from your project
root. Fix the first extraction or compiler error before chasing missing API
pages; those pages depend on successful extraction.

The build cannot find JDK 25
----------------------------

Check ``java -version``, ``javac -version`` and ``javadoc --version``. Set
``java_jdk = "/path/to/jdk-25"`` in ``conf.py`` if the default Java runtime is an
older JDK. Extraction uses the tools from the selected runtime's actual home.
``java_release = "17"`` selects the library's source/API release; it does not
allow extraction to run on JDK 17.

The compiler reports a missing package or symbol
------------------------------------------------

Check ``java_sources`` and ``java_classpath`` relative to ``conf.py``. Supply
existing dependency JARs or class directories, and produce generated sources
before extraction. List files explicitly; classpath wildcards are unsupported.
See :doc:`build-integration` for Maven, Gradle and multiple source roots.

A type, member or link is missing
---------------------------------

Check that the declaration's source is included and that visibility permits it.
Private, package-private and ``@hidden`` declarations are omitted. Methods that
are inherited without an override stay on the declaring ancestor's page.

In a handwritten guide, use a fully qualified target. Include parameter types
for overloaded methods, for example ``org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int)``.
A member selection uses semicolons between entries. See :doc:`usage` for the
exact role and directive syntax and external Javadoc configuration.

An excerpt produces duplicate-documentation warnings
----------------------------------------------------

Add ``:no-index:`` to the ``java:autoclass`` directive in your guide if the type
also has a generated API page. Keep one canonical location for each object.

Comments are incomplete or produce warnings
-------------------------------------------

Traditional Javadoc descriptions, common tags and plain inline ``{@snippet}``
bodies are supported; see :doc:`javadoc-support` for the supported content. ``///`` Markdown
comments, unsupported tags and unsupported HTML warn with an alternative or source
symbol. External/hybrid snippets, regions, IDs and markup actions warn and keep the
original tag as literal text; snippets are never executed. Malformed comments and
unresolved links also warn. Use traditional comments and supported markup for
content you need to publish.

To inherit a dependency's Javadoc, include its source as well as its binaries.
Those additional sources are also eligible for generated pages. Unresolved
explicit inheritance is marked visibly and warned; missing inherited parts also
warn. Class and constructor documentation does not inherit.

Warnings use ``java.extract``, ``java.html``, ``java.type``, ``java.member`` and
related Sphinx categories. Suppressing a warning does not supply missing content.
JDK/compiler failures stop the build and preserve prior output. For extraction
outside Sphinx, use ``--warnings-as-errors`` to fail on extraction diagnostics.
Run strict builds::

   sphinx-build -W --keep-going docs docs/_build/html
   sphinx-java-autodoc src/main/java -o build/api.xml --warnings-as-errors

The extension refuses to overwrite a generated page
---------------------------------------------------

Move your handwritten content outside the generated directory and back it up
before removing the edited file. The next build can recreate a missing generated
page. Keep API prose in Java comments and guide prose in handwritten ``.rst`` pages;
the generated-page manifest protects edited and unowned files from replacement.

A removed type still has an HTML page
-------------------------------------

Sphinx may retain old HTML in an existing output directory even after generated
sources and inventory entries are removed. Publish from a clean output directory.
Each independent Sphinx process also needs its own generated-source/output
directories; a single build's ``-j 2`` workers are supported.
