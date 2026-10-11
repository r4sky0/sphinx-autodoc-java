# Extraction experiment

Run on 2026-10-10 using Temurin 25.0.3, before selecting the final architecture.
The retained probe uses public APIs only:

```sh
mkdir -p build/probe
javac -d build/probe experiments/Probe.java
javadoc -quiet -doclet Probe -docletpath build/probe \
  experiments/fixture/probe/*.java > build/probe/result.txt
```

Observed output is retained in `experiments/result.txt`. It shows:

- `Sample#convert(int)` resolves to the `int` overload and owner `probe.Sample`.
- `convert(String)` overrides `Parent<T>.convert(T)` through `Elements.overrides`.
- The child comment is still the raw `{@inheritDoc}`. The parent comment is
  available independently; inheritance is not silently performed for a doclet.
- `probe.Sample.Point` is a `RECORD`; its component and constructor retain
  `java.time.Instant`, a JDK dependency type.
- Generic declarations retain `T`; overloads retain their distinct parameter types.

The implementation then produced `build/probe/api.xml`. Its relevant observations:

```xml
<member id="probe.Parent#convert(java.lang.Object)" .../>
<member id="probe.Sample#convert(java.lang.String)" .../>
<link target="probe.Sample#convert(int)" role="method"
      path="probe/Sample.html" fragment="convert(int)" .../>
<link target="java.time.Instant" role="type" module="java.base"
      path="java/time/Instant.html" .../>
```

The inherited child description includes the parent's resolved link, and its
parameter description is labeled `renamed`, using the child's parameter name.
The full release fixture adds an actual precompiled external dependency in tests,
annotations, enum constants, constructors, arrays/varargs, nested types, all required
comment tags, and source code with a failing static initializer. Extraction succeeds
without executing that initializer.
