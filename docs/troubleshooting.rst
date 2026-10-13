Troubleshooting
===============

Fix the first extraction or compiler error first: missing API pages usually
follow from it.

The build cannot find JDK 25
----------------------------

Check ``java -version``, ``javac -version`` and ``javadoc --version``, or set
``java_jdk = "/path/to/jdk-25"`` in ``conf.py``. ``java_release = "17"`` sets the
library's target release; extraction still runs on JDK 25.

The compiler reports a missing package or symbol
------------------------------------------------

Add the dependency's JAR or class directory to ``java_classpath`` (paths relative
to ``conf.py``, no wildcards), and generate sources before the build. See
:doc:`build-integration`.

A type, member or link is missing
---------------------------------

- Check that the source is in ``java_sources`` and that ``java_visibility``
  includes it. Private, package-private and ``@hidden`` declarations are omitted.
- Inherited methods without an override appear on the ancestor's page.
- Role targets must be fully qualified, with parameter types for overloads:
  ``org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int)``.
  Separate ``:members:`` entries with semicolons. See :doc:`usage`.

An excerpt produces duplicate-documentation warnings
----------------------------------------------------

Add ``:no-index:`` to the ``java:autoclass`` directive in your guide when the type
also has a generated page.

Comments are incomplete or produce warnings
-------------------------------------------

Unsupported tags, HTML, ``///`` Markdown comments and advanced snippets warn with
the symbol; see :doc:`javadoc-support`. To inherit a dependency's Javadoc, add its
sources to ``java_sourcepath``.

Warnings use the ``java.extract``, ``java.html``, ``java.type``, ``java.member``
and related categories. Suppressing a warning does not add the missing content.
Outside Sphinx, ``--warnings-as-errors`` makes extraction diagnostics fail.

The extension refuses to overwrite a generated page
---------------------------------------------------

You edited a file in the generated directory, or put your own file there. Move
your content to a handwritten page, then delete the file; the next build
recreates it.

A removed type still has an HTML page
-------------------------------------

Sphinx keeps old HTML files in an existing output directory. Publish from a clean
output directory.
