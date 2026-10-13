Write a task guide
==================

The generated reference says what a method accepts and returns. A guide tells the
reader which method to use for their task. Keep the contract in Javadoc and put
the task, the choice and a working example in a handwritten page.

Start with a task and its result
--------------------------------

This example guide links into the :doc:`Apache Commons Lang API <showcase>`:

.. topic:: Example guide: Shorten a title

   Use :java:method:`abbreviate(String, int) <org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int)>`
   on :java:type:`StringUtils <org.apache.commons.lang3.StringUtils>` to cut text
   from the end.

   .. code-block:: java

      String title = StringUtils.abbreviate("Now is the time for all good men", 15);
      System.out.println(title); // Now is the t...

   To keep a window around an offset instead, see
   :java:method:`abbreviate(String, int, int) <org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int,int)>`.

State the goal, show the smallest working example, then link to the reference
for parameters, return values and exceptions.

Link readable names to exact targets
------------------------------------

.. code-block:: rst

   Use :java:method:`abbreviate(String, int) <org.apache.commons.lang3.StringUtils#abbreviate(java.lang.String,int)>`
   on :java:type:`StringUtils <org.apache.commons.lang3.StringUtils>`.

The label is what the reader sees. The target uses fully qualified names, and for
overloads the erased, fully qualified parameter types. See :doc:`usage` for
constructors, fields and nested types, and :ref:`external-javadoc` for links to
the JDK or other projects.

Include a reference excerpt
---------------------------

.. code-block:: rst

   .. java:autoclass:: org.apache.commons.lang3.StringUtils
      :members: abbreviate(java.lang.String,int)
      :no-index:

``:no-index:`` lets the excerpt coexist with the generated API page. The excerpt
includes the type's full description, so a link is often enough.

Add the guide to the site
-------------------------

Save the page as ``docs/shorten.rst`` and list it before the reference:

.. code-block:: rst

   .. toctree::
      :maxdepth: 2

      shorten
      api/index

Guides and API pages share navigation, search and the theme. Next,
:doc:`build-integration` covers dependencies and publishing from CI.
