Directives in your own pages
============================

Generated pages are optional. These directives put Java documentation anywhere in a
handwritten page. Each example shows the reStructuredText and its result. See
:doc:`../usage` for every option.

A type with selected members
----------------------------

``:members:`` takes entries separated by semicolons, so overloads can include their
parameter types. A bare name selects every overload.

.. code-block:: rst

   .. java:autoclass:: demo.Widget
      :members: convert(int); LABEL; count
      :visibility: public
      :no-index:

.. java:autoclass:: demo.Widget
   :members: convert(int); LABEL; count
   :visibility: public
   :no-index:

``count`` is protected, so ``:visibility: public`` leaves it out.

All members but some
--------------------

An empty ``:members:`` selects every member; ``:exclude-members:`` removes some.

.. code-block:: rst

   .. java:autoclass:: demo.Mode
      :members:
      :exclude-members: values; valueOf
      :no-index:

.. java:autoclass:: demo.Mode
   :members:
   :exclude-members: values; valueOf
   :no-index:

A single member
---------------

.. code-block:: rst

   .. java:autofield:: demo.Widget#LABEL
      :no-index:

.. java:autofield:: demo.Widget#LABEL
   :no-index:

A summary table
---------------

``java:autosummary`` lists packages, types or members with links and their first
sentences, like ``sphinx.ext.autosummary``.

.. code-block:: rst

   .. java:autosummary::

      demo
      demo.Widget
      demo.Shape
      demo.Widget#convert(int)

.. java:autosummary::

   demo
   demo.Widget
   demo.Shape
   demo.Widget#convert(int)

Package documentation
---------------------

``java:autopackage`` renders the comment in ``package-info.java``. The generated
:java:package:`demo` page uses it.

.. code-block:: rst

   .. java:autopackage:: demo
