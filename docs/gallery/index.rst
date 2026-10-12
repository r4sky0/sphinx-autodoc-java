Feature gallery
===============

Each page here pairs a piece of Java source with what the extension makes of it, so
you can see what your own comments and declarations will look like. The examples come
from ``examples/standalone/src``, the same small API the tests and browser checks
use, so every example on these pages is built, and checked, on each change.

For a large real-world API, see the :doc:`Commons Lang showcase <../showcase>`.

This site's ``conf.py`` documents that API with these settings:

.. code-block:: python

   extensions = ["sphinx_java_autodoc", "sphinx.ext.linkcode"]
   java_sources = ["../examples/standalone/src"]
   java_generate = "gallery/api"
   java_external_javadoc = {
       "java": "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/",
   }

   def linkcode_resolve(domain, info):
       if domain == "java" and info["line"]:
           return (
               "https://github.com/r4sky0/sphinx-java-autodoc/blob/main/"
               f"examples/standalone/src/{info['source']}#L{info['line']}"
           )

The generated pages are the canonical location of every declaration. The excerpts
on the gallery pages use ``:no-index:``, so they don't register a second target.

.. toctree::
   :maxdepth: 1

   comments
   declarations
   inheritance
   directives
   links
   warnings
   Generated API pages <api/index>
