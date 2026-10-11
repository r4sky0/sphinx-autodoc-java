Installation and usage
======================

Requirements: Python 3.12 or newer, Sphinx 9.1.x, and JDK 25.

From a clean checkout::

   python3 -m venv .venv
   . .venv/bin/activate
   pip install -e '.[test]'
   sphinx-build -W --keep-going docs docs/_build/html
   pytest

The build compiles the bundled doclet locally. It never downloads Java dependencies.

The first release is installed from this checkout or its built wheel; it has not
been published to PyPI. For a distributable package::

   pip install build
   python -m build
   pip install dist/sphinx_java_autodoc-0.1.0-py3-none-any.whl

Check ``java -version``, ``javac -version`` and ``javadoc --version``. If several
JDKs are installed, set ``java_jdk`` to the JDK 25 home directory. Extraction uses
the tools from the selected runtime's actual home. The project being documented
need not target Java 25: ``java_release = '17'`` selects source/API release 17.
Runtime compatibility is separate from source-release selection.

Standalone sources
------------------

The complete fixture is in ``examples/standalone/src``. From the repository root::

   sphinx-java-autodoc examples/standalone/src \
     --release 17 --warnings-as-errors \
     --cache build/java-cache -o build/api.xml

The extension also performs extraction during a Sphinx build. In ``docs/conf.py``:

.. code-block:: python

   extensions = ['sphinx_java_autodoc']
   java_sources = ['../src/main/java']
   java_classpath = ['../lib/dependency.jar']  # omit when unnecessary
   java_generate = 'api'

Add the generated index alongside your guides:

.. code-block:: rst

   Project documentation
   =====================

   .. toctree::
      :maxdepth: 2

      introduction
      tutorials
      api/index

Then run ``sphinx-build -W --keep-going docs docs/_build/html``.
Paths in ``java_sources``, ``java_classpath`` and ``java_model`` are relative to
``conf.py``. Each source entry may be a directory (recursively scanned) or a Java
file. The CLI uses paths relative to its working directory. Empty or missing source
roots and missing classpath entries are errors, not silently skipped inputs.

Explicit extraction and rendering
---------------------------------

For an existing build pipeline, extract XML first and use it in Sphinx:

.. code-block:: python

   extensions = ['sphinx_java_autodoc']
   java_model = '../build/api.xml'
   java_generate = 'api'

Do not also set ``java_sources``. Reading an existing model requires no JDK.
The build pipeline must rerun extraction when sources or dependencies change;
Sphinx can only detect changes in the supplied model. The extraction command
preserves the last successful output if compilation or strict diagnostics fail.

For direct doclet invocation, locate and compile the bundled source::

   python -c "from sphinx_java_autodoc.extractor import DOCLET; print(DOCLET)"
   javac -proc:none -encoding UTF-8 -d build/doclet /printed/path/SphinxDoclet.java
   javadoc -quiet -encoding UTF-8 -protected \
     -doclet sphinxjava.SphinxDoclet -docletpath build/doclet \
     --sphinx-output build/api.xml -sourcepath src/main/java \
     -classpath lib/dependency.jar com.example

Prefer the Python CLI for content caching, atomic output and warning handling.
The direct command takes ordinary Javadoc package or file inputs and does not
provide the Python wrapper's cache or publication safeguards.

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

Maven
-----

``examples/maven/pom.xml`` reuses the standalone source fixture. Resolve build
plugins and dependencies in an explicit preparation step. The extension itself
never invokes Maven::

   mvn -f examples/maven/pom.xml -DskipTests compile \
     org.apache.maven.plugins:maven-dependency-plugin:3.11.0:build-classpath \
     -Dmdep.includeScope=compile -Dmdep.outputFile=target/classpath.txt
   sphinx-java-autodoc examples/standalone/src \
     --classpath-file examples/maven/target/classpath.txt \
     -o build/maven-api.xml --cache build/java-cache --warnings-as-errors

For your own project, replace the fixture root with ``src/main/java``. If no
external dependencies exist, omit ``--classpath-file``. The
`Maven dependency plugin <https://maven.apache.org/plugins/maven-dependency-plugin/build-classpath-mojo.html>`_
writes platform-separated classpaths, including provided dependencies when compile
scope is selected. Compile/generate-sources are explicit project build steps and
may run project build plugins; extraction does not execute application code.

Gradle
------

``examples/gradle/build.gradle`` reuses the same sources and provides an explicit
``writeJavaAutodocClasspath`` task. With a Gradle distribution supporting JDK 25::

   gradle -p examples/gradle classes writeJavaAutodocClasspath
   sphinx-java-autodoc examples/standalone/src \
     --classpath-file examples/gradle/build/java-autodoc-classpath.txt \
     -o build/gradle-api.xml --cache build/java-cache --warnings-as-errors

For your project, the
`Java plugin <https://docs.gradle.org/current/userguide/java_plugin.html>`_
provides ``sourceSets.main.compileClasspath``. Write its ``asPath`` to a UTF-8 file;
pass source directories separately. No Gradle wrapper or automatic distribution
download is bundled here. Neither Maven nor Gradle was installed in the validation
environment; these integration recipes remain unexecuted.

Dependencies, generated sources and multiple modules
----------------------------------------------------

Pass dependency JARs or class directories through ``java_classpath`` (a list),
``--classpath`` (platform path separator), or ``--classpath-file``. Wildcard
classpath expansion is not supported: enumerate files explicitly. Dependencies
are never downloaded implicitly. A missing dependency results in compiler diagnostics
with the failing symbol and a classpath hint.

List several source roots to combine non-JPMS Maven/Gradle modules:

.. code-block:: python

   java_sources = [
       '../core/src/main/java',
       '../client/src/main/java',
       '../client/target/generated-sources/annotations',
   ]
   java_classpath = ['../lib/dependency.jar']

Produce generated sources before running Sphinx. No annotation processors execute
inside extraction; Lombok-like compiler AST transformations are not supported.
Do not include test sources unless they are part of the API you intend to publish.
JPMS ``module-info.java`` inputs are rejected with an actionable error in this
release; use non-modular roots or explicitly enumerate declaration files. Cross-module
JPMS identity, module paths and split packages are deferred.

A binary dependency is enough to resolve a reference or signature. To inherit its
Javadoc, supply its source as an additional source root. Such roots also become
eligible for generated pages; when you only want selected types, leave
``java_generate`` empty and use explicit directives.

Documentation fidelity and diagnostics
--------------------------------------

Supported traditional Javadoc content includes descriptions, ``@param`` (including
type parameters), ``@return``, ``@throws``/``@exception``, ``@see``, ``@since`` and
``@deprecated``. Inline ``code``, ``literal``, ``link``, ``linkplain`` and ``inheritDoc``
are processed from compiler trees. HTML paragraphs, nested ordered/unordered lists,
preformatted code, emphasis, strong text and absolute HTTP(S)/mailto links become
native nodes. Literal text is never interpreted as RST, and raw HTML is not emitted.

Overriding methods inherit omitted descriptions, parameters, returns and declared
throws documentation. Parameter matching is positional, so renamed parameters work.
Generic exception types are substituted through the compiler's view of the parent
method: ``Contract<E>`` implemented as ``Contract<IOException>`` can supply
``@throws IOException`` documentation. Method exception type parameters are matched
by position, and inherited throws labels use the overriding method's exception.
The default search follows the JDK 25 rule; ``{@inheritDoc SomeSupertype}`` selects
a supertype explicitly. Links in inherited prose resolve in the original author's
scope. Class and constructor comments do not inherit. Explicit unresolved inheritance
is visibly marked and warned; missing inherited parts also warn. This is not a full
replacement for standard Javadoc's DocLint or all standard-doclet synthesis.

``{@snippet}``, ``///`` Markdown comments, unsupported tags and unsupported HTML
produce warnings with an alternative or source symbol. Snippets are not executed or
expanded. Malformed comments and unresolved links also warn. Run strict builds::

   sphinx-build -W --keep-going docs docs/_build/html
   sphinx-java-autodoc src/main/java -o build/api.xml --warnings-as-errors

Warnings use ``java.extract``, ``java.html``, ``java.type``, ``java.member`` and related
categories. Sphinx's normal missing-reference diagnostics also apply. Suppression is
possible through normal Sphinx configuration, but suppressing a warning does not
supply missing content. JDK/compiler failures stop the build and preserve prior output.

Caching and parallelism
-----------------------

The Sphinx cache lives under ``<doctreedir>/java-cache``. The CLI defaults to
``.java-autodoc-cache`` or accepts ``--cache``. Fingerprints include source paths and
contents, classpath order and contents, source release, tool identity/JDK modules,
extension version and extractor code. Cache hits still hash inputs; this costs I/O
but catches edits even when timestamps are preserved. A changed input triggers
whole-project extraction and re-reading of consuming Sphinx documents.

Output contains no build timestamps or machine-specific source paths. Temporary
work directories and atomic replacement protect simultaneous extraction into one
cache. Sphinx ``-j 2`` reading/writing and domain inventory merges are tested. Separate
Sphinx processes must use separate source/output generation directories; sharing
one generated-page directory across independent builds is not supported.

Generated skeletons are written only when changed. Removed types leave the source
toctree and inventory; Sphinx can retain old HTML files in an existing output directory,
so publish from a clean output directory. Old content-addressed cache entries can be
removed when no build is using the cache; no background cache eviction is performed.
