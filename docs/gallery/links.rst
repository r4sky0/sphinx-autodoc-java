Links
=====

Roles in your pages
-------------------

Roles take fully qualified names. Overloaded methods need their erased parameter
types; constructors are named ``<init>``.

.. list-table::
   :header-rows: 1

   * - You write
     - You get
   * - ``:java:type:`demo.Widget```
     - :java:type:`demo.Widget`
   * - ``:java:type:`demo.Widget.Nested```
     - :java:type:`demo.Widget.Nested`
   * - ``:java:method:`demo.Widget#convert(int)```
     - :java:method:`demo.Widget#convert(int)`
   * - ``:java:method:`demo.Widget#<init>(java.lang.String)```
     - :java:method:`demo.Widget#<init>(java.lang.String)`
   * - ``:java:field:`demo.Widget#LABEL```
     - :java:field:`demo.Widget#LABEL`
   * - ``:java:package:`demo```
     - :java:package:`demo`
   * - ``:java:obj:`demo.Mode#FAST```
     - :java:obj:`demo.Mode#FAST`

Links in comments
-----------------

``{@link}`` and ``{@linkplain}`` targets are resolved by the compiler, with the
comment's own imports, and become native references. See the class comment on the
:doc:`comments` page.

External Javadoc
----------------

Types outside your sources, such as ``java.time.Instant`` in
:java:type:`demo.Point`, link to the Javadoc site mapped in
``java_external_javadoc``. Links to members use the same anchors as the standard
doclet.

Other Sphinx sites
------------------

Every documented declaration is in this site's ``objects.inv``, so other Sphinx
projects can link to it through ``sphinx.ext.intersphinx``. This documentation links
to the Commons Lang showcase that way, for example
:java:type:`org.apache.commons.lang3.StringUtils`.

Source links
------------

With ``sphinx.ext.linkcode`` and a ``linkcode_resolve`` function, each declaration
gets a ``[source]`` link. This site links to the fixture's files on GitHub. For the
``java`` domain, ``info`` holds:

``fullname``
   The canonical ID, such as ``demo.Widget#convert(int)``.
``source``
   The file relative to its source root, such as ``demo/Widget.java``. Nested types
   and members point into their top-level type's file.
``line``
   The declaration's first line, including annotations. It is empty for
   compiler-generated members such as ``Mode.values()``.

See :ref:`source-links` for the configuration.
