"""Java source documentation in Sphinx, without importing application code."""

from __future__ import annotations

import hashlib
from pathlib import Path
import xml.etree.ElementTree as ET

from sphinx.errors import ExtensionError
from sphinx.util import logging

from .domain import JavaDomain
from .extractor import VERSION, extract
from .javadoc import check_mapping
from .model import Model, read_model, use_model
from .pages import plan_pages, publish_pages
from .render import quiet_reference

__version__ = VERSION
LOGGER = logging.getLogger(__name__)


def prepare(app):
    config = app.config
    if config.java_visibility not in {"public", "protected"}:
        raise ExtensionError(
            "java_visibility must be 'public' or 'protected' (public plus protected)."
        )
    check_mapping(config.java_external_javadoc)
    base = Path(app.confdir)
    if config.java_model and config.java_sources:
        raise ExtensionError("Set either java_sources or java_model, not both.")
    if config.java_model:
        path = (base / config.java_model).resolve()
        model = Model(
            read_model(path), path, hashlib.sha256(path.read_bytes()).hexdigest()
        )
    elif config.java_sources:
        cache = Path(app.doctreedir) / "java-cache"
        model = extract(
            [base / s for s in config.java_sources],
            [base / s for s in config.java_classpath],
            cache,
            jdk=config.java_jdk,
            release=str(config.java_release),
            sourcepath=[base / s for s in config.java_sourcepath],
        )
        # This cache belongs to one doctree directory, so only the current model is kept.
        for old in cache.glob("*.xml"):
            if old != model.path:
                old.unlink(missing_ok=True)
    else:
        # A consumer using only Java roles and intersphinx needs no local sources.
        model = Model(ET.Element("api", schema="1"), base / "conf.py", "empty")
    root = model.root
    app._java_changed = getattr(app.env, "java_fingerprint", None) != model.fingerprint
    app.env.java_fingerprint = model.fingerprint
    app.env.java_model_path = str(model.path)
    use_model(root)
    for diagnostic in root.findall("diagnostic"):
        LOGGER.warning(diagnostic.text, type="java", subtype="extract")
    if config.java_generate:
        directory = (Path(app.srcdir) / config.java_generate).resolve()
        if (
            not directory.is_relative_to(Path(app.srcdir).resolve())
            or directory == Path(app.srcdir).resolve()
        ):
            raise ExtensionError(
                "java_generate must be a subdirectory of the Sphinx source directory."
            )
        if not root.findall("type"):
            raise ExtensionError(
                "Java autodoc: cannot generate API pages without extracted types."
            )
        publish_pages(directory, plan_pages(root, config.java_visibility))


def outdated(app, env, added, changed, removed):
    # Roles and missing-type directives also depend on the complete Java model.
    return sorted(env.found_docs - removed) if app._java_changed else []


def add_static_path(app):
    app.config.html_static_path.append(str(Path(__file__).parent / "static"))


def setup(app):
    for name, default in {
        "java_sources": [],
        "java_classpath": [],
        "java_sourcepath": [],
        "java_jdk": "",
        "java_release": "",
        "java_model": "",
        "java_generate": "",
        "java_visibility": "protected",
        "java_external_javadoc": {},
        "java_maximum_signature_line_length": None,
    }.items():
        app.add_config_value(name, default, "env")
    app.add_domain(JavaDomain)
    app.add_css_file("java-autodoc.css")
    app.connect("builder-inited", add_static_path)
    app.connect("builder-inited", prepare)
    app.connect("env-get-outdated", outdated)
    app.connect("missing-reference", quiet_reference)
    return {
        "version": VERSION,
        "env_version": 4,
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
