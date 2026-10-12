# Prioritized follow-up roadmap

1. **Complete release verification:** register the PyPI trusted publisher. These are release qualification gaps, not
   additional backends. Keep JDK 25 / Sphinx 9.1 as the narrow baseline until wider
   runtime versions are actually tested.
2. **Extend Javadoc fidelity:** structured Markdown, external snippets and snippet
   regions/markup (plain inline snippets are supported); record
   accessor/canonical-constructor documentation synthesis; better support for definition
   lists, headings and local documentation assets. Retain actionable diagnostics
   until each behavior has fixtures.
3. **Support JPMS deliberately:** module-qualified IDs, module paths, split-package
   behavior and module documentation. Add separate fixtures before changing the
   schema; avoid introducing alternate parsing backends.
4. **Extend the measured baseline:** the Commons Lang cold/cache/edit timings and
   memory are recorded in `performance.rst`. Measure dependency-heavy multi-module
   inputs next, and profile Sphinx publication before changing Java extraction.
   Whole-project invalidation remains the correctness baseline; prioritize the
   unsupported-content diagnostics exposed by real sources over cache complexity.
