from __future__ import annotations

import re
from urllib.parse import quote, urlsplit

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode

from .render import deprecated, documentation, summary

LOGGER = logging.getLogger(__name__)


def anchor(symbol: str) -> str:
    return "java-" + symbol.encode("utf-8").hex()


def role_for(element):
    return (
        "type"
        if element.tag == "type"
        else "method"
        if element.get("kind") in {"method", "constructor"}
        else "field"
    )


# Member groups in display order, as section headings of generated type pages.
MEMBER_GROUPS = {
    "constructor": "Constructors",
    "field": "Fields and constants",
    "method": "Methods",
}
TYPE_GROUPS = {
    "interface": "Interfaces",
    "class": "Classes",
    "enum": "Enums",
    "record": "Records",
    "annotation_type": "Annotation types",
}


def member_group(member) -> str:
    kind = member.get("kind")
    return kind if kind in {"constructor", "method"} else "field"


def short_signature(member) -> str:
    """The member name with simple parameter types, as in Javadoc summaries."""
    owner, _, rest = member.get("id").partition("#")
    name, paren, parameters = rest.partition("(")
    if name == "<init>":
        name = owner.rpartition(".")[2]
    if not paren:
        return name
    simple = [p.rpartition(".")[2] for p in parameters.rstrip(")").split(",") if p]
    return f"{name}({', '.join(simple)})"


class JavaDirective(SphinxDirective):
    def visible(self, element) -> bool:
        visibility = self.options.get("visibility", self.config.java_visibility)
        return visibility == "protected" or element.get("visibility") == "public"

    def lookup(self, symbol, tags=("type", "type/member")):
        model = self.env.java_model
        self.env.note_dependency(self.env.java_model_path)
        for tag in tags:
            for element in model.findall(tag):
                if element.get("id") == symbol:
                    return element
        return None

    def missing(self, what, symbol, subtype):
        LOGGER.warning(
            "Java %s %s was not extracted; check java_sources and visibility.",
            what,
            symbol,
            location=self.get_location(),
            type="java",
            subtype=subtype,
        )

    def describe(self, element):
        symbol = element.get("id")
        role = role_for(element)
        desc = addnodes.desc(
            "", domain="java", objtype=role, desctype=role, classes=["java", role]
        )
        sig = addnodes.desc_signature("", "", fullname=symbol)
        sig += addnodes.desc_name("", element.get("signature"))
        owner, _, member = symbol.partition("#")
        # Sphinx lists objects in the page's table of contents from these attributes.
        sig["_toc_parts"] = (owner, member) if member else (owner,)
        sig["_toc_name"] = (
            short_signature(element) if member else owner.rpartition(".")[2]
        )
        result = [desc]
        if "no-index" not in self.options:
            target = anchor(symbol)
            sig["ids"].append(target)
            self.state.document.note_explicit_target(sig)
            domain = self.env.get_domain("java")
            if domain.data["objects"].get(symbol):
                LOGGER.warning(
                    "Duplicate Java documentation for %s; use :no-index: on repeated excerpts.",
                    symbol,
                    location=self.get_location(),
                    type="java",
                    subtype="duplicate",
                )
            else:
                domain.data["objects"][symbol] = (self.env.docname, target, role)
                where = f" in {owner}" if member else ""
                entry = f"{sig['_toc_name']} (Java {element.get('kind').replace('_', ' ')}{where})"
                result.insert(
                    0, addnodes.index(entries=[("single", entry, target, "", None)])
                )
        desc += sig
        desc += addnodes.desc_content("", *documentation(element, self.get_location()))
        return result


class AutoClass(JavaDirective):
    required_arguments = 1
    option_spec = {
        "members": directives.unchanged,
        "exclude-members": directives.unchanged,
        "visibility": lambda v: directives.choice(v, ("public", "protected")),
        "no-index": directives.flag,
    }

    def run(self):
        symbol = self.arguments[0].strip()
        element = self.lookup(symbol, ("type",))
        if element is None:
            self.missing("type", symbol, "type")
            return []
        if not self.visible(element):
            return []
        result = self.describe(element)
        if "members" in self.options:
            # Semicolons allow exact signatures containing commas.
            selected = {
                s.strip() for s in self.options["members"].split(";") if s.strip()
            }
            excluded = {
                s.strip()
                for s in self.options.get("exclude-members", "").split(";")
                if s.strip()
            }
            matched = set()
            groups = {}
            for member in element.findall("member"):
                names = {member.get("name"), member.get("id").split("#", 1)[1]}
                if selected and not names & selected:
                    continue
                matched.update(names & selected)
                if names & excluded or not self.visible(member):
                    continue
                groups.setdefault(member_group(member), []).append(member)
            for missing in sorted(selected - matched):
                LOGGER.warning(
                    "Java member %s#%s was not found.",
                    symbol,
                    missing,
                    location=self.get_location(),
                    type="java",
                    subtype="member",
                )
            content = result[-1][-1]
            for group, title in MEMBER_GROUPS.items():
                if group in groups:
                    content += nodes.rubric("", title)
                    for member in groups[group]:
                        content.extend(self.describe(member))
        return result


class AutoMember(JavaDirective):
    """One method, constructor or field, like autodoc's automethod and autoattribute."""

    required_arguments = 1
    option_spec = {"no-index": directives.flag}

    def run(self):
        symbol = re.sub(r"\s+", "", self.arguments[0])
        element = self.lookup(symbol.replace("...", "[]"), ("type/member",))
        if element is None:
            self.missing("member", symbol, "member")
            return []
        return self.describe(element)


class AutoPackage(JavaDirective):
    required_arguments = 1

    def run(self):
        package = self.arguments[0].strip()
        self.env.note_dependency(self.env.java_model_path)
        element = next(
            (
                p
                for p in self.env.java_model.findall("package")
                if p.get("name") == package
            ),
            None,
        )
        if element is None:
            self.missing("package", package, "package")
            return []
        domain = self.env.get_domain("java")
        target = nodes.target("", "", ids=[anchor(package)])
        self.state.document.note_explicit_target(target)
        domain.data["objects"][package] = (self.env.docname, anchor(package), "package")
        index = addnodes.index(
            entries=[("single", f"{package} (Java package)", anchor(package), "", None)]
        )
        return [index, target, *documentation(element, self.get_location())]


class AutoSummary(JavaDirective):
    """A table of linked names and first sentences, like sphinx.ext.autosummary."""

    has_content = True

    def run(self):
        model = self.env.java_model
        self.env.note_dependency(self.env.java_model_path)
        packages = {p.get("name"): p for p in model.findall("package")}
        table = nodes.table("", classes=["autosummary", "longtable", "java"])
        group = nodes.tgroup("", cols=2)
        group += nodes.colspec("", colwidth=10)
        group += nodes.colspec("", colwidth=90)
        body = nodes.tbody()
        for line in self.content:
            symbol = re.sub(r"\s+", "", line)
            if not symbol:
                continue
            element = self.lookup(symbol)
            if element is not None:
                owner, _, member = symbol.partition("#")
                label = (
                    short_signature(element)
                    if member
                    else symbol[len(element.get("package")) + 1 :]
                    if element.get("package")
                    else symbol
                )
            elif symbol in packages:
                element, label = packages[symbol], symbol
            else:
                self.missing("object", symbol, "summary")
                continue
            link = addnodes.pending_xref(
                "",
                nodes.literal("", label, classes=["xref", "java"]),
                refdomain="java",
                reftype="obj",
                reftarget=symbol,
                refexplicit=True,
                refwarn=True,
            )
            text = nodes.paragraph("")
            if deprecated(element):
                text += [nodes.strong("", "Deprecated."), nodes.Text(" ")]
            text.extend(summary(element, self.get_location()))
            body += nodes.row(
                "",
                nodes.entry("", nodes.paragraph("", "", link)),
                nodes.entry("", text),
            )
        if not body.children:
            return []
        group += body
        table += group
        return [table]


class JavaDomain(Domain):
    name = "java"
    label = "Java"
    object_types = {
        name: ObjType(name, name, "obj")
        for name in ("type", "method", "field", "package")
    }
    roles = {
        name: XRefRole(warn_dangling=True)
        for name in ("type", "method", "field", "package", "obj")
    }
    directives = {
        "autoclass": AutoClass,
        "automethod": AutoMember,
        "autofield": AutoMember,
        "autopackage": AutoPackage,
        "autosummary": AutoSummary,
    }
    initial_data = {"objects": {}}

    def clear_doc(self, docname):
        self.data["objects"] = {
            k: v for k, v in self.data["objects"].items() if v[0] != docname
        }

    def merge_domaindata(self, docnames, otherdata):
        for symbol, value in otherdata["objects"].items():
            if value[0] in docnames:
                if (
                    symbol in self.data["objects"]
                    and self.data["objects"][symbol] != value
                ):
                    LOGGER.warning(
                        "Duplicate Java documentation for %s.",
                        symbol,
                        type="java",
                        subtype="duplicate",
                    )
                self.data["objects"][symbol] = value

    def get_objects(self):
        for symbol, (docname, target, kind) in sorted(self.data["objects"].items()):
            yield symbol, symbol, kind, docname, target, 1

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        spelling = re.sub(r"\s+", "", target)
        target = spelling.replace("...", "[]")
        objects = self.data["objects"]
        if target not in objects and "(" not in target:
            matches = [key for key in objects if key.startswith(target + "(")]
            if len(matches) == 1:
                target = matches[0]
            elif len(matches) > 1:
                LOGGER.warning(
                    "Ambiguous Java reference %s; include fully qualified parameter types.",
                    target,
                    location=node,
                    type="java",
                    subtype="ambiguous",
                )
                return None
        if target in objects:
            docname, ident, kind = objects[target]
            if typ not in {"obj", kind}:
                return None
            return make_refnode(builder, fromdocname, docname, ident, contnode, target)
        metadata = node.get("java:external") or env.java_references.get(target, {})
        for prefix, base in sorted(
            env.config.java_external_javadoc.items(), key=lambda item: -len(item[0])
        ):
            if target != prefix and not target.startswith(prefix.rstrip(".") + "."):
                continue
            if urlsplit(base).scheme not in {"https", "http"}:
                return None
            if metadata.get("path"):
                path = metadata["path"]
                fragment = metadata.get("fragment", "")
                base = base.replace("{module}", metadata.get("module", ""))
            else:
                # Without compiler metadata, a mapping key must be the exact package.
                if "{module}" in base:
                    continue
                owner, _, fragment = spelling.partition("#")
                package = prefix.rstrip(".")
                path = (
                    package.replace(".", "/")
                    + "/"
                    + owner[len(package) + 1 :]
                    + ".html"
                )
            url = base.rstrip("/") + "/" + quote(path, safe="/.$")
            if fragment:
                url += "#" + quote(fragment, safe="(),.[]$")
            return nodes.reference("", "", contnode, refuri=url)
        return None

    def resolve_any_xref(self, env, fromdocname, builder, target, node, contnode):
        resolved = self.resolve_xref(
            env, fromdocname, builder, "obj", target, node, contnode
        )
        return [("java:obj", resolved)] if resolved else []
