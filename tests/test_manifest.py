"""plugin.json: closed schema, required fields, and §5.5 name constraints."""

import pytest
from conftest import PLUGIN_SCHEMA, manifest


def test_minimal_manifest_is_conformant(build, validate):
    root = build(manifest={"$schema": PLUGIN_SCHEMA, "name": "minimal-plugin"})
    assert validate(root).ok


def test_missing_manifest_is_rejected(build, validate):
    result = validate(build())
    assert result.errors(section="4.1", where="plugin.json")


def test_manifest_directory_is_rejected(build, validate):
    root = build(manifest=manifest())
    (root / "plugin.json").unlink()
    (root / "plugin.json").mkdir()
    assert validate(root).errors(section="5.1", where="plugin.json")


def test_invalid_json_is_rejected(build, validate):
    result = validate(build(manifest='{"name": "x",}'))
    assert result.errors(section="5.2", message="not valid json")


def test_non_object_top_level_is_rejected(build, validate):
    result = validate(build(manifest="[1, 2, 3]"))
    assert result.errors(section="5.2", message="must be an object")


def test_unknown_top_level_field_is_rejected(build, validate):
    """The schema is closed, so a typo must not be silently ignored (§5.2)."""
    result = validate(build(manifest=manifest(descrption="typo")))
    assert result.errors(section="5.2", where="plugin.json:descrption")


# --- $schema ------------------------------------------------------------

@pytest.mark.parametrize(
    "schema,expected_section",
    [
        (None, "5.3"),
        (42, "5.3"),
        ("https://agent-plugins.org/schemas/1.1.0/plugin.schema.json", "5.2"),
        ("https://example.com/other.schema.json", "5.2"),
    ],
)
def test_bad_schema_is_rejected(build, validate, schema, expected_section):
    result = validate(build(manifest=manifest(**{"$schema": schema})))
    assert result.errors(section=expected_section, where="plugin.json:$schema")


# --- name ---------------------------------------------------------------

@pytest.mark.parametrize("name", ["a", "my-plugin", "acme.tools", "lint3r", "a" * 64])
def test_valid_names_accepted(build, validate, name):
    assert validate(build(manifest=manifest(name=name))).ok


@pytest.mark.parametrize(
    "name,reason",
    [
        ("My-Plugin", "uppercase"),
        ("-start", "leading hyphen"),
        ("end-", "trailing hyphen"),
        (".dot", "leading period"),
        ("has--double", "consecutive hyphens"),
        ("too.many..dots", "consecutive periods"),
        ("under_score", "underscore"),
        ("has space", "space"),
        ("a" * 65, "too long"),
    ],
)
def test_invalid_names_rejected(build, validate, name, reason):
    result = validate(build(manifest=manifest(name=name)))
    assert result.errors(section="5.5", where="plugin.json:name"), reason


@pytest.mark.parametrize("name", [None, 42, ""])
def test_missing_or_untyped_name_rejected(build, validate, name):
    result = validate(build(manifest=manifest(name=name)))
    assert result.errors(section="5.3", where="plugin.json:name")


# --- metadata -----------------------------------------------------------

@pytest.mark.parametrize("field", ["version", "description", "homepage", "repository", "license"])
def test_metadata_must_be_strings(build, validate, field):
    result = validate(build(manifest=manifest(**{field: 42})))
    assert result.errors(section="5.4", where="plugin.json:%s" % field)


def test_metadata_urls_are_not_semantically_validated(build, validate):
    """§5.4 forbids rejecting a manifest merely because a URL looks wrong."""
    root = build(manifest=manifest(
        homepage="not a url", repository="also not a url", license="Definitely-Not-SPDX",
        version="not.a.semver",
    ))
    assert validate(root).ok


def test_keywords_must_be_a_string_array(build, validate):
    assert validate(build(manifest=manifest(keywords="nope"))).errors(where="plugin.json:keywords")
    assert validate(build(manifest=manifest(keywords=["ok", 3]))).errors(where="plugin.json:keywords[1]")
    assert validate(build(manifest=manifest(keywords=[]))).ok


def test_author_accepts_only_name_email_url(build, validate):
    ok = build(manifest=manifest(author={"name": "A", "email": "a@e.com", "url": "https://e.com"}))
    assert validate(ok).ok

    result = validate(build(manifest=manifest(author={"name": "A", "github": "a"})))
    assert result.errors(section="5.4", where="plugin.json:author.github")

    result = validate(build(manifest=manifest(author={"email": 42})))
    assert result.errors(section="5.4", where="plugin.json:author.email")

    result = validate(build(manifest=manifest(author="Jane")))
    assert result.errors(section="5.4", where="plugin.json:author")


# --- extensions ---------------------------------------------------------

def test_non_object_extensions_is_a_warning_not_an_error(build, validate):
    """§8.1 makes this non-fatal: clients report and ignore it."""
    result = validate(build(manifest=manifest(extensions="nope")))
    assert result.ok
    assert result.warnings(section="8.1", where="plugin.json:extensions")


def test_extension_namespace_value_must_be_an_object(build, validate):
    result = validate(build(manifest=manifest(extensions={"com.example.client": "nope"})))
    assert result.errors(section="8.1", where="plugin.json:extensions.com.example.client")


def test_non_reverse_domain_namespace_warns(build, validate):
    result = validate(build(manifest=manifest(extensions={"myclient": {"a": 1}})))
    assert result.ok
    assert result.warnings(section="8", where="plugin.json:extensions.myclient")


def test_reverse_domain_namespace_accepted(build, validate):
    root = build(manifest=manifest(extensions={"com.example.client": {"setting": True}}))
    assert validate(root).ok
