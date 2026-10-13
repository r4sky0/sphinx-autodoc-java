Performance
===========

Extraction takes a few seconds; the Sphinx HTML build takes most of the time.
These are single runs on 2026-10-12, not averages or guarantees.

The workload was Apache Commons Lang 3.21.0 from the
`Maven Central source JAR <https://repo.maven.apache.org/maven2/org/apache/commons/commons-lang3/3.21.0/commons-lang3-3.21.0-sources.jar>`_
(SHA-256 ``e0467ff7412bbedf5f120e78de484cddc0afcf995b8ef3e7cd132ef4bd101d01``):
264 Java files, 287 types and 4,337 members, with an 11 MB XML model. It ran on
macOS 26.4.1 arm64 with Temurin 25.0.3, Python 3.12.13 and Sphinx 9.1.0.

.. list-table:: Seconds per run
   :header-rows: 1
   :widths: 40 25 35

   * - Run
     - Extraction or cache lookup
     - Sphinx HTML build
   * - Empty caches
     - 3.483
     - 26.129
   * - Unchanged sources
     - 0.450
     - 2.898
   * - One package comment changed
     - 3.659
     - 28.892

A changed comment re-extracts the project and rebuilds every page that uses the
model, even when file timestamps are preserved. Peak memory was 388 MiB for the
Python process and 702 MiB for the largest child process.

Extraction recorded 106 diagnostics, and a full build emitted 3,022 warning lines.
Unsupported Javadoc is therefore a larger adoption limit for this library than
build time.

Reproduce
---------

Unpack the source JAR, then run::

   uv run --locked python tests/benchmark.py /path/to/commons-lang-sources/org

The benchmark copies the tree to a temporary directory, times the three runs and
prints JSON. Pass ``--classpath`` for a project with dependencies. Windows reports
no memory figures.
