Configuration reference
=======================

Settings, directive options and link syntax. For a first build, start with
:doc:`getting-started`.

Sphinx configuration
--------------------

Set these in ``conf.py``. Paths are relative to ``conf.py``, except
``java_generate``, which is relative to the Sphinx source directory.

.. list-table::
   :header-rows: 1
   :widths: 25 20 55

   * - Setting
     - Default
     - Purpose
   * - ``java_sources``
     - ``[]``
     - Java files or source roots; directories are scanned recursively.
   * - ``java_sourcepath``
     - ``[]``
     - Source directories used only for lookup and inherited comments; no pages.
   * - ``java_classpath``
     - ``[]``
     - Dependency JARs or class directories. No wildcards.
   * - ``java_encoding``
     - ``"UTF-8"``
     - Source file encoding, as Javadoc's ``-encoding`` accepts it.
   * - ``java_exclude_packages``
     - ``[]``
     - Packages, with their subpackages, left out of the pages like Javadoc's
       ``-exclude``. They still compile; an entry matching no package warns.
   * - ``java_jdk``
     - ``""``
     - JDK 25 home; empty uses the runtime on ``PATH``.
   * - ``java_release``
     - ``""``
     - Source/API release; empty uses the JDK default. Tested: 17, 21, 25.
   * - ``java_generate``
     - ``""``
     - Directory for generated pages, such as ``"api"``. Empty generates no pages.
   * - ``java_visibility``
     - ``"protected"``
     - ``"public"``, or ``"protected"`` for public plus protected declarations.
   * - ``java_model``
     - ``""``
     - Pre-extracted XML model; excludes ``java_sources``.
   * - ``java_external_javadoc``
     - ``{}``
     - Package prefixes mapped to external Javadoc roots; see below.
   * - ``java_maximum_signature_line_length``
     - ``None``
     - Signatures longer than this put each parameter on its own line. Unset uses
       Sphinx's ``maximum_signature_line_length``.

Empty or missing source roots and missing classpath entries are errors. A site that only links to
another site's Java API through intersphinx leaves ``java_sources`` and
``java_model`` unset and needs no JDK.

Directives
----------

.. code-block:: rst

   .. java:autoclass:: com.example.Widget
      :members: find(java.lang.String,int); LABEL
      :exclude-members: old
      :visibility: public
      :no-index:

- Without ``:members:``, only the type's declaration and description appear. An
  empty ``:members:`` includes all declared members.
- Separate selected members with **semicolons**, because signatures contain
  commas. A bare name selects every overload; a signature selects one.
- ``:no-index:`` renders an excerpt without registering anchors or inventory
  entries. Use it when the object also has a generated page.
- Unknown members and duplicate documentation warn.

Other directives work the same way:

.. code-block:: rst

   .. java:automethod:: com.example.Widget#find(java.lang.String,int)
   .. java:autofield:: com.example.Widget#LABEL
   .. java:autopackage:: com.example

   .. java:autosummary::

      com.example
      com.example.Widget
      com.example.Widget#find(java.lang.String,int)

``java:autopackage`` renders the ``package-info.java`` comment.
``java:autosummary`` lists each entry with a link and its first sentence; unknown
entries warn as ``java.summary``. As in Javadoc, members are listed with their
declared parameters, and methods and fields get a column with their modifiers and
type, such as ``static <L, R> Pair<L, R>``. Generated pages consist of these directives.

What gets documented
--------------------

- Private and package-private declarations are never shown, and ``@hidden``
  declarations are omitted. ``public`` visibility also omits public types nested in
  protected types.
- Only declared members are listed. An overriding method inherits its ancestor's
  comment; other inherited methods stay on the declaring type's page.
- As in Javadoc, an overriding method notes what it implements or overrides:
  "Specified by: ``convert`` in interface ``Transformer``", or "Overrides:
  ``hashCode`` in class ``Object``".
- Nested types get their own pages.
- Signatures show only ``@Documented`` annotations, as the standard doclet does, so
  ``@Override`` and ``@SuppressWarnings`` are left out.

Roles
-----

.. code-block:: rst

   :java:type:`com.example.Widget`
   :java:type:`com.example.Widget.Nested`
   :java:method:`com.example.Widget#find(java.lang.String,int)`
   :java:method:`com.example.Widget#<init>()`
   :java:field:`com.example.Widget#LABEL`
   :java:package:`com.example`

``java:obj`` accepts any kind. Targets are fully qualified: there are no imports
or short-name guessing. Parameters are erased, fully qualified types, with ``[]``
for varargs; constructors are ``<init>``. A method without a parameter list
resolves only when it has one overload; otherwise it warns. References inside Java
comments are resolved by the compiler as usual.

.. _source-links:

Source links
------------

Enable `sphinx.ext.linkcode <https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html>`_
to add a ``[source]`` link to each declaration. For the ``java`` domain, ``info``
holds ``fullname`` (the canonical ID), ``source`` (the file path relative to its
source root, such as ``com/example/Widget.java``) and ``line``:

.. code-block:: python

   extensions = ['sphinx_java_autodoc', 'sphinx.ext.linkcode']

   def linkcode_resolve(domain, info):
       if domain != 'java' or not info['line']:
           return None
       return (
           'https://github.com/example/project/blob/main/src/main/java/'
           f"{info['source']}#L{info['line']}"
       )

``line`` is empty for packages and for compiler-generated members, such as an enum's
``values()``.
With several source roots, choose the root in ``linkcode_resolve``, for example by
checking which root contains ``source``.

.. _external-javadoc:

External Javadoc and intersphinx
--------------------------------

Map package prefixes to Javadoc roots; the longest prefix wins:

.. code-block:: python

   java_external_javadoc = {
       'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{module}/',
       'vendor.api': 'https://vendor.example/docs/api/',
   }

``{module}`` becomes the referenced module, such as ``java.base``. Links use the
Javadoc 9+ URL structure; Javadoc 8 anchors are not supported. URLs are built
without fetching or checking the remote site.

A role that no source comment references has no module metadata. For those, map
the exact package without ``{module}``:

.. code-block:: python

   java_external_javadoc = {
       'java.lang': 'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/',
   }

For external members written by hand, use the Javadoc fragment spelling: ``...``
for varargs and declared type variables. The extension cannot check these.

Every documented object is in ``objects.inv``, so another Sphinx project can link
to it with intersphinx and the same Java roles, without sources or a JDK:

.. code-block:: python

   extensions = ['sphinx_java_autodoc', 'sphinx.ext.intersphinx']
   intersphinx_mapping = {
       'library': ('https://docs.example/library/', None),
   }

For supported Javadoc tags, HTML and snippets, see :doc:`javadoc-support`.
