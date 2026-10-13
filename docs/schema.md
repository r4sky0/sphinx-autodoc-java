# API XML schema 1

The process boundary is UTF-8 XML, rooted at `<api schema="1" extractor="VERSION">`, where `extractor` is the
package version that wrote it.
Unknown schema versions, malformed XML, DTD/entity declarations, duplicate IDs and
missing required declaration attributes or `sig` are rejected. Declaration kinds, nonempty
names/signatures, package membership, and member IDs belonging to their enclosing
type are validated before rendering. The file is generated input,
not a general XML document interchange service. No external entities are fetched.

- `package`: `name`, followed by `doc`.
- `type`: required `id`, `name`, `kind`, `package`, `visibility`;
  contains `sig`, `doc`, then zero or more `member` elements.
  Visibility includes enclosing declarations: a public nested type inside a
  protected type has `visibility="protected"`; its signature retains `public`.
- `member`: same attributes and `sig`. Kinds include `constructor`, `method`, `field`,
  `enum_constant`, `record_component`. Types include `class`, `interface`, `enum`, `record`,
  `annotation_type`.
- `line` (optional on `type` and `member`): the declaration's first source line,
  including annotations. Compiler-generated members have none. Additive in schema 1.
- `sig` (required child of `type` and `member`): the declaration as signature tokens,
  so renderers can link types and build native signature nodes. Tags: `k` keyword
  or modifier, `kt` primitive type or `void`, `t` punctuation or spaces, `q` package
  qualifier, `n` declared name, `tv` type variable, `pname` parameter name, `v` constant
  or default value, `r` type reference, and `params` containing one `param` per
  parameter or record component. `r` carries `target` (canonical ID) and the external
  Javadoc `path`, `module` and `fragment`; its text is the nested simple name.
  Readers reject unknown tokens and malformed `r` targets.
- `doc/part`: `kind` (`body`, `specifiedBy`, `overrides`, `param`, `typeparam`,
  `return`, `throws`, `see`, `since`, `deprecated`, `apiNote`, `implSpec`, `implNote`)
  and a `label`. The three note kinds, `specifiedBy` and `overrides` are additive in
  schema 1: older renderers show them under their kind name. `specifiedBy` and
  `overrides` follow `body`: one `specifiedBy` per implemented interface method, then
  the superclass method as `overrides`, or `specifiedBy` when it is abstract. Each
  holds a method `link`, ` in class ` or ` in interface ` text, and a type `link`. Parameter labels follow the child declaration
  even when prose is inherited. Part contents are an ordered token sequence.
  `typeparam` parts document the type parameters of generic types and methods.
  Throws labels name the overriding method's exception after generic substitution;
  type variables use their declared names. A `throws` part whose exception is a type
  also carries `target`, `role` and the external Javadoc `path`, `module` and
  `fragment`, as `link` does, and its label is the type's name without its package.
  These attributes are additive in schema 1.
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
  Java is the default. Snippet text is not reparsed as HTML or Javadoc. A renderer
  that does not know `lang` displays the body and warns about the attribute.
  `{@value}` produces a `literal` token with the constant's Java source form; a
  referenced constant is a `plain` field `link` whose label is that `literal`.
  HTML tables use `start`/`end` tokens (`table`, `caption`, `thead`, `tbody`,
  `tfoot`, `tr`, `th`, `td`); `colspan`/`rowspan` are `attr` children.
- `link`: `target` is the compiler's canonical symbol ID; `role` identifies the
  domain object kind. `path`, `module`, `fragment` hold external Javadoc location
  metadata; `plain` distinguishes link/plainlink presentation. Children form the
  label; a comment link without one gets the standard doclet's text, such as
  `Map.Entry`, `String.format(String, Object...)` or `of(L, R)` within the same type.
  An unresolved link has no resolved location and has a diagnostic.
- `diagnostic`: symbol-qualified warning text, including unsupported constructs.
  Warnings survive cache hits and are re-emitted by Sphinx.

Identity examples: `example.Outer.Inner`, `example.Outer#FIELD`,
`example.Outer#find(java.lang.String,int[])`, `example.Outer#<init>()`.
Parameters in canonical IDs are fully qualified erased types; varargs use `[]`.
External Javadoc fragments instead preserve declared type variables and use `...`
for varargs, as verified against the standard doclet. Return types and
parameter names do not affect IDs. HTML anchors are `java-` plus UTF-8 bytes of the
ID encoded in hexadecimal: deterministic, reversible and collision-free.

Declarations and diagnostics are sorted; no build timestamp or source path is
stored. Renderers derive a declaration's file from its package and top-level type
name. The private cache filename includes a SHA-256 input fingerprint and is not
part of a published model. Schema evolution requires an explicit version change
when consumers cannot safely interpret the changed structure.
