"""mcp.json: the closed server union (§7.2.1) and its loading rules (§7.2.2)."""

import pytest
from conftest import MCP_SCHEMA, manifest, mcp_config

REMOTE = {"type": "streamable-http", "url": "https://api.example.com/mcp"}


def test_valid_config_is_conformant(build, validate):
    root = build(
        manifest=manifest(),
        mcp=mcp_config({
            "local": {
                "type": "stdio",
                "command": "./bin/tool",
                "args": ["--data", "${PLUGIN_DATA}/db"],
                "env": {"CONFIG": "${PLUGIN_ROOT}/config.json"},
                "cwd": "${PLUGIN_ROOT}",
            },
            "remote": {**REMOTE, "headers": {"X-Tenant": "public"}},
        }),
        files={"bin/tool": "#!/bin/sh\n"},
        executables=["bin/tool"],
    )
    result = validate(root)
    assert result.ok
    assert result.servers == 2


def test_missing_mcp_json_is_not_an_error(build, validate):
    assert not validate(build(manifest=manifest())).errors(section="6.2")


def test_empty_servers_object_is_valid(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({}), skills=None)
    assert not validate(root).errors()


def test_mcp_json_as_directory_invalidates_component(build, validate):
    root = build(manifest=manifest())
    (root / "mcp.json").mkdir()
    assert validate(root).errors(section="6.2", where="mcp.json")


def test_invalid_json_disables_mcp(build, validate):
    result = validate(build(manifest=manifest(), mcp='{"mcpServers":,}'))
    assert result.errors(section="7.2.2", where="mcp.json")


def test_unknown_top_level_field_is_rejected(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({}, extra=True))
    assert validate(root).errors(section="7.2.1", where="mcp.json:extra")


def test_missing_servers_field_is_rejected(build, validate):
    root = build(manifest=manifest(), mcp={"$schema": MCP_SCHEMA})
    assert validate(root).errors(section="7.2.1", where="mcp.json:mcpServers")


def test_schema_version_must_match_plugin_json(build, validate):
    """§10.1: a version mismatch invalidates the whole MCP configuration."""
    root = build(
        manifest=manifest(),
        mcp=mcp_config({}, schema="https://agent-plugins.org/schemas/1.1.0/mcp.schema.json"),
    )
    assert validate(root).errors(section="10.1", where="mcp.json:$schema")


def test_plugin_schema_id_in_mcp_json_is_rejected(build, validate):
    from conftest import PLUGIN_SCHEMA
    root = build(manifest=manifest(), mcp=mcp_config({}, schema=PLUGIN_SCHEMA))
    assert validate(root).errors(where="mcp.json:$schema")


# --- the closed union ---------------------------------------------------

def test_type_is_required(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"url": "https://a.example.com"}}))
    assert validate(root).errors(section="7.2.1", where="mcpServers.s.type")


def test_unknown_transport_is_rejected(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "websocket"}}))
    assert validate(root).errors(section="7.2.1", where="mcpServers.s.type", message="unknown transport")


def test_unknown_field_is_rejected(stdio_plugin, validate):
    root = stdio_plugin({"timeout": 30})
    assert validate(root).errors(section="7.2.1", where="mcpServers.s.timeout", message="unknown field")


@pytest.mark.parametrize("field,value", [("url", "https://a.example.com"), ("headers", {"X-A": "1"})])
def test_remote_fields_on_stdio_are_rejected(stdio_plugin, validate, field, value):
    root = stdio_plugin({field: value})
    assert validate(root).errors(where="mcpServers.s.%s" % field, message="different transport")


@pytest.mark.parametrize("field,value", [("command", "tool"), ("args", ["-x"]), ("env", {"A": "1"}), ("cwd", "./x")])
def test_stdio_fields_on_remote_are_rejected(build, validate, field, value):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {**REMOTE, field: value}}))
    assert validate(root).errors(where="mcpServers.s.%s" % field, message="different transport")


def test_one_bad_server_does_not_affect_siblings(build, validate):
    """§7.2.2 rule 3: an invalid entry is skipped, others still load."""
    root = build(manifest=manifest(), mcp=mcp_config({
        "good": REMOTE,
        "bad": {"type": "stdio", "command": "sh -c 'x | y'"},
    }))
    result = validate(root)
    assert result.errors(where="mcpServers.bad")
    assert not result.errors(where="mcpServers.good")


# --- command ------------------------------------------------------------

def test_command_is_required_for_stdio(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "stdio"}}))
    assert validate(root).errors(section="7.2.1", where="mcpServers.s.command")


@pytest.mark.parametrize("command", [
    "sh -c 'node server.js | tee log'",
    "node server.js",
    "cmd && other",
    "tool > out.txt",
])
def test_shell_strings_are_rejected(build, validate, command):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "stdio", "command": command}}))
    assert validate(root).errors(section="7.2.1", where="command", message="single executable token")


@pytest.mark.parametrize("command,message", [
    ("/usr/bin/node", "absolute"),
    ("../bin/tool", "escapes"),
    ("bin/tool", "must begin with './'"),
])
def test_non_token_paths_are_rejected(build, validate, command, message):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "stdio", "command": command}}))
    assert validate(root).errors(where="command", message=message)


def test_placeholder_in_command_is_rejected(build, validate):
    """§9.2: no expansion happens in `command`, so this silently fails at runtime."""
    root = build(manifest=manifest(), mcp=mcp_config({
        "s": {"type": "stdio", "command": "${PLUGIN_ROOT}/bin/tool"}
    }))
    result = validate(root)
    assert result.errors(section="9.2", where="command", message="no placeholder expansion")
    assert result.errors(section="7.2.1", where="command", message="use a './'")


def test_bare_command_warns_about_path_dependence(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "stdio", "command": "npx"}}))
    result = validate(root)
    assert result.ok
    assert result.warnings(section="7.2.1", where="command", message="executable search")


def test_missing_bundled_executable_warns(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "stdio", "command": "./bin/absent"}}))
    result = validate(root)
    assert result.ok
    assert result.warnings(where="command", message="does not exist")


def test_non_executable_bundled_file_warns(build, validate):
    root = build(
        manifest=manifest(),
        mcp=mcp_config({"s": {"type": "stdio", "command": "./bin/tool"}}),
        files={"bin/tool": "#!/bin/sh\n"},
    )
    assert validate(root).warnings(where="command", message="not marked executable")


# --- cwd ----------------------------------------------------------------

@pytest.mark.parametrize("cwd", ["./", "./data", "${PLUGIN_ROOT}", "${PLUGIN_ROOT}/data",
                                 "${PLUGIN_DATA}", "${PLUGIN_DATA}/a/b"])
def test_valid_cwd_forms(stdio_plugin, validate, cwd):
    assert validate(stdio_plugin({"cwd": cwd})).ok


@pytest.mark.parametrize("cwd", ["data", "/tmp", "../outside", "~/x", "${PLUGIN_ROOTX}", "$PLUGIN_ROOT"])
def test_invalid_cwd_forms(stdio_plugin, validate, cwd):
    assert validate(stdio_plugin({"cwd": cwd})).errors(section="7.2.1", where="cwd")


@pytest.mark.parametrize("cwd", ["${PLUGIN_ROOT}/../../etc", "${PLUGIN_DATA}/../escape", "./../up"])
def test_cwd_escapes_are_rejected(stdio_plugin, validate, cwd):
    assert validate(stdio_plugin({"cwd": cwd})).errors(where="cwd")


def test_placeholder_inside_cwd_path_is_rejected(stdio_plugin, validate):
    """An interior placeholder expands to an absolute path and escapes the root."""
    assert validate(stdio_plugin({"cwd": "./a${PLUGIN_DATA}/b"})).errors(where="cwd", message="escape")


# --- env ----------------------------------------------------------------

@pytest.mark.parametrize("name", ["PLUGIN_ROOT", "PLUGIN_DATA"])
def test_reserved_env_names_are_rejected(stdio_plugin, validate, name):
    root = stdio_plugin({"env": {name: "/tmp"}})
    assert validate(root).errors(section="9.2", where="env.%s" % name)


def test_env_values_must_be_strings(stdio_plugin, validate):
    assert validate(stdio_plugin({"env": {"PORT": 8080}})).errors(where="env.PORT")


def test_unknown_placeholder_in_env_warns(stdio_plugin, validate):
    result = validate(stdio_plugin({"env": {"HOME_DIR": "${HOME}/x"}}))
    assert result.ok
    assert result.warnings(section="9.2", message="not a recognized placeholder")


def test_credential_shaped_env_value_is_rejected(stdio_plugin, validate):
    root = stdio_plugin({"env": {"API_TOKEN": "sk-abcdefghijklmnopqrstuvwxyz012345"}})
    assert validate(root).errors(section="9.2", message="credential")


def test_credential_shaped_env_name_warns(stdio_plugin, validate):
    result = validate(stdio_plugin({"env": {"API_TOKEN": "set-me"}}))
    assert result.ok
    assert result.warnings(message="suggests a credential")


# --- args ---------------------------------------------------------------

def test_args_must_be_a_string_array(stdio_plugin, validate):
    assert validate(stdio_plugin({"args": "not-a-list"})).errors(where="args")
    assert validate(stdio_plugin({"args": ["ok", 3]})).errors(where="args[1]")


def test_placeholders_in_args_are_accepted(stdio_plugin, validate):
    assert validate(stdio_plugin({"args": ["--root", "${PLUGIN_ROOT}", "--data", "${PLUGIN_DATA}/x"]})).ok


# --- remote transports --------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://localhost:3000/mcp",
    "http://127.0.0.1:8080/mcp",
    "http://[::1]:9000/mcp",
    "https://api.example.com/mcp",
])
def test_permitted_urls(build, validate, url):
    assert validate(build(manifest=manifest(), mcp=mcp_config({"s": {**REMOTE, "url": url}}))).ok


@pytest.mark.parametrize("url,message", [
    ("http://api.example.com/mcp", "https"),
    ("http://192.168.1.9/mcp", "https"),
    ("https://u:p@api.example.com/mcp", "user information"),
    ("https://api.example.com/mcp#frag", "fragment"),
    ("ftp://api.example.com/mcp", "absolute http"),
    ("/relative/mcp", "absolute http"),
])
def test_rejected_urls(build, validate, url, message):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {**REMOTE, "url": url}}))
    assert validate(root).errors(section="7.2.1", where="url", message=message)


def test_url_is_required(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "streamable-http"}}))
    assert validate(root).errors(where="mcpServers.s.url")


def test_duplicate_header_names_are_rejected(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({
        "s": {**REMOTE, "headers": {"X-Tenant": "a", "x-tenant": "b"}}
    }))
    assert validate(root).errors(where="headers", message="case-insensitive")


@pytest.mark.parametrize("name", ["X Tenant", "X:Tenant", "X\tTenant"])
def test_invalid_header_names_are_rejected(build, validate, name):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {**REMOTE, "headers": {name: "v"}}}))
    assert validate(root).errors(where="headers", message="header field name")


def test_control_characters_in_header_value_are_rejected(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {**REMOTE, "headers": {"X-A": "a\nb"}}}))
    assert validate(root).errors(where="headers", message="control characters")


def test_credential_header_is_rejected(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({
        "s": {**REMOTE, "headers": {"Authorization": "Bearer abcdefghijklmnopqrstuvwxyz"}}
    }))
    assert validate(root).errors(message="credential")


def test_placeholder_in_url_is_rejected(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({
        "s": {**REMOTE, "url": "https://api.example.com/${PLUGIN_ROOT}"}
    }))
    assert validate(root).errors(section="9.2", where="url")


def test_sse_is_valid_but_warns_as_deprecated(build, validate):
    root = build(manifest=manifest(), mcp=mcp_config({
        "s": {"type": "sse", "url": "https://legacy.example.com/sse"}
    }))
    result = validate(root)
    assert result.ok
    assert result.warnings(section="7.2.1", message="deprecated")
