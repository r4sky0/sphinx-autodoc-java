# Java autodoc research

Research date: **2026-10-10**. Findings below come from official documentation and
source inspection, not claims that every candidate was executed. Only the selected
backend was prototyped and tested here. GitHub `pushed_at` is evidence of repository
activity, not proof of maintenance quality or a supported compatibility matrix.

## Comparison

Performance and maintenance columns are architectural assessments, not benchmarks.
“M/G” means Maven/Gradle; all source approaches need generated sources produced first.

| Approach | Java / Javadoc fidelity | Modern Java | Semantic references | JDK / classpath / steps | M/G integration | Sphinx quality | Incremental work | Dependencies / license | Our maintenance burden |
|---|---|---|---|---|---|---|---|---|---|
| Supported JDK doclet **selected** | Compiler declarations and structured comments; implement doc inheritance | Matches selected JDK | `DocTrees.getElement`, `Elements.overrides`, `Types.erasure` | JDK, compile classpath, local doclet compilation, extraction | Feed compile classpath to CLI or Javadoc task | Native nodes/domain we supply | Whole-project cache; all semantic inputs hashed | JDK APIs; no extra Java libraries; our code MIT | Compact extractor + explicit comment renderer |
| Manticore XMLDoclet + sphinx-javadoc-xml | Rich declarations, comments reduced to strings | Java 17 toolchain; CI lists 17/21/22/23; records have no dedicated schema node | Qualified declaration types, but no resolved comment-reference model in inspected parser | JDK, doclet JAR/JAXB/Saxon, classpath, XML | Documented Gradle `Javadoc` task | Nodes/HTML generation; no registered Java domain in inspected setup | XML file generation and parsing; consumer-specific | XMLDoclet Apache-2.0; renderer MIT; JAXB/Saxon transitive licenses | Reuse would require semantic and renderer changes |
| Doxygen → XML → Breathe | Doxygen's Java dialect; not the JDK documentation model | Must verify each Java feature against Doxygen | Doxygen IDs; Breathe C/C++ domain integration does not establish Java semantics | Doxygen then Sphinx; no JVM required by parser | External task/exec | Native nodes, but Java domain/overloads need work | Doxygen extraction plus XML parsing | Doxygen GPL-2.0; Breathe modified BSD | Two tools plus Java adaptation |
| Doxygen → Doxysphinx | Preserves Doxygen HTML presentation | Same frontend limits as Doxygen | Existing HTML links retained | Doxygen HTML, doxysphinx, Sphinx | External task/exec | RST wrappers around raw HTML; not native Java objects | Resource copying and HTML/RST conversion | Doxysphinx MIT, Doxygen separate executable | Theme/HTML integration and separate semantics |
| JavaParser + symbol solver | Good syntax/AST; own doc inheritance/rendering | README advertises Java 1–25 | Optional symbol solver, configured type solvers | Java libraries; dependency/source resolution config | Published Maven artifacts | Would require our own model/domain | AST cache possible; cross-file invalidation remains | Apache-2.0 or LGPL choice; solver dependencies | Extra parser release and resolution policy |
| Eclipse JDT | Compiler AST and Javadoc nodes; own doc inheritance | JDT release-dependent; ongoing compiler development | Binding resolution must be enabled; source/classpath environment required | JDT runtime jars + environment or Eclipse project | Java library integration | Would require our own model/domain | AST/binding caching requires environment tracking | EPL-2.0 | More configuration and runtime surface |
| tree-sitter-java | Concrete syntax; comments are not resolved Javadoc | Grammar includes records; no blanket JDK compatibility guarantee | No Java type or overload resolver | Native/runtime parser bindings; no compile classpath for syntax | External extraction task | Must supply documentation semantics and domain | Incremental syntax parsing, not semantic invalidation | MIT grammar/runtime ecosystem | Would rebuild too much compiler/doc logic |
| Reflection / bytecode | Declarations, some annotations; source comments absent | Runtime/classfile version dependent | Runtime names; erased information and synthetic members need care | Compiled classes/dependencies; reflection risks initialization | Natural after compile | No source comments to render | Classfile fingerprints possible | JDK reflection or bytecode library | Rejected: cannot fulfill core goal alone |
| Parse generated Javadoc HTML | Standard doclet renders inheritance/snippets | Follows installed JDK HTML format | Links exist but semantic identity must be reconstructed | JDK/classpath → HTML → parser → Sphinx | Existing Javadoc tasks | HTML embedding or lossy reverse conversion | Regeneration and HTML diffing | HTML parser dependency optional | Rejected: presentation markup is an unstable interchange |

## Verified evidence and source inspection

### JDK APIs and the experiment

The public [Doclet API](https://docs.oracle.com/en/java/javase/25/docs/api/jdk.javadoc/jdk/javadoc/doclet/package-summary.html)
provides a [DocletEnvironment](https://docs.oracle.com/en/java/javase/25/docs/api/jdk.javadoc/jdk/javadoc/doclet/DocletEnvironment.html)
with compiler elements/types and [DocTrees](https://docs.oracle.com/en/java/javase/25/docs/api/jdk.compiler/com/sun/source/util/DocTrees.html).
These distinguish source syntax, type identity, and comment references. Javadoc
parses and resolves declarations; a custom doclet is responsible for output and
interpretation of documentation tags. There is no supported call that returns
“the standard doclet's fully inherited documentation”.

The [JDK 25 comment specification](https://docs.oracle.com/en/java/javase/25/docs/specs/javadoc/doc-comment-spec.html#inheritDoc)
defines automatic supertype search (superclass before interfaces, Object last),
explicit supertype selection, positional parameter matching, and inheritance by
omission. Ancestor source comments must be available; binary classes alone do not
contain them. This is why the extractor emits warnings instead of deleting
unresolved inheritance markers. See `experiment.md` for observed results.

XML and JSON can both express the required model. XML was selected because Java
and Python have standard-library serializers/readers, avoiding a new JSON jar or
a handwritten serializer. We do not inherit Manticore's XML schema: ours preserves
ordered documentation tokens and compiler-resolved symbol IDs.

### Manticore: inspected implementation, not just feature lists

The [XMLDoclet repository](https://github.com/manticore-projects/xml-doclet)
was not archived; last push observed 2026-08-30. Inspected tree SHA:
`68f02942d14a8ffc4c4ebfc79db66469b6e78bd1`. Its
[build](https://github.com/manticore-projects/xml-doclet/blob/68f02942d14a8ffc4c4ebfc79db66469b6e78bd1/build.gradle)
uses a Java 17 toolchain and JAXB/Saxon; the
[CI workflow](https://github.com/manticore-projects/xml-doclet/blob/68f02942d14a8ffc4c4ebfc79db66469b6e78bd1/.github/workflows/build.yml)
lists JDKs 17, 21, 22, 23. That is a configured matrix, not a verified passing run.
The repository is Apache-2.0. Its [usage guide](https://manticore-projects.com/XMLDoclet/usage.html)
shows Gradle doclet configuration and XSLT-to-RST conversion.

In [Parser.java](https://github.com/manticore-projects/xml-doclet/blob/68f02942d14a8ffc4c4ebfc79db66469b6e78bd1/src/main/java/com/manticore/tools/xmldoclet/Parser.java),
`getJavaDoc` stringifies `getFullBody()` and uses regexes to remove comma artifacts
(the code references issue #12). `parseTag` retains tag name and `toString()`.
Its [XSD](https://github.com/manticore-projects/xml-doclet/blob/68f02942d14a8ffc4c4ebfc79db66469b6e78bd1/src/main/resources/xjc/javadoc.xsd)
has qualified types, member signatures, and generic structure, but no structured
resolved inline-link targets or distinct record-component model. Useful data could
seed a domain, but comment semantics would still need extending.

The [sphinx-javadoc-xml repository](https://github.com/manticore-projects/sphinx-javadoc-xml)
is MIT, not archived, last push observed 2026-03-20; its Python source declares
0.3.0. [Setup](https://github.com/manticore-projects/sphinx-javadoc-xml/blob/main/sphinx_javadoc_xml/__init__.py)
registers three directives, not a Java domain. The actual
[comment processor](https://github.com/manticore-projects/sphinx-javadoc-xml/blob/main/sphinx_javadoc_xml/directives.py)
removes `inheritDoc` and turns inline Java links into formatted display text.
That does not satisfy semantic links/inventories or honest inheritance handling.
Useful architectural reference; no code copied. Neither tool was installed or run.

### Doxygen, Breathe, Doxysphinx

Doxygen documents [Java optimization](https://www.doxygen.nl/manual/config.html#cfg_optimize_output_java)
and [differences from Javadoc](https://www.doxygen.nl/manual/faq.html).
Changing output style does not establish compiler-equivalent overload resolution
or support for every current Javadoc tag. Records/snippets/inheritance parity were
not empirically verified; they must not be inferred from C++ examples.

[Breathe](https://github.com/breathe-doc/breathe) was active (push 2026-10-02);
its README requires Python 3.9+, Sphinx 7.2+, Doxygen 1.9.2+.
Its [domain documentation](https://breathe.readthedocs.io/en/latest/domains.html)
describes C/C++ targets, and its [license](https://github.com/breathe-doc/breathe/blob/main/LICENSE)
is modified BSD. It does not provide the desired Java domain merely by accepting
Doxygen XML. Doxygen's [license](https://www.doxygen.nl/license.html) governs the
separate tool, not automatically the documentation output.

[Doxysphinx's implementation description](https://boschglobal.github.io/doxysphinx/docs/inner_workings.html)
explicitly describes parsing Doxygen HTML, wrapping it in RST raw directives, and
copying/prefixing resources. It preserves HTML links and adds Sphinx navigation;
that is different from constructing semantic Java descriptions and inventory
entries. Its [repository](https://github.com/boschglobal/doxysphinx) is MIT, active
(push 2026-07-20). No candidate in this group was run here.

### Direct source parsers

[JavaParser](https://github.com/javaparser/javaparser) was active (push 2026-10-10).
Its README advertises Java 1–25 and 3.28.2, explains the optional symbol solver,
and offers Apache-2.0 or LGPL licensing. Syntax parsing alone is insufficient;
resolution needs appropriate type solvers and dependency inputs. No full
standard-doclet inheritance engine was established by this inspection.

[Eclipse JDT ASTParser](https://help.eclipse.org/latest/topic/org.eclipse.jdt.doc.isv/reference/api/org/eclipse/jdt/core/dom/ASTParser.html)
separates AST construction from optional bindings and exposes `setEnvironment`
for sourcepaths/classpaths. The [compiler repository](https://github.com/eclipse-jdt/eclipse.jdt.core)
is EPL-2.0 and active (push 2026-10-10). This is a capable alternative, but adds
runtime jars/configuration without removing the need for documentation rendering.

[tree-sitter-java](https://github.com/tree-sitter/tree-sitter-java) is MIT and
active (push 2026-09-13). Its [grammar](https://github.com/tree-sitter/tree-sitter-java/blob/master/grammar.js)
contains record declarations. Grammar coverage is not semantic resolution; source
comments, inherited docs, classpath lookup and overload targets require another layer.

### Reusable Sphinx architecture

| Project | Verified pattern and maintenance evidence | What we reuse |
|---|---|---|
| [sphinx.ext.autodoc](https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) | Directives, member filtering, domain descriptions; Python imports can execute code. Sphinx 9.1.0 source also inspected locally. | Directive vocabulary and native nodes; no Python introspection machinery |
| [sphinx-autoapi](https://github.com/readthedocs/sphinx-autoapi/blob/main/src/autoapi/extension.py) | Static analysis, mapper/model/render phases, page generation at `builder-inited`; MIT, active 2026-08-23, inspected tree `7018ce6d` | Page-generation lifecycle, not its Python mapper |
| [sphinx-autodoc2](https://github.com/sphinx-extensions2/sphinx-autodoc2/blob/main/src/autodoc2/sphinx/extension.py) | Separate analysis/database/rendering, SHA-256 file caching, diagnostics; MIT, active 2026-10-05, inspected tree `1f55a887` | Separation and content-based rebuilds, not its Python analysis |
| [sphinx-js IR](https://github.com/pyodide/sphinx-js/blob/master/sphinx_js/ir.py) | External JS/TS extraction, explicit internal/external type references and description fragments; MIT, active 2026-10-05, inspected tree `5e48e93a` | Structured process boundary, not its JS/TS implementation |
| [Sphinx domain API](https://www.sphinx-doc.org/en/master/extdev/domainapi.html) | Object types, roles, cross-reference resolver, `get_objects`, purge/merge lifecycle | Actual supported Sphinx extension interfaces |
| [javasphinx](https://github.com/bronto/javasphinx) | Apache-2.0; archived 2019-03-07, explicitly deprecated | Naming/navigation inspiration only |

Javasphinx's [apidoc implementation](https://github.com/bronto/javasphinx/blob/master/javasphinx/apidoc.py)
uses `javalang`, a Javadoc-to-RST compiler, and mtime-based pickle caches. Its
[issues](https://github.com/bronto/javasphinx/issues) include
[inheritDoc #59](https://github.com/bronto/javasphinx/issues/59),
[default methods #60](https://github.com/bronto/javasphinx/issues/60),
[method references #62](https://github.com/bronto/javasphinx/issues/62),
[encoding #63](https://github.com/bronto/javasphinx/issues/63), and
[parallel building #38](https://github.com/bronto/javasphinx/issues/38).
These motivate compiler-backed parsing, explicit diagnostics, UTF-8, content
fingerprints and domain merge tests. They are reported failure modes, not tests we
ran against that old project.

## Name and uncertainty

Selected distribution name: `sphinx-java-autodoc`; import: `sphinx_java_autodoc`.
Exact-name web searches found no matching published distribution. Direct PyPI
project/JSON lookups were attempted but unavailable from this environment, so
registry availability is **not confirmed** and the name is provisional until a
pre-publication check. No package was uploaded or name reserved.

The selected backend's behavior is backed by the included experiment and tests.
Other tools' runtime compatibility, modern-Java completeness and relative speed
remain unverified. The architecture choice is our assessment of the inspected
interfaces and code, not a performance claim.
