"""Shared helpers for the Agent Plugins validator test suite.

The validator ships inside the skill as a standalone script rather than an
installable package, so it is loaded by path.
"""

import importlib.util
import json
import os
import pathlib
import stat

import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
MARKETPLACE = REPO_ROOT / ".claude-plugin" / "marketplace.json"
PLUGINS_DIR = REPO_ROOT / "plugins"
BUILDER_PLUGIN = PLUGINS_DIR / "agent-plugin-builder"
SKILL_DIR = BUILDER_PLUGIN / "skills" / "agent-plugin-builder"
VALIDATOR = SKILL_DIR / "scripts" / "validate_plugin.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("validate_plugin", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vp = _load_validator()

PLUGIN_SCHEMA = vp.PLUGIN_SCHEMA_ID
MCP_SCHEMA = vp.MCP_SCHEMA_ID

VALID_DESCRIPTION = "Does a demo thing. Use when the user asks for a demo of the thing."


def manifest(**overrides):
    """A minimal conformant manifest, with overrides applied.

    Passing a key with value ``None`` removes it, so tests can assert on
    missing required fields.
    """
    base = {
        "$schema": PLUGIN_SCHEMA,
        "name": "test-plugin",
        "version": "1.0.0",
        "description": "A plugin used by the test suite.",
    }
    base.update(overrides)
    return {k: v for k, v in base.items() if v is not None}


def mcp_config(servers, schema=MCP_SCHEMA, **extra):
    config = {"$schema": schema, "mcpServers": servers}
    config.update(extra)
    return config


def skill_md(name="demo", description=VALID_DESCRIPTION, body="Instructions.", **fields):
    lines = ["---"]
    if name is not None:
        lines.append("name: %s" % name)
    if description is not None:
        lines.append("description: %s" % description)
    for key, value in fields.items():
        key = key.replace("_", "-")
        if isinstance(value, dict):
            lines.append("%s:" % key)
            lines.extend("  %s: %s" % (k, v) for k, v in value.items())
        else:
            lines.append("%s: %s" % (key, value))
    lines += ["---", "", body, ""]
    return "\n".join(lines)


class Result:
    """Findings from one validation run, with convenience filters."""

    def __init__(self, report, skills, servers):
        self.report = report
        self.skills = skills
        self.servers = servers

    @property
    def ok(self):
        return not self.report.errors

    def _match(self, findings, section=None, where=None, message=None):
        out = []
        for f in findings:
            if section is not None and f["section"] != section:
                continue
            if where is not None and where not in f["where"]:
                continue
            if message is not None and message.lower() not in f["message"].lower():
                continue
            out.append(f)
        return out

    def errors(self, section=None, where=None, message=None):
        return self._match(self.report.errors, section, where, message)

    def warnings(self, section=None, where=None, message=None):
        return self._match(self.report.warnings, section, where, message)

    def __repr__(self):
        return "Result(errors=%r, warnings=%r)" % (
            [(f["section"], f["where"]) for f in self.report.errors],
            [(f["section"], f["where"]) for f in self.report.warnings],
        )


@pytest.fixture
def build(tmp_path):
    """Materialize a plugin directory on disk and return its path.

    ``manifest``/``mcp`` accept a dict (serialized to JSON) or a raw string,
    so tests can supply deliberately malformed JSON. ``None`` omits the file.
    """

    def _build(manifest=None, mcp=None, skills=None, files=None, executables=(), symlinks=None):
        root = tmp_path / "plugin"
        root.mkdir(exist_ok=True)

        for name, content in (("plugin.json", manifest), ("mcp.json", mcp)):
            if content is None:
                continue
            target = root / name
            if isinstance(content, str):
                target.write_text(content)
            else:
                target.write_text(json.dumps(content, indent=2))

        for dirname, content in (skills or {}).items():
            skill_dir = root / "skills" / dirname
            skill_dir.mkdir(parents=True, exist_ok=True)
            if content is not None:
                (skill_dir / "SKILL.md").write_text(content)

        for relpath, content in (files or {}).items():
            target = root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)

        for relpath in executables:
            target = root / relpath
            target.chmod(target.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

        for link, dest in (symlinks or {}).items():
            os.symlink(dest, root / link)

        return root

    return _build


@pytest.fixture
def validate():
    """Run the validator and wrap the findings."""

    def _validate(root):
        report, skills, servers = vp.validate(str(root))
        return Result(report, skills, servers)

    return _validate


@pytest.fixture
def stdio_plugin(build):
    """A conformant plugin with one bundled-executable stdio server."""

    def _make(server_overrides=None, **build_kwargs):
        server = {"type": "stdio", "command": "./bin/tool"}
        server.update(server_overrides or {})
        kwargs = {
            "manifest": manifest(),
            "mcp": mcp_config({"s": server}),
            "files": {"bin/tool": "#!/bin/sh\n"},
            "executables": ["bin/tool"],
        }
        kwargs.update(build_kwargs)
        return build(**kwargs)

    return _make
