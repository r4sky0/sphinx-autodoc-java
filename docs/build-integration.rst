Build with dependencies and CI
==============================

Once :doc:`getting-started` works for a source root, give extraction the same
source and dependency inputs your Java compiler needs. The extension does not
invoke Maven or Gradle, run annotation processors, or resolve dependencies for you.
Prepare those inputs before running Sphinx.

Choose where extraction runs
----------------------------

* **During Sphinx:** set ``java_sources`` and ``java_classpath`` in ``conf.py``.
  This is the simplest path when JDK 25 is available on the documentation builder.
* **Before Sphinx:** run ``sphinx-java-autodoc`` in the Java build job, then pass
  its XML to Sphinx with ``java_model``. The Sphinx job needs no JDK.

For example, for a locally available dependency:

.. code-block:: python

   java_sources = ["../src/main/java"]
   java_classpath = ["../lib/dependency.jar", "../other-module/target/classes"]
   java_generate = "api"

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

Explicit extraction and rendering
---------------------------------

Use this when Java extraction runs in a separate job from Sphinx. From your
project root, with JDK 25 available:

.. code-block:: console

   sphinx-java-autodoc src/main/java --release 17 --warnings-as-errors \
     --cache build/java-cache -o build/api.xml

Add ``--classpath-file build/classpath.txt`` when dependencies are needed.
CLI paths are relative to the working directory. Then configure ``docs/conf.py``:

.. code-block:: python

   extensions = ['sphinx_java_autodoc']
   java_model = '../build/api.xml'
   java_generate = 'api'

Do not also set ``java_sources``. Reading an existing model requires no JDK.
The build pipeline must rerun extraction when sources or dependencies change;
Sphinx can only detect changes in the supplied model. The extraction command
preserves the last successful output if compilation or strict diagnostics fail.

Maven
-----

The Maven and Gradle recipes below are provided as integration examples; neither
has been executed in the recorded validation environment.

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

Publish the site from CI
------------------------

This GitHub Actions workflow builds strictly on every push to ``main`` and
deploys to GitHub Pages. In the repository settings, set **Pages → Source** to
**GitHub Actions**. Save it as ``.github/workflows/docs.yml``:

.. code-block:: yaml

   name: Documentation
   on:
     push:
       branches: [main]

   permissions:
     contents: read

   jobs:
     build:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v7
           with:
             persist-credentials: false
         - uses: actions/setup-java@v6
           with:
             distribution: temurin
             java-version: "25"
         - uses: actions/setup-python@v7
           with:
             python-version: "3.12"
         - run: python -m pip install "git+https://github.com/r4sky0/sphinx-java-autodoc.git"
         # Prepare java_classpath inputs and generated sources here, for example
         # with the Maven or Gradle commands below.
         - run: sphinx-build -W --keep-going -n docs docs/_build/html
         - uses: actions/upload-pages-artifact@v5
           with:
             path: docs/_build/html

     deploy:
       needs: build
       runs-on: ubuntu-latest
       permissions:
         pages: write
         id-token: write
       environment:
         name: github-pages
         url: ${{ steps.deployment.outputs.page_url }}
       steps:
         - id: deployment
           uses: actions/deploy-pages@v5

Each run starts from a clean output directory, so removed types do not leave old
pages behind. Install the extension from your own lockfile or requirements file
if you have one, and pin actions to commit SHAs if your project does. This
repository publishes its own site with the same JDK setup, strict build and
Pages actions; this standalone workflow has been checked with ``actionlint``
but has not run in another repository.

Caching and parallelism
-----------------------

The Sphinx cache lives under ``<doctreedir>/java-cache``. The CLI defaults to
``.java-autodoc-cache`` or accepts ``--cache``. Fingerprints include source paths and
contents, classpath order and contents, source release, tool identity/JDK modules,
extension version and extractor code. Cache hits still hash inputs; this costs I/O
but catches edits even when timestamps are preserved. A changed input triggers
whole-project extraction and re-reading of all Sphinx documents, including pages
containing only Java roles and directives for types that were previously missing.

Output contains no build timestamps or machine-specific source paths. Temporary
work directories and atomic replacement protect simultaneous extraction into one
cache. Sphinx ``-j 2`` reading/writing and domain inventory merges are tested. Separate
Sphinx processes must use separate source/output generation directories; sharing
one generated-page directory across independent builds is not supported.

Generated skeletons are written only when changed. Removed types leave the source
toctree and inventory; Sphinx can retain old HTML files in an existing output directory,
so publish from a clean output directory. Old content-addressed cache entries can be
removed when no build is using the cache; no background cache eviction is performed.

Direct doclet invocation
------------------------

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
