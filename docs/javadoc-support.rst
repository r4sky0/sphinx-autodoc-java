Supported Javadoc
=================

These traditional Javadoc constructs render as native Sphinx content. Anything
else produces a warning; see :doc:`troubleshooting`. Comment text is never
interpreted as reStructuredText, and no raw HTML is emitted.

Tags and HTML
-------------

- Block tags: ``@param`` (including type parameters), ``@return``,
  ``@throws``/``@exception``, ``@see``, ``@since`` and ``@deprecated``.
- JDK notes: ``@apiNote``, ``@implSpec`` and ``@implNote``, with the standard
  doclet's headings. They are not inherited.
- Inline tags: ``code``, ``literal``, ``link``, ``linkplain``, ``value``,
  ``inheritDoc``, ``return`` and plain inline ``snippet``.
- HTML: paragraphs, nested lists, tables, ``<pre>``, emphasis, strong text,
  ``<br>`` and absolute HTTP(S) or mailto links.

``@author``, ``@version`` and the ``@serial`` tags are omitted silently, as in the
standard doclet's default output. Other custom tags warn.

Text reads as in the standard doclet. A link without a label shows
``Map.Entry``, ``String.format(String, Object...)``, or ``of(L, R)`` for a member of
the same type. Sphinx's smart quotes are off, so quotes and ``...`` stay as written.
``@throws`` names link to the exception type.

Constant values
---------------

``{@value}`` shows a constant in Java source form, as the standard doclet does:
quoted strings and characters, and ``L``/``f`` suffixes. ``{@value Type#FIELD}``
links to the field, including JDK fields such as ``Double#MAX_VALUE``. A format
such as ``{@value %x #MASK}`` is applied with the root locale. Non-constant fields
and invalid formats warn.

Tables
------

HTML tables become Sphinx tables. ``<caption>`` becomes the title, and ``<thead>``
rows or leading all-``<th>`` rows form the header. ``colspan``, ``rowspan``,
omitted end tags and nested content work. Styling attributes are ignored because
the theme styles tables; other attributes warn. Wide tables scroll horizontally.

Inherited documentation
-----------------------

An overriding method inherits an omitted description, parameters, return and
declared throws from its ancestor, following the JDK 25 search order.
``{@inheritDoc SomeSupertype}`` picks a supertype explicitly. Parameters match by
position, generic exception types are substituted, and links resolve in the
ancestor's scope. Class and constructor comments do not inherit. Unresolved
inheritance is marked in the output and warns.

The ancestor's source must be available: in ``java_sources`` or
``java_sourcepath``.

Snippets
--------

Plain inline snippets become code blocks, highlighted as Java unless ``lang``
says otherwise:

.. code-block:: java

   /** Example:
    * {@snippet lang="java" :
    *     System.out.println("Hello");
    * }
    */

Indentation follows ``String.stripIndent``. The body is shown literally and never
executed. External snippets (``file``/``class``), regions, IDs and markup tags such
as ``@highlight`` warn and keep the original tag as text.

Inline return
-------------

A comment starting with ``{@return description}`` produces both the "Returns
description." first sentence and a Returns field, as the standard doclet does.
