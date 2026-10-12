Performance measurements
========================

A real-library baseline was measured on 2026-10-12 using Apache Commons Lang
3.21.0 sources from `Maven Central
<https://repo.maven.apache.org/maven2/org/apache/commons/commons-lang3/3.21.0/commons-lang3-3.21.0-sources.jar>`_.
The run used macOS 26.4.1 arm64, Temurin 25.0.3, Python 3.12.13 and Sphinx 9.1.0.
It exercised 264 Java files (4,083,008 bytes), yielding 287 types, 4,337 members
and an 11,084,894-byte XML model. No runtime dependency classpath was needed.

.. list-table:: One observed run, seconds
   :header-rows: 1
   :widths: 40 25 35

   * - Phase
     - Extraction/cache lookup
     - Sphinx HTML build
   * - Empty extraction and Sphinx caches
     - 3.483
     - 26.129
   * - Unchanged sources and existing caches
     - 0.450
     - 2.898
   * - One package comment changed, mtime preserved
     - 3.659
     - 28.892

Sphinx times include its own extraction-cache lookup after the separately timed
extraction. The source edit changed the XML, and the extension invalidated all
consuming documents. OS filesystem caches were not flushed. These are individual
observations, not averages or performance guarantees.

The benchmark process peaked at 388.1 MiB RSS; the highest child-process RSS was
702.3 MiB. These are separate process high-water marks across the complete run,
not simultaneous totals or per-phase measurements. The benchmark also retains
models for correctness assertions, so its Python peak is not a measurement of
Sphinx alone.

Fidelity matters more than the timings
--------------------------------------

Extraction recorded 106 diagnostics. Cold and edited Sphinx builds each emitted
3,022 warning lines; the unchanged build replayed 106 extraction diagnostics.
Warnings were captured and counted, not disabled. Unsupported Javadoc constructs
and markup therefore remain a substantial adoption limit for this workload.
Completing a non-strict build does not establish faithful documentation coverage.
The small Maven/Gradle consumer fixtures, separately, pass strict builds.

This run does not justify finer-grained Java extraction: extraction takes about
three to four seconds while Sphinx publication takes 26 to 29, most of it
resolving the type links in signatures. Retain the
whole-project correctness baseline. Before optimizing, profile document reading,
reference resolution and writing, and repeat on a dependency-heavy multi-module
project. Cache-hit hashing is measurable and remains intentional.

Reproduce
---------

Prepare and unpack the source JAR explicitly, then run::

   uv run --locked python tests/benchmark.py /path/to/commons-lang-sources/org

The benchmark copies the supplied tree into a temporary directory, measures
cold/cache/edit extraction and HTML builds, verifies cache reuse and semantic
change despite preserved mtime, reports JSON, and removes its temporary output.
It never downloads dependencies or edits the original source tree. Use
``--classpath`` with an explicit platform-separated classpath for another project.
Peak RSS is reported on macOS/Linux; Windows omits those measurements.

The source JAR SHA-256 was
``e0467ff7412bbedf5f120e78de484cddc0afcf995b8ef3e7cd132ef4bd101d01``;
its published Maven Central SHA-1 was also verified. The benchmark's Java-source
fingerprint was
``da269af51660d3237547b374e3675025981a378a789eb3cd4ac8ee8f87e1daa5``.
