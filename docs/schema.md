# API XML schema 1

The process boundary is UTF-8 XML, rooted at `<api schema="1" extractor="0.1.0">`.
Unknown schema versions, malformed XML, DTD/entity declarations, duplicate IDs and
missing required declaration attributes are rejected. Declaration kinds, nonempty
names/signatures, package membership, and member IDs belonging to their enclosing
type are validated before rendering. This tightens schema 1 validation without
changing valid model structure. The file is generated input,
not a general XML document interchange service. No external entities are fetched.

- `package`: `name`, followed by `doc`.
- `type`: required `id`, `name`, `kind`, `package`, `signature`, `visibility`;
  contains `doc` then zero or more `member` elements.
  Visibility includes enclosing declarations: a public nested type inside a
  protected type has `visibility="protected"`; its signature retains `public`.
- `member`: same attributes. Kinds include `constructor`, `method`, `field`,
  `enum_constant`, `record_component`. Types include `class`, `interface`, `enum`, `record`,
  `annotation_type`.
- `doc/part`: `kind` (`body`, `param`, `typeparam`, `return`, `throws`, `see`,
  `since`, `deprecated`) and a `label`. Parameter labels follow the child declaration
  even when prose is inherited. Part contents are an ordered token sequence.
  Throws labels name the overriding method's exception after generic substitution;
  type variables use their declared names. This preserves the schema 1 structure.
  Repeated `throws` descriptions for one exception share a part, separated by
  paragraph tokens, so explicit and omitted inheritance preserve all descriptions.
- Tokens: `text`, `literal`, `code`, `link`, `start`, `end`. Text is element text,
  never serialized HTML to inject. `start`/`end` carry HTML element `name`;
  `start` may contain `attr name="href"` text and a `closed` flag.
  Characters XML 1.0 cannot represent (controls, lone surrogates), which javac
  produces from Unicode escapes in comments, are written as `\uXXXX` text.
  Attribute entities are decoded once before XML serialization. HTML line breaks
  remain `start name="br"` tokens and render as native line blocks.
  Plain inline snippets use existing `start name="pre"`, `literal`, `end name="pre"`
  tokens; `pre` accepts an optional `attr name="lang"` for syntax highlighting.
  Java is the default. Snippet text is not reparsed as HTML or Javadoc. Schema 1
  remains valid: older renderers can display the body and warn about the attribute.
- `link`: `target` is the compiler's canonical symbol ID; `role` identifies the
  domain object kind. `path`, `module`, `fragment` hold external Javadoc location
  metadata; `plain` distinguishes link/plainlink presentation. Children form the
  label. An unresolved link has no resolved location and has a diagnostic.
- `diagnostic`: symbol-qualified warning text, including unsupported constructs.
  Warnings survive cache hits and are re-emitted by Sphinx.

Identity examples: `example.Outer.Inner`, `example.Outer#FIELD`,
`example.Outer#find(java.lang.String,int[])`, `example.Outer#<init>()`.
Parameters in canonical IDs are fully qualified erased types; varargs use `[]`.
External Javadoc fragments instead preserve declared type variables and use `...`
for varargs, as verified against the standard doclet. Return types and
parameter names do not affect IDs. HTML anchors are `java-` plus UTF-8 bytes of the
ID encoded in hexadecimal: deterministic, reversible and collision-free.

Declarations and diagnostics are sorted; no build timestamp or source location is
stored. The private cache filename includes a SHA-256 input fingerprint and is not
part of a published model. Schema evolution requires an explicit version change
when consumers cannot safely interpret the changed structure.
