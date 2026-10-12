# Java API documentation in Sphinx

Java declarations and their Javadoc comments, extracted by the compiler and shown
as native Sphinx objects.

## Language

**API model**:
The validated declarations, comments and links of one extraction, shared by every
page of a build.
_Avoid_: tree, XML, root

**Symbol**:
The canonical identity of a package, type or member: `pkg.Type` for types and
`pkg.Type#member(erased.Params)` for members, with nested types joined by dots.
_Avoid_: name, key, fully qualified name (for members)

**Visibility**:
Which declarations a site documents: `public` only, or `protected` (public plus
protected).
_Avoid_: access, scope

**Member group**:
The section a member is listed under: constructors, fields and constants, or methods.

**External Javadoc link**:
A link from a symbol not documented on this site to its page on another site's
standard Javadoc, chosen by package prefix.
_Avoid_: intersphinx link (that is a link to another Sphinx site)

**Javadoc fragment**:
The URL anchor standard Javadoc gives a member. Unlike a symbol, it keeps type
variable names and writes varargs as `...`.
_Avoid_: anchor (that is the HTML id on this site)

**Fingerprint**:
The content hash of everything an extraction depends on: sources, dependencies,
options and extractor/JDK identity. Every API model carries one; a changed
fingerprint rereads every document.
_Avoid_: cache key, checksum

**Generated page**:
An index, package or type page skeleton written for `java_generate`. Generated
pages contain directives only; comments never become reStructuredText.

**Page plan**:
The generated pages of one API model and visibility, as filenames and contents,
before anything is written.

**Publication**:
Replacing the generated pages in a directory with a page plan. A manifest records
the pages publication owns, so edited or unowned pages are never overwritten and
an interrupted publication recovers on the next build.
_Avoid_: generation (that covers planning too)
