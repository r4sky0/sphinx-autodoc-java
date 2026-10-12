What produces a warning
=======================

Content the extension can't render faithfully produces a warning naming the
declaration, instead of disappearing from the page. These aren't live examples:
this site builds with ``-W``, so a real warning would fail it.

.. list-table::
   :header-rows: 1
   :widths: 35 45 20

   * - In your source or page
     - What the warning says
     - Category
   * - ``///`` Markdown comments
     - Markdown documentation comments are not supported
     - ``java.extract``
   * - An unknown block tag, such as ``@todo``
     - Unsupported block tag UNKNOWN_BLOCK_TAG
     - ``java.extract``
   * - External snippets, regions or markup
     - Unsupported snippet attributes or markup
     - ``java.extract``
   * - ``{@link}`` to a symbol the compiler can't find
     - Unresolved Javadoc reference
     - ``java.extract``
   * - ``{@inheritDoc}`` without ancestor source
     - Cannot resolve inheritDoc
     - ``java.extract``
   * - An HTML element outside the supported subset, such as ``<h3>``
     - Unsupported Javadoc HTML <h3>
     - ``java.html``
   * - A ``:members:`` entry that doesn't exist
     - Java member ... was not found
     - ``java.member``
   * - The same declaration documented twice without ``:no-index:``
     - Duplicate Java documentation
     - ``java.duplicate``
   * - An overloaded method named without parameters
     - Ambiguous Java reference
     - ``java.ambiguous``

Unsupported content stays in the page as literal text where possible, such as
``[unresolved inheritDoc]``. See :doc:`../troubleshooting` for fixes and
:doc:`../javadoc-support` for the supported content.
