Generate your API pages
=======================

This walkthrough ends with a local site that has a page for each Java type in one
source root. It assumes this layout, with commands run from the project root:

.. code-block:: text

   my-library/
     src/main/java/          # your Java sources, including package-info.java
     docs/
       conf.py              # Sphinx configuration
       index.rst            # documentation home page

Use traditional Javadoc comments; see :doc:`javadoc-support`. JPMS
``module-info.java`` inputs and Lombok-like transformations are unsupported.

Install the extension
---------------------

You need Python 3.12+ and JDK 25 for extraction, even if your library targets an
older Java release. Check that ``java -version``, ``javac -version`` and
``javadoc --version`` report JDK 25. The extension installs a compatible Sphinx.

.. code-block:: console

   uv add sphinx-java-autodoc
   # or, in an existing virtual environment:
   python -m pip install sphinx-java-autodoc

Point Sphinx at your sources
----------------------------

Add this to ``docs/conf.py``, appending to an existing ``extensions`` list if you
have one:

.. code-block:: python

   project = "My Java library"
   extensions = ["sphinx_java_autodoc"]
   java_sources = ["../src/main/java"]
   java_release = "17"
   java_generate = "api"
   java_visibility = "public"

- ``java_sources`` is relative to ``conf.py``.
- ``java_release`` is your library's target release; omitted, the JDK default applies.
- ``java_generate`` writes an index, package pages and type pages to ``docs/api/``.
- ``java_visibility = "public"`` documents the public API; ``"protected"`` adds
  extension points for subclass authors.

If JDK 25 is not on ``PATH``, add ``java_jdk = "/path/to/jdk-25"``. If your sources
depend on other libraries, see :doc:`build-integration`.

Add the API to your navigation
------------------------------

Create ``docs/index.rst``, or add ``api/index`` to its existing toctree:

.. code-block:: rst

   My Java library
   ===============

   .. toctree::
      :maxdepth: 2

      api/index

Build the site
--------------

.. code-block:: console

   uv run sphinx-build -W --keep-going -n docs docs/_build/html

``-W`` turns warnings into errors and ``-n`` checks references. Open
``docs/_build/html/index.html`` and follow **Java API** to a type page. If the
build fails, see :doc:`troubleshooting`.

Edit Java comments to change the reference. Keep handwritten pages outside
``docs/api/``: the extension owns that directory and refuses to overwrite edited
or unowned files there.

Next, :doc:`guide` shows how to write a task guide that links into the reference.
