Example: Apache Commons Lang
============================

Browse the API in
`Furo <showcase/commons-lang/furo/index.html>`__,
`Read the Docs <showcase/commons-lang/rtd/index.html>`__,
`Alabaster <showcase/commons-lang/alabaster/index.html>`__ or
`Lumina <showcase/commons-lang/lumina/index.html>`__: the same generated pages in four
themes, with no theme-specific configuration. It's version |showcase-version| of
`Apache Commons Lang
<https://commons.apache.org/proper/commons-lang/>`_, about 260 source files,
generated from unmodified sources. Apache Commons Lang is licensed under the Apache
License 2.0; this site is not affiliated with the Apache Software Foundation.

It uses the :doc:`getting-started` configuration plus ``java_external_javadoc`` for
JDK links and ``sphinx.ext.linkcode`` for :ref:`source links <source-links>` to
GitHub at the pinned commit. For an example of every feature, see the
:doc:`gallery/index`. The build reports |showcase-total| warnings:

- |showcase-java.extract| ``java.extract``: overrides of JDK methods that cannot
  inherit their documentation, and links to libraries not on the classpath.
- |showcase-java.html| ``java.html``: headings and other unsupported HTML.
- |showcase-misc.highlighting_failure| highlighting failures: ``<pre>`` examples that
  are not Java.
- |showcase-ref| ``ref.*``: links to private members and to libraries not on the
  classpath.
