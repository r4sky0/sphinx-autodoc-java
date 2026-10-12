Declarations and signatures
===========================

Signatures come from the compiler, so they show exactly what JDK 25 accepts. Type
names in signatures link to their documentation, here or in external Javadoc.

Generics, arrays and varargs
----------------------------

Bounds, wildcards and intersection types are kept as declared. Arrays and varargs
keep their brackets and dots.

.. literalinclude:: ../../examples/standalone/src/demo/Widget.java
   :language: java
   :start-at: /** Combines array
   :end-at: public String[] combine

.. java:automethod:: demo.Widget#combine(int[][],java.lang.String[])
   :no-index:

Records
-------

Record components appear in the signature and are documented by the record's
``@param`` tags. The compiler-generated accessors are listed as members.

.. literalinclude:: ../../examples/standalone/src/demo/Point.java
   :language: java
   :start-at: /** A timestamped

.. java:autoclass:: demo.Point
   :members:
   :no-index:

Sealed types
------------

``sealed`` and the ``permits`` clause are part of the signature.

.. literalinclude:: ../../examples/standalone/src/demo/Shape.java
   :language: java
   :start-at: /** Something

.. java:autoclass:: demo.Shape
   :members:
   :no-index:

Enums
-----

Enum constants are fields. The generated ``values()`` and ``valueOf(String)``
methods are listed too, but have no source line to link to.

.. literalinclude:: ../../examples/standalone/src/demo/Mode.java
   :language: java
   :start-at: /** Execution mode.

.. java:autoclass:: demo.Mode
   :members:
   :no-index:

Annotation types
----------------

Elements show their default values, and meta-annotations their arguments.

.. literalinclude:: ../../examples/standalone/src/demo/Label.java
   :language: java
   :start-at: /** A source annotation.

.. java:autoclass:: demo.Label
   :members:
   :no-index:

Interfaces and default methods
------------------------------

Default methods carry the ``default`` modifier.

.. java:autoclass:: demo.Transformer
   :members:
   :no-index:

Nested types
------------

Nested types keep their qualified name, such as ``demo.Widget.Nested``, and get their
own generated page.

.. java:autoclass:: demo.Widget.Nested
   :members:
   :no-index:
