Supported Javadoc
=================

Write API documentation as traditional Javadoc comments. This page lists what
renders as native Sphinx content. Anything else produces a warning; see
:doc:`troubleshooting` for alternatives and :doc:`compatibility` for known limits.

Tags and HTML
-------------

Supported traditional Javadoc content includes descriptions, ``@param`` (including
type parameters), ``@return``, ``@throws``/``@exception``, ``@see``, ``@since`` and
``@deprecated``. Inline ``code``, ``literal``, ``link``, ``linkplain`` and ``inheritDoc``
are processed from compiler trees. HTML paragraphs, nested ordered/unordered lists,
preformatted code, emphasis, strong text and absolute HTTP(S)/mailto links become
native nodes. Literal text is never interpreted as RST, and raw HTML is not emitted.
HTML link attribute entities are decoded once, and ``<br>`` preserves line breaks
and inline formatting. Repeated ``@throws`` descriptions for the same exception
are retained in order, including when inherited.

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
