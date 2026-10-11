Write a guide your users can follow
===================================

A generated reference answers "What does this method accept and return?" Your
guide should answer "Which method should I use, and how do I get started?"
Keep the contract in Javadoc and put the task, choices and working example in
a handwritten Sphinx page.

This page uses the repository's ``demo`` fixture to show the pattern. Replace
its names and task with your library's real use case.

Start with a task and an expected result
----------------------------------------

Suppose a reader wants to turn an integer into decimal text. A short guide can
give them the right overload, runnable statements and the result:

.. topic:: Example guide: Convert a number to text

   Use :java:method:`convert(int) <demo.Widget#convert(int)>` on a
   :java:type:`Widget <demo.Widget>` when your input is an integer.

   .. code-block:: java

      import demo.Widget;

      // Inside your method:
      Widget widget = new Widget();
      String text = widget.convert(42);
      System.out.println(text); // 42

   If your input is already text, see
   :java:method:`convert(String) <demo.Widget#convert(java.lang.String)>`.
   Its documentation inherits the transformation contract from
   :java:type:`Transformer <demo.Transformer>`.

The example gives the reader a choice and a result before sending them into
the reference. Use the same sequence for your library: state the goal, show the
smallest working example, then link to parameters, return values and exceptions.

Link readable names to precise targets
--------------------------------------

Write Java roles in your ``.rst`` guide. An explicit label keeps the sentence
readable while the target identifies the exact overload:

.. code-block:: rst

   Use :java:method:`convert(int) <demo.Widget#convert(int)>`
   on a :java:type:`Widget <demo.Widget>`.

Use fully qualified names in targets. For overloaded methods, include the erased,
fully qualified parameter types, such as ``java.lang.String``. The label can use
the spelling a reader would use in Java code. See :doc:`usage` for constructors,
fields, nested types and member selection.

Include reference excerpts where they help
------------------------------------------

To include a type's Javadoc and selected members directly in a guide:

.. code-block:: rst

   .. java:autoclass:: demo.Widget
      :members: convert(int)
      :no-index:

``:no-index:`` lets the excerpt coexist with the canonical generated API page.
It still renders the type's description, so a link is often enough for a short
task guide. An empty ``:members:`` includes all declared members; omit the option
to include only the type's declaration and description.

Add your guide to the site
--------------------------

Save your page as ``docs/convert.rst`` and include it before the reference in
``docs/index.rst``:

.. code-block:: rst

   My Java library
   ===============

   .. toctree::
      :maxdepth: 2

      convert
      api/index

Rebuild with ``sphinx-build -W --keep-going -n docs docs/_build/html`` and follow
the links from your guide to the API. Guides and API pages share navigation,
search and the site's theme.

For your next guide, choose another question your users ask. For dependencies,
generated sources and CI, continue with :doc:`build-integration`.
