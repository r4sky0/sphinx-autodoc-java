Configuration and reference
===========================

Use this page to look up settings, directive options and link syntax. For a first
build, start with :doc:`getting-started`. For dependencies and separate extraction,
see :doc:`build-integration`.

Sphinx configuration
--------------------

Set these values in ``conf.py``. Source, source lookup, classpath and model paths are relative to
that file; ``java_generate`` is relative to the Sphinx source directory.

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
     - Source lookup directories for dependency comments; not selected for publication.
   * - ``java_classpath``
     - ``[]``
     - Existing dependency JARs or class directories. No wildcard expansion.
   * - ``java_jdk``
     - ``""``
     - JDK 25 home; empty selects the runtime on ``PATH``.
   * - ``java_release``
     - ``""``
     - Source/API release; empty uses the selected JDK's default. Tested: 17, 21, 25.
   * - ``java_generate``
     - ``""``
     - Subdirectory for generated package/type pages, such as ``"api"``.
       Empty disables page generation; use explicit directives instead.
   * - ``java_visibility``
     - ``"protected"``
     - ``"public"`` for public declarations; ``"protected"`` also includes
       protected declarations.
   * - ``java_model``
     - ``""``
     - Pre-extracted XML model; mutually exclusive with ``java_sources``.
   * - ``java_external_javadoc``
     - ``{}``
     - Package prefixes mapped to external Javadoc roots; examples below.

Empty or missing source roots and missing classpath entries are errors. Leave
both ``java_sources`` and ``java_model`` unset when only consuming another site's
Java inventory through intersphinx. Such a site needs no JDK; generating local
API pages requires extracted types.

Directives and roles
--------------------

Use a fully qualified type name:

.. code-block:: rst

   .. java:autoclass:: com.example.Widget
      :members:
      :visibility: protected

With no ``:members:`` option, only the type declaration and documentation appear.
An empty ``:members:`` selects all declared public/protected members. A selection
uses **semicolons** so overloaded signatures can contain commas:

.. code-block:: rst

   .. java:autoclass:: com.example.Widget
      :members: find(java.lang.String,int); LABEL
      :exclude-members: old
      :visibility: public
      :no-index:

A bare member name selects every overload of that name; an exact signature selects
one. Use erased fully qualified parameter types and ``[]`` for varargs. Constructors
use ``<init>(...)``. ``protected`` includes public and protected; ``public`` excludes
protected declarations. Private and package-private declarations are never exported.
Public nested types inside protected enclosing types are also excluded in public
mode. Declaration signatures retain their original modifiers.
``@hidden`` declarations are omitted. Ancestor methods are not duplicated under each
subclass; overriding declarations inherit their comments, while other ancestor
methods remain documented on the declaring type. Nested types have their own pages.

``:no-index:`` creates an excerpt without registering duplicate anchors or inventory
entries. Use it when an object also appears in generated pages. Unknown selected
members and duplicate canonical documentation produce warnings.

.. code-block:: rst

   :java:type:`com.example.Widget`
   :java:type:`com.example.Widget.Nested`
   :java:method:`com.example.Widget#find(java.lang.String,int)`
   :java:method:`com.example.Widget#<init>()`
   :java:field:`com.example.Widget#LABEL`
   :java:package:`com.example`

``java:obj`` accepts any kind. Roles require fully qualified names; no import context
or short-name guessing is used. Omitting a method's parameter list works only when
there is one documented overload. Ambiguity warns instead of selecting arbitrarily.
In Java comments, ordinary Javadoc import-sensitive references are compiler-resolved.

``java:autopackage`` renders package comments from ``package-info.java`` and registers
the package. Set ``java_generate`` to generate its package index and type pages
automatically. Generated pages are owned through a content-hash manifest. Edited or
unowned files are never overwritten; put handwritten material outside that directory.

.. _external-javadoc:

External Javadoc and intersphinx
--------------------------------

Map package prefixes to documentation roots. The longest matching prefix wins:

.. code-block:: python

   java_external_javadoc = {
       'java': 'https://docs.oracle.com/en/java/javase/25/docs/api/{module}/',
       'vendor.api': 'https://vendor.example/docs/api/',
   }

Compiler-resolved links include package, nested type, module and member metadata.
``{module}`` is replaced with the referenced module, for example ``java.base``.
Javadoc 9+ member anchors are supported, including varargs and constructors. Javadoc
8's dash-style member anchors are deferred. URLs are generated without fetching
remote documentation or validating that the vendor publishes that symbol.

For roles that have no compiler metadata, map the **exact package** to a root
without a module placeholder, for example:

.. code-block:: python

   java_external_javadoc = {
       'java.lang': 'https://docs.oracle.com/en/java/javase/25/docs/api/java.base/',
   }

This permits ``:java:type:`java.lang.String``` even when no source comment refers
to it. For external members without metadata, use the published Javadoc fragment spelling,
including ``...`` for varargs and declared type variables where applicable. This
manual fallback cannot infer varargs from erased arrays or verify the symbol exists. Prefer compiler-resolved links.

Signature types use the same local, external and intersphinx resolution. When a
type has no documentation target, its signature text remains readable without a
missing-reference warning. Explicit roles and comment links still warn normally.

Every documented object is exported to ``objects.inv``. A second project can load
it using standard intersphinx:

.. code-block:: python

   extensions = ['sphinx_java_autodoc', 'sphinx.ext.intersphinx']
   intersphinx_mapping = {
       'library': ('https://docs.example/library/', '../library-html/objects.inv'),
   }

Then use the same Java roles. A roles-only consumer needs no Java sources or JDK.
Local inventory files make cross-project tests and offline builds deterministic;
normal intersphinx URL inventories may perform network requests independently.

For supported Javadoc tags, HTML and snippets, see :doc:`javadoc-support`.
