Publish your first API pages
============================

Start with one source root and let Sphinx generate the reference. By the end,
you will have a local site with a page for each exported Java type. You do not
need to convert your Javadoc comments or maintain a second copy of the API.

This walkthrough assumes this layout. If you do not have Sphinx docs yet, create
the ``docs`` directory and the two files shown below. Run commands from the
project root:

.. code-block:: text

   my-library/
     src/main/java/          # your Java sources, including package-info.java
     docs/
       conf.py              # Sphinx configuration
       index.rst            # documentation home page

Use traditional Javadoc comments; see :doc:`javadoc-support` for what renders.
JPMS ``module-info.java`` inputs and Lombok-like transformations are unsupported.

Install the extension
---------------------

Use Python 3.12+ and **JDK 25 for documentation extraction**, even if your library
targets an older Java release; see :doc:`compatibility` for tested versions. Check
that ``java -version``, ``javac -version`` and ``javadoc --version`` select JDK 25.
Installing the extension also installs its compatible Sphinx dependency.

From an existing uv project:

.. code-block:: console

   uv add "sphinx-java-autodoc @ git+https://github.com/r4sky0/sphinx-java-autodoc.git"

Or install into an existing Python virtual environment:

.. code-block:: console

   python -m pip install "git+https://github.com/r4sky0/sphinx-java-autodoc.git"

The extension has not been published to PyPI yet, so install it from GitHub.

Point Sphinx at your sources
----------------------------

Add the following to ``docs/conf.py``. If you already have an ``extensions`` list,
append ``"sphinx_java_autodoc"`` to it instead of replacing the list.

.. code-block:: python

   project = "My Java library"
   extensions = ["sphinx_java_autodoc"]
   java_sources = ["../src/main/java"]
   java_release = "17"
   java_generate = "api"
   java_visibility = "public"

``java_sources`` is relative to ``conf.py``. Set ``java_release`` to your
library's source/API target. Omitting it uses the selected JDK's default release. If JDK 25 is not on
``PATH``, add ``java_jdk = "/path/to/jdk-25"``.

``java_generate`` creates pages in ``docs/api/``: an index, a page per package and
a page per type, titled with its name inside the package, such as
``Widget.Nested``. ``java_visibility = "public"`` focuses the reference on the
public API. Use ``"protected"`` to also document
extension points for subclass authors.

If your sources depend on other libraries, add their JARs or class directories
to ``java_classpath`` before building; see :doc:`build-integration`.

Put the API in your navigation
------------------------------

Create ``docs/index.rst``, or add ``api/index`` to its existing toctree:

.. code-block:: rst

   My Java library
   ===============

   .. toctree::
      :maxdepth: 2

      api/index

Build and inspect the site
--------------------------

.. code-block:: console

   uv run sphinx-build -W --keep-going -n docs docs/_build/html

With a virtual environment activated, run the same command without ``uv run``.
Open ``docs/_build/html/index.html``, follow **Java API**, choose a package,
then open a type. You should see its declaration, Javadoc description and
public members. ``-W`` makes warnings fail the build, and ``-n`` checks references.
If the build fails, use :doc:`troubleshooting` to find the next step.

Edit a Javadoc description and rebuild to see it update. The extension compiles
its bundled doclet locally and caches extraction; it does not need a separate
doclet download or an application run.

Keep API contracts and guides in their own places
-------------------------------------------------

Edit Java comments to change the generated reference. Keep handwritten pages
outside ``docs/api/``: the extension owns that directory and refuses to overwrite
edited or unowned pages.

You now have the reference. Continue with :doc:`guide` to help a reader choose
an API and complete a task. When the local build works, :doc:`build-integration`
shows how to publish it from CI.
