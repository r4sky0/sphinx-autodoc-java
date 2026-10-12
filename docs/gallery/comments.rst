Javadoc comments
================

Comments are read from the compiler's comment trees and rendered as native Sphinx
content, so your theme styles them like any other page. Source comments are never
interpreted as reStructuredText, and no raw HTML is emitted.

HTML, inline tags and snippets
------------------------------

One class comment uses most of the supported content: paragraphs, emphasis, nested
lists, ``<pre>{@code ...}</pre>`` blocks, line breaks, external links, an inline
``{@snippet}``, a table with a caption, ``{@value}``, ``{@link}`` and
``{@linkplain}``, and the ``@see`` and ``@since`` tags.

.. literalinclude:: ../../examples/standalone/src/demo/Widget.java
   :language: java
   :start-at: /** A widget
   :end-at: public class Widget

.. java:autoclass:: demo.Widget
   :no-index:

Parameters, returns and exceptions
----------------------------------

``@param``, ``@return`` and ``@throws`` become fields. Type parameters get their own
field.

.. literalinclude:: ../../examples/standalone/src/demo/Widget.java
   :language: java
   :start-at: /** Builds a generic index.
   :end-at: List<? extends T> values

.. java:automethod:: demo.Widget#buildIndex(java.util.List,java.util.Map)
   :no-index:

API and implementation notes
----------------------------

The JDK's ``@apiNote``, ``@implSpec`` and ``@implNote`` tags use the standard
doclet's headings. ``@author`` and ``@version`` are left out, as the standard doclet
does by default.

.. literalinclude:: ../../examples/standalone/src/demo/Transformer.java
   :language: java
   :start-at: /** Transforms a value twice.
   :end-at: default T twice

.. java:automethod:: demo.Transformer#twice(java.lang.Object)
   :no-index:

Deprecation
-----------

``@deprecated`` produces the same notice as Sphinx's ``deprecated`` directive, and
the annotation stays in the signature.

.. literalinclude:: ../../examples/standalone/src/demo/Widget.java
   :language: java
   :start-at: /** Old entry point.
   :end-at: public void old()

.. java:automethod:: demo.Widget#old()
   :no-index:
