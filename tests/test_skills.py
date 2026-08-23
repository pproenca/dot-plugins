"""skills/: one-level discovery (§7.1) and Agent Skills frontmatter."""

import importlib
import sys

import pytest
from conftest import VALID_DESCRIPTION, manifest, skill_md


def test_valid_skill_is_discovered(build, validate):
    result = validate(build(manifest=manifest(), skills={"demo": skill_md()}))
    assert result.ok
    assert result.skills == 1


def test_missing_skills_directory_is_not_an_error(build, validate):
    """§6.2: an absent fixed location is never an error."""
    result = validate(build(manifest=manifest()))
    assert not result.errors(section="6.2")


def test_skills_as_a_file_invalidates_the_component_type(build, validate):
    root = build(manifest=manifest(), files={"skills": "not a directory"})
    assert validate(root).errors(section="6.2", where="skills")


def test_skill_directory_without_skill_md_warns(build, validate):
    result = validate(build(manifest=manifest(), skills={"empty": None}))
    assert result.ok
    assert result.warnings(section="7.1", where="skills/empty")


def test_nested_skill_is_never_discovered(build, validate):
    """Clients MUST NOT search deeper than skills/<dir>/SKILL.md."""
    root = build(manifest=manifest(), files={"skills/outer/inner/SKILL.md": skill_md("inner")})
    result = validate(root)
    assert result.skills == 0
    assert result.warnings(section="7.1", where="skills/outer/inner")


def test_sibling_skills_are_independent(build, validate):
    """A malformed skill must not suppress a valid one (§7.1, §11.3)."""
    root = build(manifest=manifest(), skills={
        "good": skill_md("good"),
        "bad": skill_md("mismatched-name"),
    })
    result = validate(root)
    assert result.errors(where="skills/bad")
    assert not result.errors(where="skills/good")


# --- frontmatter --------------------------------------------------------

def test_frontmatter_must_be_present(build, validate):
    root = build(manifest=manifest(), skills={"demo": "# No frontmatter\n"})
    assert validate(root).errors(section="7.1", message="frontmatter")


def test_unterminated_frontmatter_is_rejected(build, validate):
    root = build(manifest=manifest(), skills={"demo": "---\nname: demo\n"})
    assert validate(root).errors(section="7.1", message="never closed")


def test_name_must_match_directory(build, validate):
    root = build(manifest=manifest(), skills={"demo": skill_md(name="other")})
    assert validate(root).errors(section="7.1", message="must match its directory name")


def test_skill_name_may_not_contain_periods(build, validate):
    """Plugin names allow '.', skill names do not -- an easy trap to fall into."""
    root = build(manifest=manifest(), skills={"acme.tools": skill_md(name="acme.tools")})
    result = validate(root)
    assert result.errors(section="7.1", message="may contain only")
    assert result.errors(section="7.1", message="plugin names may contain periods")


def test_invalid_directory_name_is_reported(build, validate):
    """If the directory name is itself illegal, no frontmatter name can satisfy it."""
    root = build(manifest=manifest(), skills={"My_Skill": skill_md(name="My_Skill")})
    assert validate(root).errors(section="7.1", message="directory name is not a valid")


@pytest.mark.parametrize("name", ["a", "d" * 64])
def test_valid_skill_names_accepted(build, validate, name):
    assert validate(build(manifest=manifest(), skills={name: skill_md(name=name)})).ok


@pytest.mark.parametrize("name", ["d" * 65, "-lead", "trail-", "double--hyphen"])
def test_invalid_skill_names_rejected(build, validate, name):
    root = build(manifest=manifest(), skills={name: skill_md(name=name)})
    assert validate(root).errors(section="7.1")


@pytest.mark.parametrize("description", [None, "", "   "])
def test_description_is_required_and_non_empty(build, validate, description):
    root = build(manifest=manifest(), skills={"demo": skill_md(description=description)})
    assert validate(root).errors(section="7.1", where="description")


def test_description_length_limit(build, validate):
    ok = build(manifest=manifest(), skills={"demo": skill_md(description="d" * 1024)})
    assert validate(ok).ok

    too_long = build(manifest=manifest(), skills={"demo": skill_md(description="d" * 1025)})
    assert validate(too_long).errors(section="7.1", message="at most 1024")


def test_compatibility_length_limit(build, validate):
    ok = build(manifest=manifest(), skills={"demo": skill_md(compatibility="c" * 500)})
    assert validate(ok).ok

    too_long = build(manifest=manifest(), skills={"demo": skill_md(compatibility="c" * 501)})
    assert validate(too_long).errors(section="7.1", message="at most 500")


def test_optional_frontmatter_fields_accepted(build, validate):
    content = skill_md(
        license="Apache-2.0",
        compatibility="Requires Python 3.12",
        metadata={"author": "acme", "version": '"1.0"'},
        allowed_tools="Bash(git:*) Read",
    )
    assert validate(build(manifest=manifest(), skills={"demo": content})).ok


def test_unknown_frontmatter_field_warns(build, validate):
    root = build(manifest=manifest(), skills={"demo": skill_md(author="acme")})
    result = validate(root)
    assert result.ok
    assert result.warnings(section="7.1", where="author")


def test_block_scalar_description_is_parsed(build, validate):
    content = (
        "---\nname: demo\ndescription: >-\n  %s\n  Continued on a second line.\n---\n\nBody.\n"
        % VALID_DESCRIPTION
    )
    assert validate(build(manifest=manifest(), skills={"demo": content})).ok


# --- frontmatter parser parity ------------------------------------------

def _fingerprint(result):
    return sorted(
        (f["level"], f["section"], f["where"], f["message"]) for f in result.report.findings
    )


@pytest.mark.parametrize("content", [
    skill_md(),
    skill_md(description='"%s"' % VALID_DESCRIPTION),
    skill_md(license="Apache-2.0", metadata={"author": "acme", "version": '"1.0"'}),
    skill_md(allowed_tools="Bash(git:*) Read"),
    skill_md(author="unknown-field"),
    skill_md(description=None),
    skill_md(name="mismatched"),
    "---\nname: demo\ndescription: >-\n  Folded scalar description.\n  Second line.\n---\n\nBody.\n",
    "---\nname: demo\ndescription: |\n  Literal scalar description.\n  Second line.\n---\n\nBody.\n",
])
def test_fallback_parser_agrees_with_pyyaml(build, validate, monkeypatch, content):
    """The bundled YAML subset parser must reach the same verdict as PyYAML.

    The validator prefers PyYAML and falls back to a built-in parser when it is
    absent, so the two paths disagreeing would make findings depend on whether an
    optional dependency happens to be installed.
    """
    pytest.importorskip("yaml", reason="parity test needs PyYAML as the reference parser")

    root = build(manifest=manifest(), skills={"demo": content})
    with_pyyaml = _fingerprint(validate(root))

    monkeypatch.setitem(sys.modules, "yaml", None)
    with pytest.raises(ImportError):
        importlib.import_module("yaml")  # proves the fallback path is the one under test
    without_pyyaml = _fingerprint(validate(root))

    assert with_pyyaml == without_pyyaml
