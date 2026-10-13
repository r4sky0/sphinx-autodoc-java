Add dependencies and publish
============================

Extraction needs the same sources and dependencies as your Java compiler. The
extension never invokes Maven or Gradle, runs annotation processors or downloads
dependencies, so prepare those inputs before running Sphinx.

Choose where extraction runs
----------------------------

- **During Sphinx:** set ``java_sources`` and ``java_classpath`` in ``conf.py``.
  The documentation builder needs JDK 25.
- **Before Sphinx:** run the ``sphinx-java-autodoc`` command in your Java build and
  pass its XML to Sphinx with ``java_model``. The Sphinx job needs no JDK.

Dependencies and generated sources
----------------------------------

.. code-block:: python

   java_sources = [
       "../core/src/main/java",
       "../client/src/main/java",
       "../client/target/generated-sources/annotations",
   ]
   java_classpath = ["../lib/dependency.jar", "../other-module/target/classes"]
   java_sourcepath = ["../dependency-sources"]
   java_generate = "api"

- ``java_sources`` takes several roots, so non-JPMS modules can share one site.
  Leave out test sources unless they are part of your API.
- ``java_classpath`` lists JARs and class directories explicitly; wildcards are not
  expanded. A missing dependency produces a compiler error naming the symbol.
- ``java_sourcepath`` adds dependency sources so their Javadoc can be inherited,
  without generating pages for them. Its contents are part of the cache key.
- Generate sources (annotation processors, templates) in your build first.
  Lombok-like AST transformations are not supported.
- JPMS ``module-info.java`` inputs are rejected; use non-modular source roots.

Extract before Sphinx
---------------------

With JDK 25, from your project root:

.. code-block:: console

   sphinx-java-autodoc src/main/java --release 17 --warnings-as-errors \
     --classpath-file build/classpath.txt --cache build/java-cache -o build/api.xml

Then, in ``docs/conf.py``, without ``java_sources``:

.. code-block:: python

   extensions = ['sphinx_java_autodoc']
   java_model = '../build/api.xml'
   java_generate = 'api'

CLI paths are relative to the working directory. ``--classpath`` takes a
platform-separated path. ``--sourcepath`` and ``--exclude-package`` can repeat, and
``--encoding`` matches ``java_encoding``. If compilation or a
strict check fails, the previous output is kept. Your pipeline must rerun
extraction when sources change, since Sphinx only sees the model.

Maven
-----

Write the compile classpath with the
`dependency plugin <https://maven.apache.org/plugins/maven-dependency-plugin/build-classpath-mojo.html>`_,
then extract. With the repository's fixture:

.. code-block:: console

   mvn -f examples/maven/pom.xml -DskipTests compile \
     org.apache.maven.plugins:maven-dependency-plugin:3.11.0:build-classpath \
     -Dmdep.includeScope=compile -Dmdep.outputFile=target/classpath.txt
   sphinx-java-autodoc examples/standalone/src examples/build-consumer/src \
     examples/maven/target/generated-sources/java-autodoc \
     --classpath-file examples/maven/target/classpath.txt \
     -o build/maven-api.xml --cache build/java-cache --warnings-as-errors

For your project, use ``src/main/java`` and your generated-source directories.

Gradle
------

Write ``sourceSets.main.compileClasspath.asPath`` to a UTF-8 file, then extract.
The fixture's ``examples/gradle/build.gradle`` has a ``writeJavaAutodocClasspath``
task for this:

.. code-block:: console

   gradle -p examples/gradle classes writeJavaAutodocClasspath
   sphinx-java-autodoc examples/standalone/src examples/build-consumer/src \
     examples/gradle/build/generated/sources/java-autodoc \
     --classpath-file examples/gradle/build/java-autodoc-classpath.txt \
     -o build/gradle-api.xml --cache build/java-cache --warnings-as-errors

Both fixtures are verified by ``uv run --locked python tests/build_tools_check.py``;
see :doc:`compatibility` for the tested versions.

Publish the site from CI
------------------------

This GitHub Actions workflow builds on every push to ``main`` and deploys to
GitHub Pages. Set **Pages → Source** to **GitHub Actions** in the repository
settings, then save it as ``.github/workflows/docs.yml``:

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
         - run: python -m pip install sphinx-java-autodoc
         # Prepare java_classpath inputs and generated sources here.
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

Each run builds into a clean directory, so removed types leave no stale pages.
The workflow passes ``actionlint`` but has not run in another repository.

Caching and parallel builds
---------------------------

Sphinx caches extraction under ``<doctreedir>/java-cache`` and keeps only the
current model. The CLI uses ``.java-autodoc-cache`` or ``--cache`` and never
removes old entries.

The cache key covers source and classpath contents, options, the JDK and the
extension version. Every build hashes these inputs, so edits are caught even when
timestamps are unchanged. Any change re-extracts the whole project and rereads
every Sphinx document.

``sphinx-build -j`` is supported. Separate Sphinx processes must not share a
generated-page directory.

Run the doclet directly
-----------------------

To run the bundled doclet without the Python wrapper's caching and safeguards.
Its ``--sphinx-exclude`` option takes excluded packages separated by commas:

.. code-block:: console

   python -c "from sphinx_java_autodoc.extractor import DOCLET; print(DOCLET)"
   javac -proc:none -encoding UTF-8 -d build/doclet /printed/path/SphinxDoclet.java
   javadoc -quiet -encoding UTF-8 -protected \
     -doclet sphinxjava.SphinxDoclet -docletpath build/doclet \
     --sphinx-output build/api.xml -sourcepath src/main/java \
     -classpath lib/dependency.jar com.example
