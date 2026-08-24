#!/usr/bin/env python3
"""Validate a directory against the Agent Plugins Specification v1.0.0.

Checks the manifest schema and name constraints, skill discovery and Agent
Skills frontmatter, the mcp.json closed union, package path containment, and
placeholder usage.

Usage:
    validate_plugin.py <plugin-dir> [--json] [--quiet]

Exit codes: 0 clean, 1 conformance errors found, 2 could not run.
"""

import argparse
import ipaddress
import json
import os
import re
import sys
from urllib.parse import urlsplit

SPEC_VERSION = "1.0.0"
PLUGIN_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
MCP_SCHEMA_ID = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
SCHEMA_ID_RE = re.compile(
    r"^https://agent-plugins\.org/schemas/(?P<version>[^/]+)/(?P<kind>plugin|mcp)\.schema\.json$"
)

MANIFEST_FIELDS = {
    "$schema", "name", "version", "description", "author",
    "homepage", "repository", "license", "keywords", "extensions",
}
AUTHOR_FIELDS = {"name", "email", "url"}

STDIO_FIELDS = {"type", "command", "args", "env", "cwd"}
HTTP_FIELDS = {"type", "url", "headers"}
ALL_SERVER_FIELDS = STDIO_FIELDS | HTTP_FIELDS
HTTP_TYPES = {"streamable-http", "sse"}

SKILL_FRONTMATTER_FIELDS = {
    "name", "description", "license", "compatibility", "metadata", "allowed-tools",
}

PLACEHOLDER_RE = re.compile(r"\$\{([^}]*)\}")
KNOWN_PLACEHOLDERS = {"PLUGIN_ROOT", "PLUGIN_DATA"}
RESERVED_ENV = {"PLUGIN_ROOT", "PLUGIN_DATA"}

HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
SHELL_METACHARS = set(" \t\n|&;<>()$`\\\"'*?[]{}!~")

# Component types that exist in some clients but are not part of Agent Plugins v1.
NON_PORTABLE_ENTRIES = {
    "commands": "slash commands",
    "hooks": "hooks",
    "agents": "subagent definitions",
    "rules": "rules",
    "lsp": "LSP servers",
    ".claude-plugin": "client-specific manifest directory",
    ".mcp.json": "client-native MCP configuration",
    "hooks.json": "hook configuration",
    "settings.json": "client settings",
}

CREDENTIAL_NAME_RE = re.compile(
    r"(?i)(secret|token|passwd|password|api[-_]?key|apikey|credential|auth|private[-_]?key|session)"
)
CREDENTIAL_VALUE_RE = re.compile(
    r"(?i)^(bearer\s+\S{16,}|basic\s+[A-Za-z0-9+/=]{16,}|sk-[A-Za-z0-9_\-]{16,}"
    r"|gh[pousr]_[A-Za-z0-9]{16,}|xox[baprs]-[A-Za-z0-9\-]{16,}|AKIA[0-9A-Z]{12,}"
    r"|eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\.\S+)$"
)


class Report:
    def __init__(self):
        self.findings = []

    def add(self, level, section, where, message):
        self.findings.append(
            {"level": level, "section": section, "where": where, "message": message}
        )

    def error(self, section, where, message):
        self.add("error", section, where, message)

    def warn(self, section, where, message):
        self.add("warning", section, where, message)

    @property
    def errors(self):
        return [f for f in self.findings if f["level"] == "error"]

    @property
    def warnings(self):
        return [f for f in self.findings if f["level"] == "warning"]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def is_str(v):
    return isinstance(v, str)


def type_name(v):
    if v is None:
        return "null"
    return {bool: "boolean", int: "number", float: "number", str: "string",
            list: "array", dict: "object"}.get(type(v), type(v).__name__)


def within(root_real, candidate):
    """True if candidate (already realpath'd) is inside or equal to root_real."""
    return candidate == root_real or candidate.startswith(root_real + os.sep)


def resolve_in_root(root, relative):
    """Realpath of `relative` interpreted against the plugin root."""
    return os.path.realpath(os.path.join(root, relative))


def scan_placeholders(value):
    return PLACEHOLDER_RE.findall(value)


def check_expandable(report, where, value):
    """A field where ${PLUGIN_ROOT}/${PLUGIN_DATA} do expand."""
    for name in scan_placeholders(value):
        if name not in KNOWN_PLACEHOLDERS:
            report.warn(
                "9.2", where,
                "'${%s}' is not a recognized placeholder and stays literal; "
                "only ${PLUGIN_ROOT} and ${PLUGIN_DATA} expand." % name,
            )


def check_not_expandable(report, where, value, field_desc):
    """A field where no expansion happens at all."""
    for name in scan_placeholders(value):
        report.error(
            "9.2", where,
            "'${%s}' stays literal: clients perform no placeholder expansion in %s."
            % (name, field_desc),
        )


def check_secret(report, section, where, name, value):
    if CREDENTIAL_VALUE_RE.match(value.strip()):
        report.error(
            section, where,
            "value looks like a live credential. Plugins MUST NOT embed secrets in "
            "package data; credential storage is client-managed.",
        )
    elif CREDENTIAL_NAME_RE.search(name):
        report.warn(
            section, where,
            "name suggests a credential. Package data is visible to anyone who reads "
            "the plugin, so it MUST NOT carry secrets. Document the requirement instead.",
        )


# --------------------------------------------------------------------------
# frontmatter parsing
# --------------------------------------------------------------------------

def split_frontmatter(text):
    """Return (frontmatter_text, error_message)."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return None, "file does not begin with a '---' YAML frontmatter delimiter"
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "\n".join(lines[1:i]), None
    return None, "YAML frontmatter is never closed with '---'"


def parse_yaml_mapping(text):
    """Parse a shallow YAML mapping. Uses PyYAML when present, else a subset parser."""
    try:
        import yaml  # type: ignore
        data = yaml.safe_load(text)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            return None, "frontmatter is not a mapping"
        return data, None
    except ImportError:
        pass
    except Exception as exc:  # malformed YAML
        return None, "frontmatter is not valid YAML: %s" % exc

    result = {}
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        raw = lines[i]
        i += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[:1] in (" ", "\t"):
            continue  # handled by the nested branch below
        if ":" not in raw:
            return None, "cannot parse frontmatter line: %r" % raw
        key, _, rest = raw.partition(":")
        key = key.strip()
        rest = rest.strip()
        if rest in ("|", ">", "|-", ">-", "|+", ">+"):
            block, joiner = [], " " if rest[0] == ">" else "\n"
            while i < len(lines) and (not lines[i].strip() or lines[i][:1] in (" ", "\t")):
                block.append(lines[i].strip())
                i += 1
            result[key] = joiner.join(b for b in block if b or joiner == "\n").strip()
        elif rest == "":
            nested = {}
            while i < len(lines) and (lines[i][:1] in (" ", "\t")) and lines[i].strip():
                sub = lines[i].strip()
                i += 1
                if ":" not in sub:
                    continue
                sk, _, sv = sub.partition(":")
                nested[sk.strip()] = _unquote(sv.strip())
            result[key] = nested if nested else ""
        else:
            result[key] = _unquote(rest)
    return result, None


def _unquote(v):
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ("'", '"'):
        return v[1:-1]
    return v


# --------------------------------------------------------------------------
# manifest
# --------------------------------------------------------------------------

def check_plugin_name(report, name):
    where = "plugin.json:name"
    if not (1 <= len(name) <= 64):
        report.error("5.5", where, "must be 1-64 characters (is %d)." % len(name))
    bad = sorted({c for c in name if not re.match(r"[a-z0-9.\-]", c)})
    if bad:
        report.error(
            "5.5", where,
            "may contain only a-z, 0-9, '-' and '.'; found %s."
            % ", ".join(repr(c) for c in bad),
        )
    if name and not re.match(r"[a-z0-9]", name[0]):
        report.error("5.5", where, "first character must be alphanumeric.")
    if name and not re.match(r"[a-z0-9]", name[-1]):
        report.error("5.5", where, "last character must be alphanumeric.")
    if "--" in name:
        report.error("5.5", where, "consecutive hyphens '--' are not allowed.")
    if ".." in name:
        report.error("5.5", where, "consecutive periods '..' are not allowed.")


def validate_manifest(report, root):
    """Returns (manifest_dict_or_None, declared_version_or_None)."""
    path = os.path.join(root, "plugin.json")
    if not os.path.exists(path):
        report.error("4.1", "plugin.json", "missing; a plugin MUST have a manifest at the root.")
        return None, None
    if not os.path.isfile(path):
        report.error("5.1", "plugin.json", "is not a regular file.")
        return None, None

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, UnicodeDecodeError) as exc:
        report.error("5.2", "plugin.json", "cannot be read: %s" % exc)
        return None, None
    except json.JSONDecodeError as exc:
        report.error("5.2", "plugin.json", "is not valid JSON: %s" % exc)
        return None, None

    if not isinstance(data, dict):
        report.error("5.2", "plugin.json", "top level must be an object, found %s." % type_name(data))
        return None, None

    for key in sorted(set(data) - MANIFEST_FIELDS):
        report.error(
            "5.2", "plugin.json:%s" % key,
            "unknown top-level field; the manifest schema is closed. Client-specific "
            "data belongs under 'extensions'.",
        )

    declared = None
    schema = data.get("$schema")
    if schema is None:
        report.error("5.3", "plugin.json:$schema", "required field is missing.")
    elif not is_str(schema):
        report.error("5.3", "plugin.json:$schema", "must be a string, found %s." % type_name(schema))
    elif schema != PLUGIN_SCHEMA_ID:
        m = SCHEMA_ID_RE.match(schema)
        if m and m.group("kind") == "plugin":
            declared = m.group("version")
            report.error(
                "5.2", "plugin.json:$schema",
                "declares Agent Plugins %s; this validator implements %s."
                % (declared, SPEC_VERSION),
            )
        else:
            report.error(
                "5.2", "plugin.json:$schema",
                "must be exactly %r for Agent Plugins %s." % (PLUGIN_SCHEMA_ID, SPEC_VERSION),
            )
    else:
        declared = SPEC_VERSION

    name = data.get("name")
    if name is None:
        report.error("5.3", "plugin.json:name", "required field is missing.")
    elif not is_str(name):
        report.error("5.3", "plugin.json:name", "must be a string, found %s." % type_name(name))
    elif not name:
        report.error("5.3", "plugin.json:name", "must not be empty.")
    else:
        check_plugin_name(report, name)

    for field in ("version", "description", "homepage", "repository", "license"):
        if field in data and not is_str(data[field]):
            report.error(
                "5.4", "plugin.json:%s" % field,
                "must be a string, found %s." % type_name(data[field]),
            )

    if "keywords" in data:
        kw = data["keywords"]
        if not isinstance(kw, list):
            report.error("5.4", "plugin.json:keywords", "must be an array of strings, found %s." % type_name(kw))
        else:
            for idx, item in enumerate(kw):
                if not is_str(item):
                    report.error(
                        "5.4", "plugin.json:keywords[%d]" % idx,
                        "must be a string, found %s." % type_name(item),
                    )

    if "author" in data:
        author = data["author"]
        if not isinstance(author, dict):
            report.error("5.4", "plugin.json:author", "must be an object, found %s." % type_name(author))
        else:
            for key in sorted(set(author) - AUTHOR_FIELDS):
                report.error(
                    "5.4", "plugin.json:author.%s" % key,
                    "unknown field; author may contain only name, email and url.",
                )
            for key in sorted(set(author) & AUTHOR_FIELDS):
                if not is_str(author[key]):
                    report.error(
                        "5.4", "plugin.json:author.%s" % key,
                        "must be a string, found %s." % type_name(author[key]),
                    )

    if "extensions" in data:
        ext = data["extensions"]
        if not isinstance(ext, dict):
            report.warn(
                "8.1", "plugin.json:extensions",
                "must be an object; clients report and ignore it (non-fatal), so the "
                "extension data is lost. Found %s." % type_name(ext),
            )
        else:
            for ns in sorted(ext):
                if not isinstance(ext[ns], dict):
                    report.error(
                        "8.1", "plugin.json:extensions.%s" % ns,
                        "namespace value must be an object, found %s." % type_name(ext[ns]),
                    )
                if "." not in ns:
                    report.warn(
                        "8", "plugin.json:extensions.%s" % ns,
                        "namespace should be a reverse-domain identifier based on a domain "
                        "the client controls, e.g. 'com.example.client'.",
                    )

    if "version" not in data:
        report.warn(
            "10.2", "plugin.json:version",
            "no version declared; clients use it for update checks and cache freshness.",
        )
    if "description" not in data:
        report.warn("5.4", "plugin.json:description", "no description declared.")

    return data, declared


# --------------------------------------------------------------------------
# skills
# --------------------------------------------------------------------------

def check_skill_name(report, where, name, dirname):
    if not (1 <= len(name) <= 64):
        report.error("7.1", where, "skill name must be 1-64 characters (is %d)." % len(name))
    bad = sorted({c for c in name if not re.match(r"[a-z0-9\-]", c)})
    if bad:
        detail = ""
        if "." in bad:
            detail = (" Note: plugin names may contain periods, but skill names may not.")
        report.error(
            "7.1", where,
            "skill name may contain only a-z, 0-9 and '-'; found %s.%s"
            % (", ".join(repr(c) for c in bad), detail),
        )
    if name and (name[0] == "-" or name[-1] == "-"):
        report.error("7.1", where, "skill name must not start or end with a hyphen.")
    if "--" in name:
        report.error("7.1", where, "skill name must not contain consecutive hyphens.")
    if name != dirname:
        report.error(
            "7.1", where,
            "skill name %r must match its directory name %r." % (name, dirname),
        )


def validate_skill(report, root_real, skill_dir, dirname):
    rel = os.path.join("skills", dirname)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.exists(skill_md):
        report.warn(
            "7.1", rel,
            "contains no SKILL.md, so it is not discovered as a skill. Clients never "
            "search deeper, so nested skills here are invisible.",
        )
        for sub in sorted(os.listdir(skill_dir)):
            nested = os.path.join(skill_dir, sub, "SKILL.md")
            if os.path.isfile(nested):
                report.warn(
                    "7.1", os.path.join(rel, sub),
                    "a SKILL.md here is two levels below skills/ and is never discovered; "
                    "move the directory up to skills/.",
                )
        return
    if not os.path.isfile(skill_md):
        report.error("7.1", os.path.join(rel, "SKILL.md"), "is not a regular file.")
        return
    if not within(root_real, os.path.realpath(skill_md)):
        report.error("4.1", os.path.join(rel, "SKILL.md"), "resolves outside the plugin root.")
        return

    if (not re.fullmatch(r"[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?", dirname)
            or "--" in dirname or len(dirname) > 64):
        report.error(
            "7.1", rel,
            "directory name is not a valid Agent Skills name (a-z, 0-9 and '-' only; no "
            "leading, trailing or consecutive hyphens; max 64 characters). Since the "
            "frontmatter 'name' must equal the directory name, the directory must be renamed.",
        )

    try:
        with open(skill_md, "r", encoding="utf-8") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        report.error("7.1", os.path.join(rel, "SKILL.md"), "cannot be read: %s" % exc)
        return

    fm_text, err = split_frontmatter(text)
    if err:
        report.error("7.1", os.path.join(rel, "SKILL.md"), err + "; the skill is skipped by clients.")
        return

    fm, err = parse_yaml_mapping(fm_text)
    if err:
        report.error("7.1", os.path.join(rel, "SKILL.md"), err)
        return

    where = os.path.join(rel, "SKILL.md")
    name = fm.get("name")
    if name is None:
        report.error("7.1", where + ":name", "required frontmatter field is missing.")
    elif not is_str(name):
        report.error("7.1", where + ":name", "must be a string, found %s." % type_name(name))
    else:
        check_skill_name(report, where + ":name", name, dirname)

    desc = fm.get("description")
    if desc is None:
        report.error("7.1", where + ":description", "required frontmatter field is missing.")
    elif not is_str(desc):
        report.error("7.1", where + ":description", "must be a string, found %s." % type_name(desc))
    elif not desc.strip():
        report.error("7.1", where + ":description", "must not be empty.")
    elif len(desc) > 1024:
        report.error("7.1", where + ":description", "must be at most 1024 characters (is %d)." % len(desc))

    compat = fm.get("compatibility")
    if compat is not None:
        if not is_str(compat):
            report.error("7.1", where + ":compatibility", "must be a string, found %s." % type_name(compat))
        elif len(compat) > 500:
            report.error("7.1", where + ":compatibility", "must be at most 500 characters (is %d)." % len(compat))

    meta = fm.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        report.error("7.1", where + ":metadata", "must be a mapping of string keys to string values.")
    elif isinstance(meta, dict):
        for k, v in meta.items():
            if not is_str(v):
                report.error(
                    "7.1", where + ":metadata.%s" % k,
                    "values must be strings, found %s." % type_name(v),
                )

    for key in sorted(set(fm) - SKILL_FRONTMATTER_FIELDS):
        report.warn(
            "7.1", where + ":" + str(key),
            "not an Agent Skills frontmatter field; put extra properties under 'metadata'.",
        )


def validate_skills(report, root, root_real):
    path = os.path.join(root, "skills")
    if not os.path.exists(path):
        return 0
    if not os.path.isdir(path):
        report.error(
            "6.2", "skills",
            "exists but is not a directory, so the skills component type is invalid.",
        )
        return 0
    count = 0
    for entry in sorted(os.listdir(path)):
        child = os.path.join(path, entry)
        if not os.path.isdir(child):
            if entry not in (".DS_Store",):
                report.warn(
                    "7.1", os.path.join("skills", entry),
                    "is not a directory; only immediate subdirectories containing SKILL.md "
                    "are discovered as skills.",
                )
            continue
        validate_skill(report, root_real, child, entry)
        if os.path.isfile(os.path.join(child, "SKILL.md")):
            count += 1
    if count == 0:
        report.warn("6.1", "skills", "directory exists but contains no discoverable skills.")
    return count


# --------------------------------------------------------------------------
# mcp.json
# --------------------------------------------------------------------------

def validate_command(report, root, root_real, where, command):
    if not is_str(command):
        report.error("7.2.1", where, "must be a string, found %s." % type_name(command))
        return
    if not command:
        report.error("7.2.1", where, "must not be empty.")
        return

    if PLACEHOLDER_RE.search(command):
        check_not_expandable(report, where, command, "'command'")
        report.error(
            "7.2.1", where,
            "use a './' plugin-relative path instead; it already resolves against the "
            "plugin root, which is why no placeholder is needed here.",
        )
        return

    if command.startswith("./"):
        rel = command[2:]
        if not rel:
            report.error("7.2.1", where, "'./' is not an executable path.")
            return
        resolved = resolve_in_root(root, rel)
        if not within(root_real, resolved):
            report.error("4.1", where, "plugin-relative command escapes the plugin root.")
        elif not os.path.exists(resolved):
            report.warn(
                "7.2.1", where,
                "bundled executable does not exist in the package; the server will fail "
                "to start unless it is built or installed before use.",
            )
        elif not os.access(resolved, os.X_OK):
            report.warn("7.2.1", where, "bundled executable is not marked executable.")
        return

    offenders = sorted({c for c in command if c in SHELL_METACHARS})
    if offenders:
        report.error(
            "7.2.1", where,
            "must be a single executable token, not a shell command string; found %s. "
            "Pass arguments via 'args'."
            % ", ".join(repr(c) for c in offenders),
        )
        return
    if command.startswith("/") or re.match(r"^[A-Za-z]:[\\/]", command):
        report.error(
            "7.2.1", where,
            "absolute paths are not allowed; use a bare executable name or a "
            "plugin-relative './' path.",
        )
        return
    if command.startswith("../"):
        report.error("4.1", where, "escapes the plugin root; use a './' path inside the package.")
        return
    if "/" in command or "\\" in command:
        report.error(
            "7.2.1", where,
            "a path command must begin with './' to be plugin-relative.",
        )
        return
    report.warn(
        "7.2.1", where,
        "bare command %r relies on the platform executable search, which is client-defined. "
        "If this executable ships in the package, reference it as './%s' instead; otherwise "
        "document the dependency." % (command, command),
    )


def validate_cwd(report, root, root_real, where, cwd):
    if not is_str(cwd):
        report.error("7.2.1", where, "must be a string, found %s." % type_name(cwd))
        return
    check_expandable(report, where, cwd)

    if cwd.startswith("${PLUGIN_ROOT}"):
        rest = cwd[len("${PLUGIN_ROOT}"):]
        base_root = True
    elif cwd.startswith("${PLUGIN_DATA}"):
        rest = cwd[len("${PLUGIN_DATA}"):]
        base_root = False
    elif cwd.startswith("./"):
        rest = "/" + cwd[2:]
        base_root = True
    else:
        report.error(
            "7.2.1", where,
            "invalid form. 'cwd' must be a './' plugin-relative path, '${PLUGIN_ROOT}'"
            "[/...], or '${PLUGIN_DATA}'[/...]. Omit it to use the plugin root.",
        )
        return

    if rest and not rest.startswith("/"):
        report.error(
            "7.2.1", where,
            "a placeholder-rooted cwd must be the placeholder alone or be followed by '/'.",
        )
        return

    inner = rest.lstrip("/")
    if PLACEHOLDER_RE.search(inner):
        report.error(
            "7.2.1", where,
            "a placeholder inside the path can expand to an absolute path and escape the "
            "configured root; keep placeholders at the start of 'cwd' only.",
        )
        return

    if base_root:
        resolved = resolve_in_root(root, inner) if inner else root_real
        if not within(root_real, resolved):
            report.error("7.2.1", where, "resolves outside the plugin root after expansion.")
    else:
        normalized = os.path.normpath(inner) if inner else "."
        if os.path.isabs(normalized) or normalized == ".." or normalized.startswith(".." + os.sep):
            report.error("7.2.1", where, "resolves outside the plugin data directory after expansion.")


def validate_url(report, where, url):
    if not is_str(url):
        report.error("7.2.1", where, "must be a string, found %s." % type_name(url))
        return
    check_not_expandable(report, where, url, "'url'")

    try:
        parts = urlsplit(url)
    except ValueError as exc:
        report.error("7.2.1", where, "is not a parseable URL: %s" % exc)
        return

    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        report.error("7.2.1", where, "must be an absolute HTTP or HTTPS URL (found scheme %r)." % parts.scheme)
        return
    if not parts.netloc:
        report.error("7.2.1", where, "must be an absolute URL with a host.")
        return
    if "@" in parts.netloc:
        report.error("7.2.1", where, "must not contain user information.")
    if parts.fragment or "#" in url:
        report.error("7.2.1", where, "must not contain a fragment.")

    if scheme == "http":
        host = (parts.hostname or "").lower()
        loopback = host == "localhost"
        if not loopback:
            try:
                loopback = ipaddress.ip_address(host).is_loopback
            except ValueError:
                loopback = False
        if not loopback:
            report.error(
                "7.2.1", where,
                "non-loopback endpoints MUST use HTTPS; plain HTTP is allowed only for "
                "'localhost' or a loopback IP literal.",
            )


def validate_headers(report, where, headers):
    if not isinstance(headers, dict):
        report.error("7.2.1", where, "must be an object of strings, found %s." % type_name(headers))
        return
    seen = {}
    for name in headers:
        if not is_str(name):
            report.error("7.2.1", where, "header names must be strings.")
            continue
        lower = name.lower()
        if lower in seen:
            report.error(
                "7.2.1", "%s.%s" % (where, name),
                "duplicates header %r; header names are case-insensitive." % seen[lower],
            )
        seen[lower] = name

        field = "%s.%s" % (where, name)
        if not HEADER_NAME_RE.match(name):
            report.error("7.2.1", field, "is not a valid HTTP header field name.")
        check_not_expandable(report, field, name, "header names")

        value = headers[name]
        if not is_str(value):
            report.error("7.2.1", field, "header value must be a string, found %s." % type_name(value))
            continue
        check_not_expandable(report, field, value, "header values")
        if any(ord(c) < 32 and c != "\t" or ord(c) == 127 for c in value):
            report.error("7.2.1", field, "header value contains control characters.")
        check_secret(report, "7.2.1", field, name, value)


def validate_env(report, where, env):
    if not isinstance(env, dict):
        report.error("7.2.1", where, "must be an object of strings, found %s." % type_name(env))
        return
    for key in sorted(env):
        field = "%s.%s" % (where, key)
        if not is_str(key):
            report.error("7.2.1", where, "environment variable names must be strings.")
            continue
        if key in RESERVED_ENV:
            report.error(
                "9.2", field,
                "'env' MUST NOT define %s; the client supplies it after applying 'env', "
                "so the entry both invalidates the server and would be overwritten." % key,
            )
        if PLACEHOLDER_RE.search(key):
            report.warn("9.2", field, "placeholders are not expanded in 'env' keys; this name stays literal.")

        value = env[key]
        if not is_str(value):
            report.error("7.2.1", field, "environment values must be strings, found %s." % type_name(value))
            continue
        check_expandable(report, field, value)
        check_secret(report, "9.2", field, key, value)


def validate_server(report, root, root_real, name, cfg):
    where = "mcp.json:mcpServers.%s" % name
    if not isinstance(cfg, dict):
        report.error("7.2.1", where, "server configuration must be an object, found %s." % type_name(cfg))
        return

    stype = cfg.get("type")
    if stype is None:
        report.error("7.2.1", where + ".type", "required field is missing; each server MUST declare a transport.")
        return
    if not is_str(stype):
        report.error("7.2.1", where + ".type", "must be a string, found %s." % type_name(stype))
        return

    if stype == "stdio":
        allowed, foreign = STDIO_FIELDS, HTTP_FIELDS - STDIO_FIELDS
    elif stype in HTTP_TYPES:
        allowed, foreign = HTTP_FIELDS, STDIO_FIELDS - HTTP_FIELDS
    else:
        report.error(
            "7.2.1", where + ".type",
            "unknown transport %r; must be 'stdio', 'streamable-http' or 'sse'." % stype,
        )
        return

    for key in sorted(set(cfg) - allowed):
        if key in foreign:
            report.error(
                "7.2.1", "%s.%s" % (where, key),
                "belongs to a different transport variant and invalidates this %r server." % stype,
            )
        elif key not in ALL_SERVER_FIELDS:
            report.error(
                "7.2.1", "%s.%s" % (where, key),
                "unknown field; server configurations are a closed union.",
            )

    if stype == "stdio":
        if "command" not in cfg:
            report.error("7.2.1", where + ".command", "required field is missing for a stdio server.")
        else:
            validate_command(report, root, root_real, where + ".command", cfg["command"])

        if "args" in cfg:
            args = cfg["args"]
            if not isinstance(args, list):
                report.error("7.2.1", where + ".args", "must be an array of strings, found %s." % type_name(args))
            else:
                for idx, item in enumerate(args):
                    field = "%s.args[%d]" % (where, idx)
                    if not is_str(item):
                        report.error("7.2.1", field, "must be a string, found %s." % type_name(item))
                    else:
                        check_expandable(report, field, item)

        if "env" in cfg:
            validate_env(report, where + ".env", cfg["env"])
        if "cwd" in cfg:
            validate_cwd(report, root, root_real, where + ".cwd", cfg["cwd"])
    else:
        if stype == "sse":
            report.warn(
                "7.2.1", where + ".type",
                "'sse' is the deprecated HTTP+SSE transport and client support is OPTIONAL; "
                "prefer 'streamable-http' unless the server only speaks the 2024-11-05 transport.",
            )
        if "url" not in cfg:
            report.error("7.2.1", where + ".url", "required field is missing for a %r server." % stype)
        else:
            validate_url(report, where + ".url", cfg["url"])
        if "headers" in cfg:
            validate_headers(report, where + ".headers", cfg["headers"])


def validate_mcp(report, root, root_real, plugin_version):
    path = os.path.join(root, "mcp.json")
    if not os.path.exists(path):
        return 0
    if not os.path.isfile(path):
        report.error(
            "6.2", "mcp.json",
            "exists but is not a regular file, so the MCP component type is invalid.",
        )
        return 0

    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, UnicodeDecodeError) as exc:
        report.error("7.2.2", "mcp.json", "cannot be read: %s" % exc)
        return 0
    except json.JSONDecodeError as exc:
        report.error("7.2.2", "mcp.json", "is not valid JSON, which disables MCP for the whole plugin: %s" % exc)
        return 0

    if not isinstance(data, dict):
        report.error("7.2.1", "mcp.json", "top level must be an object, found %s." % type_name(data))
        return 0

    for key in sorted(set(data) - {"$schema", "mcpServers"}):
        report.error(
            "7.2.1", "mcp.json:%s" % key,
            "unknown top-level field; only '$schema' and 'mcpServers' are permitted, and "
            "an extra field disables MCP for the whole plugin.",
        )

    schema = data.get("$schema")
    if schema is None:
        report.error("7.2.1", "mcp.json:$schema", "required field is missing.")
    elif not is_str(schema):
        report.error("7.2.1", "mcp.json:$schema", "must be a string, found %s." % type_name(schema))
    elif schema != MCP_SCHEMA_ID:
        m = SCHEMA_ID_RE.match(schema)
        if m and m.group("kind") == "mcp":
            found = m.group("version")
            if plugin_version and found != plugin_version:
                report.error(
                    "10.1", "mcp.json:$schema",
                    "declares Agent Plugins %s but plugin.json declares %s; a version "
                    "mismatch invalidates the whole MCP configuration."
                    % (found, plugin_version),
                )
            else:
                report.error(
                    "7.2.1", "mcp.json:$schema",
                    "declares Agent Plugins %s; this validator implements %s." % (found, SPEC_VERSION),
                )
        else:
            report.error(
                "7.2.1", "mcp.json:$schema",
                "must be exactly %r for Agent Plugins %s." % (MCP_SCHEMA_ID, SPEC_VERSION),
            )

    servers = data.get("mcpServers")
    if servers is None:
        report.error("7.2.1", "mcp.json:mcpServers", "required field is missing (an empty object is valid).")
        return 0
    if not isinstance(servers, dict):
        report.error("7.2.1", "mcp.json:mcpServers", "must be an object, found %s." % type_name(servers))
        return 0

    for name in sorted(servers):
        validate_server(report, root, root_real, name, servers[name])
    return len(servers)


# --------------------------------------------------------------------------
# layout and containment
# --------------------------------------------------------------------------

def validate_layout(report, root, root_real, manifest):
    namespaces = set()
    if isinstance(manifest, dict) and isinstance(manifest.get("extensions"), dict):
        namespaces = set(manifest["extensions"])

    for entry in sorted(os.listdir(root)):
        if entry in NON_PORTABLE_ENTRIES and entry not in namespaces:
            report.warn(
                "7", entry,
                "%s are not an Agent Plugins v1 component type, so every client ignores "
                "this path. Move it into a reverse-domain extension directory such as "
                "'com.example.client/'." % NON_PORTABLE_ENTRIES[entry].capitalize(),
            )

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        for entry in list(dirnames) + filenames:
            full = os.path.join(dirpath, entry)
            rel = os.path.relpath(full, root)
            if os.path.islink(full):
                target = os.path.realpath(full)
                if not within(root_real, target):
                    report.error(
                        "4.1", rel,
                        "is a symlink resolving outside the plugin root (%s); clients MUST "
                        "reject package paths that escape the root." % target,
                    )
                    if entry in dirnames:
                        dirnames.remove(entry)
        if ".git" in dirnames:
            dirnames.remove(".git")


# --------------------------------------------------------------------------
# output
# --------------------------------------------------------------------------

def validate(root):
    """Validate the plugin rooted at `root`.

    Returns (report, skill_count, mcp_server_count). Counts are of entries
    *discovered*, including any that were then rejected.
    """
    root = os.path.abspath(root)
    root_real = os.path.realpath(root)

    report = Report()
    manifest, version = validate_manifest(report, root)
    skills = validate_skills(report, root, root_real)
    servers = validate_mcp(report, root, root_real, version)
    validate_layout(report, root, root_real, manifest)

    if skills == 0 and servers == 0 and not report.errors:
        report.warn(
            "11.1", ".",
            "the plugin declares no skills and no MCP servers; it is valid but provides "
            "nothing to a client.",
        )
    return report, skills, servers


def render(report, root, skills, servers, quiet):
    order = {"error": 0, "warning": 1}
    findings = sorted(report.findings, key=lambda f: (order[f["level"]], f["where"]))
    if quiet:
        findings = [f for f in findings if f["level"] == "error"]

    label = {"error": "ERROR", "warning": "WARN "}
    lines = ["Agent Plugins %s conformance check: %s" % (SPEC_VERSION, root), ""]
    for f in findings:
        lines.append("%s [§%s] %s" % (label[f["level"]], f["section"], f["where"]))
        lines.append("      %s" % f["message"])
    if findings:
        lines.append("")

    n_err, n_warn = len(report.errors), len(report.warnings)
    lines.append("Discovered: %d skill(s), %d MCP server entr(y/ies)." % (skills, servers))
    if n_err:
        lines.append("FAIL: %d error(s), %d warning(s)." % (n_err, n_warn))
    elif n_warn and not quiet:
        lines.append("PASS with %d warning(s): conformant, but review the warnings above." % n_warn)
    else:
        lines.append("PASS: conformant with Agent Plugins %s." % SPEC_VERSION)
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a plugin against the Agent Plugins Specification v%s." % SPEC_VERSION
    )
    parser.add_argument("plugin_dir", help="path to the plugin root")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit findings as JSON")
    parser.add_argument("--quiet", action="store_true", help="suppress warnings")
    args = parser.parse_args(argv)

    root = os.path.abspath(args.plugin_dir)
    if not os.path.isdir(root):
        sys.stderr.write("error: %s is not a directory\n" % root)
        return 2

    report, skills, servers = validate(root)

    if args.as_json:
        print(json.dumps({
            "spec_version": SPEC_VERSION,
            "plugin_dir": root,
            "conformant": not report.errors,
            "skills": skills,
            "mcp_servers": servers,
            "findings": report.findings,
        }, indent=2))
    else:
        print(render(report, root, skills, servers, args.quiet))

    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
