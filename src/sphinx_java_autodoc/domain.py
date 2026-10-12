from __future__ import annotations

from pathlib import PurePosixPath
import re

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx import addnodes
from sphinx.domains import Domain, ObjType
from sphinx.roles import XRefRole
from sphinx.util import logging
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode

from .javadoc import external_url
from .model import (
    MEMBER_GROUPS,
    PACKAGES,
    REFERENCES,
    SYMBOLS,
    grouped,
    local_name,
    member_label,
    visible,
)
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


# Signature tokens from the model mapped to Sphinx's standard signature nodes.
SIGNATURE_NODES = {
    "k": addnodes.desc_sig_keyword,
    "kt": addnodes.desc_sig_keyword_type,
    "q": addnodes.desc_addname,
    "n": addnodes.desc_name,
    "tv": addnodes.desc_sig_name,
    "pname": addnodes.desc_sig_name,
}


def signature_nodes(tokens) -> list[nodes.Node]:
    result: list[nodes.Node] = []
    for token in tokens:
        text = token.text or ""
        if token.tag == "params":
            parameters = addnodes.desc_parameterlist()
            for parameter in token.findall("param"):
                parameters += addnodes.desc_parameter(
                    "", "", *signature_nodes(parameter)
                )
            result.append(parameters)
        elif token.tag == "t":
            for part in re.split(r"( +)", text):
                if part:
                    result.append(
                        addnodes.desc_sig_space()
                        if part.isspace()
                        else addnodes.desc_sig_punctuation("", part)
                    )
        elif token.tag == "v":
            literal = (
                addnodes.desc_sig_literal_string
                if text[:1] in {'"', "'"}
                else addnodes.desc_sig_literal_number
            )
            result.append(literal("", text))
        elif token.tag == "r":
            # Like type annotations in Sphinx's Python domain, unresolved types stay
            # plain text and only warn in nitpicky mode.
            reference = addnodes.pending_xref(
                "",
                nodes.Text(text),
                refdomain="java",
                reftype="type",
                reftarget=token.get("target", ""),
                refexplicit=True,
                refwarn=False,
            )
            reference["java:external"] = dict(token.attrib)
            result.append(reference)
        elif token.tag in SIGNATURE_NODES:
            result.append(SIGNATURE_NODES[token.tag]("", text))
    return result


def display_name(symbol: str) -> str:
    owner, _, member = symbol.partition("#")
    return f"{owner}.{member_label(symbol)}" if member else symbol


class JavaDirective(SphinxDirective):
    def visible(self, element) -> bool:
        return visible(
            element, self.options.get("visibility", self.config.java_visibility)
        )

    def lookup(self, symbol, tags=("type", "member")):
        self.env.note_dependency(self.env.java_model_path)
        element = SYMBOLS.get(symbol)
        return element if element is not None and element.tag in tags else None

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
        package = element.get("package")
        local = symbol.removeprefix(f"{package}.") if package else symbol
        top = local.split("#")[0].split(".")[0]
        # javac requires a public top-level type to live in a file named after it.
        source = PurePosixPath(*package.split("."), f"{top}.java")
        sig = addnodes.desc_signature(
            "",
            "",
            fullname=symbol,
            source=str(source),
            line=element.get("line", ""),
        )
        sig.extend(signature_nodes(element.find("sig")))
        limit = (
            self.config.java_maximum_signature_line_length
            or self.config.maximum_signature_line_length
        )
        if limit and len(sig.astext()) > limit:
            for parameters in sig.findall(addnodes.desc_parameterlist):
                parameters["multi_line_parameter_list"] = True
        owner, _, member = symbol.partition("#")
        # Sphinx lists objects in the page's table of contents from these attributes.
        sig["_toc_parts"] = (owner, member) if member else (owner,)
        sig["_toc_name"] = member_label(symbol) if member else owner.rpartition(".")[2]
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
            members = []
            for member in element.findall("member"):
                names = {member.get("name"), member.get("id").split("#", 1)[1]}
                if selected and not names & selected:
                    continue
                matched.update(names & selected)
                if names & excluded or not self.visible(member):
                    continue
                members.append(member)
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
            for group, found in grouped(members).items():
                content += nodes.rubric("", MEMBER_GROUPS[group])
                for member in found:
                    content.extend(self.describe(member))
        return result


class AutoMember(JavaDirective):
    """One method, constructor or field, like autodoc's automethod and autoattribute."""

    required_arguments = 1
    option_spec = {"no-index": directives.flag}

    def run(self):
        symbol = re.sub(r"\s+", "", self.arguments[0])
        element = self.lookup(symbol.replace("...", "[]"), ("member",))
        if element is None:
            self.missing("member", symbol, "member")
            return []
        return self.describe(element)


class AutoPackage(JavaDirective):
    required_arguments = 1

    def run(self):
        package = self.arguments[0].strip()
        self.env.note_dependency(self.env.java_model_path)
        element = PACKAGES.get(package)
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
        self.env.note_dependency(self.env.java_model_path)
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
                label = local_name(element)
            elif symbol in PACKAGES:
                element, label = PACKAGES[symbol], symbol
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
            # Sphinx's search treats the text after the last dot as the object's name,
            # so members display as Type.member(SimpleTypes); IDs stay canonical.
            yield symbol, display_name(symbol), kind, docname, target, 0

    def resolve_xref(self, env, fromdocname, builder, typ, target, node, contnode):
        spelling = re.sub(r"\s+", "", target)
        target = spelling.replace("...", "[]")
        objects = self.data["objects"]
        # Only member names can omit their parameter list.
        if target not in objects and "#" in target and "(" not in target:
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
        metadata = node.get("java:external") or REFERENCES.get(target, {})
        url = external_url(target, spelling, metadata, env.config.java_external_javadoc)
        return nodes.reference("", "", contnode, refuri=url) if url else None

    def resolve_any_xref(self, env, fromdocname, builder, target, node, contnode):
        resolved = self.resolve_xref(
            env, fromdocname, builder, "obj", target, node, contnode
        )
        return [("java:obj", resolved)] if resolved else []
