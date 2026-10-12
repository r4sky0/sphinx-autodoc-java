from __future__ import annotations

import pytest
from sphinx.errors import ExtensionError

from sphinx_java_autodoc.javadoc import check_mapping, external_url

ORACLE = "https://docs.oracle.com/en/java/javase/25/docs/api/{module}/"


@pytest.mark.parametrize(
    ("target", "spelling", "metadata", "mapping", "url"),
    [
        # Compiler metadata supplies the module, path and Javadoc fragment.
        (
            "java.util.List#add(java.lang.Object)",
            "java.util.List#add(java.lang.Object)",
            {
                "path": "java/util/List.html",
                "fragment": "add(E)",
                "module": "java.base",
            },
            {"java": ORACLE},
            "https://docs.oracle.com/en/java/javase/25/docs/api/java.base/java/util/List.html#add(E)",
        ),
        (
            "vendor.Token#<init>()",
            "vendor.Token#<init>()",
            {"path": "vendor/Token.html", "fragment": "<init>()"},
            {"vendor": "https://example.test/api/"},
            "https://example.test/api/vendor/Token.html#%3Cinit%3E()",
        ),
        # The longest prefix wins.
        (
            "vendor.special.Token",
            "vendor.special.Token",
            {"path": "vendor/special/Token.html"},
            {"vendor": "https://a.test/", "vendor.special": "https://b.test/"},
            "https://b.test/vendor/special/Token.html",
        ),
        # Prefixes match whole package names.
        ("vendorx.Token", "vendorx.Token", {}, {"vendor": "https://a.test/"}, None),
        # Without metadata, the spelling keeps varargs for the fragment.
        (
            "vendor.Token#take(java.lang.String[])",
            "vendor.Token#take(java.lang.String...)",
            {},
            {"vendor": "https://example.test/api"},
            "https://example.test/api/vendor/Token.html#take(java.lang.String...)",
        ),
        (
            "vendor.Outer.Inner",
            "vendor.Outer.Inner",
            {},
            {"vendor": "https://example.test/api/"},
            "https://example.test/api/vendor/Outer.Inner.html",
        ),
        # A module placeholder cannot be filled without metadata.
        ("java.util.List", "java.util.List", {}, {"java": ORACLE}, None),
    ],
)
def test_external_urls(target, spelling, metadata, mapping, url):
    assert external_url(target, spelling, metadata, mapping) == url


@pytest.mark.parametrize(
    "mapping", [{"": "https://a.test/"}, {"vendor": "ftp://a.test/"}, {"vendor": "a"}]
)
def test_invalid_mappings_are_rejected(mapping):
    with pytest.raises(ExtensionError, match="java_external_javadoc"):
        check_mapping(mapping)
