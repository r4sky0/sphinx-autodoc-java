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

from .render import documentation, reference

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


class AutoClass(SphinxDirective):
    required_arguments = 1
    option_spec = {
        "members": directives.unchanged,
        "exclude-members": directives.unchanged,
        "visibility": lambda v: directives.choice(v, ("public", "protected")),
        "no-index": directives.flag,
    }

    def run(self):
        model = self.env.java_model
        symbol = self.arguments[0].strip()
        element = next(
            (e for e in model.findall("type") if e.get("id") == symbol), None
        )
        if element is None:
            LOGGER.warning(
                "Java type %s was not extracted; check java_sources and visibility.",
                symbol,
                location=self.get_location(),
                type="java",
                subtype="type",
            )
            return []
        self.env.note_dependency(self.env.java_model_path)
        visibility = self.options.get("visibility", self.config.java_visibility)
        if visibility == "public" and element.get("visibility") != "public":
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
                if names & excluded or (
                    visibility == "public" and member.get("visibility") != "public"
                ):
                    continue
                group = (
                    "Constructors"
                    if member.get("kind") == "constructor"
                    else "Methods"
                    if member.get("kind") == "method"
                    else "Fields and constants"
                )
                groups.setdefault(group, []).append(member)
            for missing in sorted(selected - matched):
                LOGGER.warning(
                    "Java member %s#%s was not found.",
                    symbol,
                    missing,
                    location=self.get_location(),
                    type="java",
                    subtype="member",
                )
            content = result[-1]
            for title in ("Constructors", "Fields and constants", "Methods"):
                if title not in groups:
                    continue
                content += nodes.rubric("", title)
                for member in groups[title]:
                    content += self.describe(member)
        return [result]

    def describe(self, element):
        symbol = element.get("id")
        role = role_for(element)
        desc = addnodes.desc(
            "", domain="java", objtype=role, desctype=role, classes=["java", role]
        )
        sig = addnodes.desc_signature("", "", fullname=symbol)
        signature = element.find("signature")
        if signature is None:
            sig += addnodes.desc_name("", element.get("signature"))
        else:
            for token in signature:
                if token.tag == "link":
                    ref = reference(token, [nodes.Text(t.text or "") for t in token])
                    ref["java:signature"] = True
                    sig += ref
                elif token.tag == "name":
                    sig += addnodes.desc_name("", token.text or "")
                else:
                    sig += nodes.Text(token.text or "")
        if "no-index" not in self.options:
            target = anchor(symbol)
            sig["ids"].append(target)
            self.state.document.note_explicit_target(sig)
            domain = self.env.get_domain("java")
            previous = domain.data["objects"].get(symbol)
            if previous:
                LOGGER.warning(
                    "Duplicate Java documentation for %s; use :no-index: on repeated excerpts.",
                    symbol,
                    location=self.get_location(),
                    type="java",
                    subtype="duplicate",
                )
            else:
                domain.data["objects"][symbol] = (self.env.docname, target, role)
        desc += sig
        desc += addnodes.desc_content("", *documentation(element, self.get_location()))
        return desc


class AutoPackage(SphinxDirective):
    required_arguments = 1

    def run(self):
        package = self.arguments[0].strip()
        element = next(
            (
                p
                for p in self.env.java_model.findall("package")
                if p.get("name") == package
            ),
            None,
        )
        if element is None:
            LOGGER.warning(
                "Java package %s was not extracted.",
                package,
                location=self.get_location(),
                type="java",
                subtype="package",
            )
            return []
        domain = self.env.get_domain("java")
        self.env.note_dependency(self.env.java_model_path)
        target = nodes.target("", "", ids=[anchor(package)])
        self.state.document.note_explicit_target(target)
        domain.data["objects"][package] = (self.env.docname, anchor(package), "package")
        return [target, *documentation(element, self.get_location())]


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
    directives = {"autoclass": AutoClass, "autopackage": AutoPackage}
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


def signature_fallback(app, env, node, contnode):
    # Automatic type links stay readable when no local, external or intersphinx target exists.
    if node.get("refdomain") == "java" and node.get("java:signature"):
        return contnode
    return None
