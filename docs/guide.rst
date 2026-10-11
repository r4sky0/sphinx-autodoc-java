Write a guide your users can follow
===================================

A generated reference answers "What does this method accept and return?" Your
guide should answer "Which method should I use, and how do I get started?"
Keep the contract in Javadoc and put the task, choices and working example in
a handwritten Sphinx page.

This page links into the :doc:`Apache Commons Lang API <showcase>` to show the
pattern. Replace its names and task with your library's real use case.

Start with a task and an expected result
----------------------------------------

Suppose a reader wants to shorten a long title. A short guide can give them the
right overload, runnable statements and the result:

.. topic:: Example guide: Shorten a title

   Use :java:method:`abbreviate(String, int) <org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int)>`
   on :java:type:`StringUtils <org.apache.commons.lang3.StringUtils>` to cut text
   from the end.

   .. code-block:: java

      import org.apache.commons.lang3.StringUtils;

      // Inside your method:
      String title = StringUtils.abbreviate("Now is the time for all good men", 15);
      System.out.println(title); // Now is the t...

   To keep a window around an offset instead, see
   :java:method:`abbreviate(String, int, int) <org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int,int)>`.

The example gives the reader a choice and a result before sending them into
the reference. Use the same sequence for your library: state the goal, show the
smallest working example, then link to parameters, return values and exceptions.

Link readable names to precise targets
--------------------------------------

Write Java roles in your ``.rst`` guide. An explicit label keeps the sentence
readable while the target identifies the exact overload:

.. code-block:: rst

   Use :java:method:`abbreviate(String, int) <org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int)>`
   on :java:type:`StringUtils <org.apache.commons.lang3.StringUtils>`.

Use fully qualified names in targets. For overloaded methods, include the erased,
fully qualified parameter types, such as ``java.lang.String``. The label can use
the spelling a reader would use in Java code. See :doc:`usage` for constructors,
fields, nested types and member selection.

Include reference excerpts where they help
------------------------------------------

To include a type's Javadoc and selected members directly in a guide:

.. code-block:: rst

   .. java:autoclass:: org.apache.commons.lang3.StringUtils
      :members: abbreviate(java.lang.String,int)
      :no-index:

``:no-index:`` lets the excerpt coexist with the canonical generated API page.
It still renders the type's description, so a link is often enough for a short
task guide. An empty ``:members:`` includes all declared members; omit the option
to include only the type's declaration and description.

Add your guide to the site
--------------------------

Save your page as ``docs/shorten.rst`` and include it before the reference in
``docs/index.rst``:

.. code-block:: rst

   My Java library
   ===============

   .. toctree::
      :maxdepth: 2

      shorten
      api/index

Rebuild with ``sphinx-build -W --keep-going -n docs docs/_build/html`` and follow
the links from your guide to the API. Guides and API pages share navigation,
search and the site's theme.

To link to JDK or dependency Javadoc, or to another Sphinx project's Java API,
configure :ref:`external Javadoc and intersphinx <external-javadoc>`.

For your next guide, choose another question your users ask. For dependencies,
generated sources and publishing from CI, continue with :doc:`build-integration`.
