:orphan:

Reference layout
================

Native Sphinx objects with the same fields as the Java fixture. The browser checks
use this page as each theme's own layout for object descriptions.

.. py:class:: Widget(label)

   A widget with a unified API.

   :param label: the label

   .. py:method:: build_index(values, fallback)

      Builds a generic index.

      :Type parameters: **<T>** – comparable numeric key
      :param values: input values
      :param fallback: default entries
      :returns: grouped entries
      :Throws: **IllegalArgumentException** – for invalid input
      :See also: :py:meth:`Widget.build_index`
