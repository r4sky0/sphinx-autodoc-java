Supported Javadoc
=================

Write API documentation as traditional Javadoc comments. This page lists what
renders as native Sphinx content. Anything else produces a warning; see
:doc:`troubleshooting` for alternatives and :doc:`compatibility` for known limits.

Tags and HTML
-------------

Supported traditional Javadoc content includes descriptions, ``@param`` (including
type parameters), ``@return``, ``@throws``/``@exception``, ``@see``, ``@since`` and
``@deprecated``, plus the JDK's ``@apiNote``, ``@implSpec`` and ``@implNote`` notes,
which use the standard doclet's headings and are not inherited. ``@author``,
``@version`` and the ``@serial`` tags are omitted without a warning, as the standard
doclet does by default; other custom tags warn. Inline ``code``, ``literal``, ``link``, ``linkplain``, ``value`` and
``inheritDoc`` are processed from compiler trees. HTML paragraphs, nested
ordered/unordered lists, tables, preformatted code, emphasis, strong text and absolute HTTP(S)/mailto links become
native nodes. Literal text is never interpreted as RST, and raw HTML is not emitted.
HTML link attribute entities are decoded once, and ``<br>`` preserves line breaks
and inline formatting. Repeated ``@throws`` descriptions for the same exception
are retained in order, including when inherited.

Constant values
---------------

``{@value}`` shows a constant in Java source form, as the standard doclet does:
strings are quoted and escaped, characters quoted, and ``long``/``float`` values keep
their ``L``/``f`` suffix. ``{@value Type#FIELD}`` links to the field, including external
Javadoc fields such as ``Double#MAX_VALUE``; bare ``{@value}`` in a constant's own
comment is plain text. An optional ``java.util.Formatter`` format, such as
``{@value %x #MASK}``, is applied with the root locale. References to non-constant
fields, bare ``{@value}`` outside a constant and invalid formats warn.

Tables
------

HTML tables become native Sphinx tables with ``<caption>`` as the table title. Rows in
``<thead>``, or leading rows that contain only ``<th>`` cells, form the header.
``colspan`` and ``rowspan`` are kept, short rows are padded, and HTML's optional
``</td>``, ``</th>`` and ``</tr>`` end tags are inferred. Cells can contain paragraphs,
lists, code and nested tables. ``class``, ``summary`` and ``border`` on ``<table>`` and
``scope`` on cells are accepted but have no effect: themes style tables. Other
attributes and text outside cells warn. ``<th>`` cells outside the header render as
ordinary cells. Wide tables scroll horizontally within the content column, and code in
cells is not wrapped. Text from ``{@literal}`` and ``{@value}`` keeps straight quotes
because Sphinx's smart quotes are not applied to it.

Inherited documentation
-----------------------

Overriding methods inherit omitted descriptions, parameters, returns and declared
throws documentation. Parameter matching is positional, so renamed parameters work.
Generic exception types are substituted through the compiler's view of the parent
method: ``Contract<E>`` implemented as ``Contract<IOException>`` can supply
``@throws IOException`` documentation. Method exception type parameters are matched
by position, and inherited throws labels use the overriding method's exception.
The default search follows the JDK 25 rule; ``{@inheritDoc SomeSupertype}`` selects
a supertype explicitly. Links in inherited prose resolve in the original author's
scope. Class and constructor comments do not inherit. Explicit unresolved inheritance
is visibly marked and warned; missing inherited parts also warn. This is not a full
replacement for standard Javadoc's DocLint or all standard-doclet synthesis.

Snippets
--------

Plain inline snippets become native literal blocks, with Java highlighting by
default. An optional ``lang`` selects a Sphinx/Pygments language (such as ``text``):

.. code-block:: java

   /** Example:
    * {@snippet lang="java" :
    *     System.out.println("Hello");
    * }
    */

Indentation follows JDK ``String.stripIndent`` rules, including the closing brace's
indentation. Snippet content is literal: HTML entities, Javadoc tags and RST syntax
inside the body are preserved rather than interpreted. Snippets are never executed.
External/hybrid snippets (``file``/``class``), regions, IDs, duplicate attributes and
markup actions (``@highlight``, ``@replace``, ``@link``, ``@start``, ``@end``) warn
and retain the original tag as literal text. Markup detection is conservative:
reserved markup tags following ``//`` or ``#`` also warn inside quoted examples.

Inline return descriptions
--------------------------

A method comment beginning with ``{@return description}`` produces both the
introductory "Returns description." sentence and a Returns field. Inline markup
and inherited return descriptions are preserved in both places. The conformance
suite compares these results with the JDK standard doclet, including inheritance
between inline and block return tags.
