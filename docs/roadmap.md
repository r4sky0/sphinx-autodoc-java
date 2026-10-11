# Prioritized follow-up roadmap

1. **Complete release verification:** execute the Maven/Gradle recipes and
   register the PyPI trusted publisher. These are release qualification gaps, not
   additional backends. Keep JDK 25 / Sphinx 9.1 as the narrow baseline until wider
   runtime versions are actually tested.
2. **Extend Javadoc fidelity:** structured Markdown, external snippets and snippet
   regions/markup (plain inline snippets are supported); record
   accessor/canonical-constructor documentation synthesis; better support for tables, definition
   lists, headings and local documentation assets. Retain actionable diagnostics
   until each behavior has fixtures.
3. **Support JPMS deliberately:** module-qualified IDs, module paths, split-package
   behavior and module documentation. Add separate fixtures before changing the
   schema; avoid introducing alternate parsing backends.
4. **Measure larger projects:** cold/cache-hit timings and memory on real multi-module
   inputs. Only then consider separate doclet compilation caching or finer-grained
   extraction. Whole-project invalidation is the correctness baseline.
