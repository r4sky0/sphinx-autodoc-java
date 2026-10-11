# ADR 001: JDK doclet, versioned XML, native Sphinx domain

Accepted 2026-10-10 after a doclet prototype; research date 2026-10-10.

Use the supported `jdk.javadoc.doclet` and compiler model APIs to inspect source
without loading application classes. The compiler resolves signatures, imports,
overloads, type erasure, and overrides. Comment inheritance is a separate doclet
responsibility: a doclet receives an unexpanded `INHERIT_DOC` node and can locate
the overridden generic method using `Elements.overrides`. There is no supported
call that returns the standard doclet's fully inherited documentation, and ancestor
comments are only available when the ancestor's source is supplied.

Use XML schema version 1 across the process boundary. The JDK includes DOM/XML
serialization and Python includes ElementTree. JSON is equally capable but would
require a Java JSON library or our own JSON serializer. XML preserves ordered
comment tokens without re-parsing Javadoc strings; semantic reference targets
travel alongside their presentation labels. Neither format supplies semantics
on its own. No upstream implementation is copied.

Render native docutils paragraphs, lists, literal blocks, Sphinx descriptions,
and pending cross-references. A `java` domain owns inventories and resolution.
Only page skeletons (titles, toctrees, directives) use generated reStructuredText;
source comments are never interpreted as reStructuredText or embedded raw HTML.

Run extraction once before Sphinx reads documents. Hash source and dependency
contents, options, JDK identity and extractor code. Cache complete immutable XML
snapshots and atomically replace files. A changed model invalidates consuming
documents even if filesystem timestamps do not change. This intentionally uses
whole-project extraction rather than fragile per-file semantic invalidation.

The initial runtime baseline is JDK 25. Traditional Javadoc and the JDK 25
automatic inheritance search are supported; snippet expansion and Markdown
comments initially produced diagnostics (plain inline snippets were added later). This avoids promising old-JDK
compatibility without running old JDKs. See the validation report for tested
Python/Sphinx versions and exact boundaries.

Tradeoffs: a JDK and a resolvable compile classpath are required; we own a compact
doc-comment-to-node mapping and inheritance implementation.

## Alternatives considered

Assessed from official documentation and source inspection; only the selected
backend was prototyped. Other tools' runtime behavior and speed were not measured.

- **[Manticore XMLDoclet](https://github.com/manticore-projects/xml-doclet) +
  [sphinx-javadoc-xml](https://github.com/manticore-projects/sphinx-javadoc-xml):**
  rich declaration metadata, but `Parser.getJavaDoc` stringifies comment bodies, the
  schema has no resolved inline-link targets or record components, and the renderer
  removes `inheritDoc` and registers directives without a Java domain.
- **Doxygen with [Breathe](https://github.com/breathe-doc/breathe) or
  [Doxysphinx](https://github.com/boschglobal/doxysphinx):** Doxygen's Java dialect
  is not the JDK documentation model, Breathe's domains target C/C++, and Doxysphinx
  wraps Doxygen HTML in raw directives instead of native Java objects.
- **[JavaParser](https://github.com/javaparser/javaparser),
  [Eclipse JDT](https://github.com/eclipse-jdt/eclipse.jdt.core),
  [tree-sitter-java](https://github.com/tree-sitter/tree-sitter-java):** a second
  parser to configure and maintain, with our own type resolution (or none, for
  tree-sitter) and still our own inheritance and rendering.
- **Reflection or bytecode:** no source comments, and loading classes can run
  static initializers.
- **Parsing generated Javadoc HTML:** presentation markup is an unstable
  interchange format and semantic identities would have to be reconstructed.

From the Sphinx side, [sphinx-autoapi](https://github.com/readthedocs/sphinx-autoapi)
informed page generation at `builder-inited`,
[sphinx-autodoc2](https://github.com/sphinx-extensions2/sphinx-autodoc2) the
separation of analysis and rendering with content-hash caching, and
[sphinx-js](https://github.com/pyodide/sphinx-js) the structured process boundary.
The archived [javasphinx](https://github.com/bronto/javasphinx) issues (inheritDoc,
default methods, encoding, parallel builds) motivated compiler-backed parsing,
explicit diagnostics, content fingerprints and domain merge tests. No code was copied.
