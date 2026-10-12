Inherited documentation
=======================

An overriding method inherits the parts of its comment that it leaves out, following
the JDK 25 search order. ``{@inheritDoc}`` copies a part explicitly. Inheritance
follows parameter positions, so a renamed parameter keeps its own name as the label.

``Transformer`` documents the contract:

.. literalinclude:: ../../examples/standalone/src/demo/Transformer.java
   :language: java
   :start-at: /** Transforms a value using
   :end-at: T convert(T input)

``Widget`` overrides it with ``{@inheritDoc}`` and renames the parameter:

.. literalinclude:: ../../examples/standalone/src/demo/Widget.java
   :language: java
   :start-at: /** {@inheritDoc}
   :end-at: @Override public String convert

.. java:automethod:: demo.Widget#convert(java.lang.String)
   :no-index:

Links in inherited prose still resolve where the original author wrote them. Both
``@throws`` descriptions of the same exception are kept.

When documentation can't be inherited, for example because the ancestor is only on
the classpath as a binary, the build warns instead of silently leaving the part
out. Add the ancestor's sources with ``java_sourcepath``; see
:doc:`../build-integration`.
