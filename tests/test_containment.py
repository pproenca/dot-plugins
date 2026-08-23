"""Path containment (§4.1) and non-portable layout warnings (§7, §8.2)."""

import pytest
from conftest import manifest, skill_md


def test_symlink_escaping_the_root_is_rejected(build, validate):
    root = build(manifest=manifest(), symlinks={"outside": "/etc"})
    assert validate(root).errors(section="4.1", where="outside", message="outside the plugin root")


def test_symlink_inside_the_root_is_allowed(build, validate):
    """§4.1 permits symlinks whose targets resolve within the plugin root."""
    root = build(manifest=manifest(), files={"real/data.txt": "x"})
    (root / "link").symlink_to(root / "real")
    assert validate(root).ok


def test_command_traversal_out_of_the_root_is_rejected(build, validate):
    from conftest import mcp_config
    root = build(manifest=manifest(), mcp=mcp_config({
        "s": {"type": "stdio", "command": "./bin/../../../usr/bin/env"}
    }))
    assert validate(root).errors(where="command")


@pytest.mark.parametrize("entry", ["commands", "hooks", "agents", "rules", "lsp"])
def test_non_portable_component_directories_warn(build, validate, entry):
    root = build(manifest=manifest(), files={"%s/thing.md" % entry: "x"})
    result = validate(root)
    assert result.ok, "not a spec violation -- clients simply ignore these"
    assert result.warnings(section="7", where=entry, message="not an Agent Plugins v1 component type")


@pytest.mark.parametrize("entry", [".mcp.json", "hooks.json", "settings.json"])
def test_client_native_config_files_warn(build, validate, entry):
    root = build(manifest=manifest(), files={entry: "{}"})
    assert validate(root).warnings(section="7", where=entry)


def test_reverse_domain_extension_directory_is_silent(build, validate):
    """§8.2: client files belong in a namespace directory, which is fully portable."""
    root = build(
        manifest=manifest(extensions={"com.acme.client": {"autoStart": True}}),
        files={"com.acme.client/hooks/hooks.json": "{}"},
        skills={"demo": skill_md()},
    )
    result = validate(root)
    assert result.ok
    assert not result.warnings(section="7")


def test_plugin_with_no_components_warns(build, validate):
    result = validate(build(manifest=manifest()))
    assert result.ok
    assert result.warnings(section="11.1")
