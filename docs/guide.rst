Working with widgets
====================

This is a handwritten guide. Its navigation, search, theme, and references are
shared with the generated API pages.

Choose an overload
------------------

Use :java:method:`demo.Widget#convert(int)` for numbers or
:java:method:`demo.Widget#convert(java.lang.String)` for text.
The text overload inherits the contract from :java:type:`demo.Transformer`.

.. code-block:: java

   Widget widget = new Widget();
   String text = widget.convert(42);

A timestamped location is represented by :java:type:`demo.Point`.
Nested types are referenced as :java:type:`demo.Widget.Nested`.
