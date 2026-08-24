#!/usr/bin/env python3
"""Synchronize the lockstep marketplace version for a Craft release."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SEMVER = re.compile(
    r"^(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)\."
    r"(?:0|[1-9]\d*)"
    r"(?:-(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
BOOTSTRAP_OLD_VERSION = "0.0.0"
BOOTSTRAP_NEW_VERSION = "0.15.0"


class ReleaseVersionError(ValueError):
    """Raised when marketplace state is unsafe to update."""


@dataclass
class PluginFiles:
    name: str
    portable_path: Path
    codex_path: Path
    claude_entry: dict[str, Any]
    portable: dict[str, Any]
    codex: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise ReleaseVersionError(f"required file is missing: {path}")
    try:
        payload = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ReleaseVersionError(f"cannot read JSON from {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReleaseVersionError(f"expected a JSON object in {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


def _require_semver(value: str, label: str) -> str:
    normalized = value[1:] if value.startswith("v") else value
    if not SEMVER.fullmatch(normalized):
        raise ReleaseVersionError(f"{label} is not valid SemVer: {value!r}")
    return normalized


def _catalog_entries(payload: dict[str, Any], path: Path) -> list[dict[str, Any]]:
    entries = payload.get("plugins")
    if not isinstance(entries, list) or not entries:
        raise ReleaseVersionError(f"{path} must contain a non-empty plugins list")
    if not all(isinstance(entry, dict) for entry in entries):
        raise ReleaseVersionError(f"{path} contains a non-object plugin entry")
    return entries


def _safe_plugin_path(root: Path, source: str, catalog_path: Path) -> Path:
    if not source.startswith("./") or ".." in Path(source).parts:
        raise ReleaseVersionError(f"unsafe plugin source {source!r} in {catalog_path}")
    resolved = (root / source).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ReleaseVersionError(f"plugin source escapes the repository: {source!r}")
    return resolved


def _entry_map(entries: list[dict[str, Any]], path: Path) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in entries:
        name = entry.get("name")
        if not isinstance(name, str) or not name:
            raise ReleaseVersionError(f"plugin entry without a valid name in {path}")
        if name in result:
            raise ReleaseVersionError(f"duplicate plugin {name!r} in {path}")
        result[name] = entry
    return result


def _load_plugin_files(root: Path) -> tuple[Path, dict[str, Any], list[PluginFiles]]:
    claude_path = root / ".claude-plugin" / "marketplace.json"
    codex_catalog_path = root / ".agents" / "plugins" / "marketplace.json"
    claude_catalog = _read_json(claude_path)
    codex_catalog = _read_json(codex_catalog_path)
    claude_entries = _entry_map(_catalog_entries(claude_catalog, claude_path), claude_path)
    codex_entries = _entry_map(_catalog_entries(codex_catalog, codex_catalog_path), codex_catalog_path)

    if claude_entries.keys() != codex_entries.keys():
        raise ReleaseVersionError("Claude and Codex marketplace catalogs list different plugins")

    plugin_files: list[PluginFiles] = []
    for name in sorted(claude_entries):
        claude_entry = claude_entries[name]
        claude_source = claude_entry.get("source")
        if not isinstance(claude_source, str):
            raise ReleaseVersionError(f"Claude source for {name!r} must be a relative path")

        codex_source = codex_entries[name].get("source")
        if not isinstance(codex_source, dict) or codex_source.get("source") != "local":
            raise ReleaseVersionError(f"Codex source for {name!r} must be local")
        codex_path_value = codex_source.get("path")
        if not isinstance(codex_path_value, str):
            raise ReleaseVersionError(f"Codex source path for {name!r} is missing")

        plugin_dir = _safe_plugin_path(root, claude_source, claude_path)
        codex_plugin_dir = _safe_plugin_path(root, codex_path_value, codex_catalog_path)
        if plugin_dir != codex_plugin_dir:
            raise ReleaseVersionError(f"Claude and Codex sources disagree for {name!r}")

        portable_path = plugin_dir / "plugin.json"
        codex_path = plugin_dir / ".codex-plugin" / "plugin.json"
        portable = _read_json(portable_path)
        codex = _read_json(codex_path)
        if portable.get("name") != name or codex.get("name") != name:
            raise ReleaseVersionError(f"manifest name does not match catalog entry {name!r}")

        plugin_files.append(
            PluginFiles(
                name=name,
                portable_path=portable_path,
                codex_path=codex_path,
                claude_entry=claude_entry,
                portable=portable,
                codex=codex,
            )
        )

    return claude_path, claude_catalog, plugin_files


def sync_versions(root: Path, old_version: str, new_version: str) -> set[Path]:
    """Validate all version locations, then update them as one logical operation."""
    root = root.resolve()
    old_version = _require_semver(old_version, "old version")
    new_version = _require_semver(new_version, "new version")
    if old_version == new_version and not (
        old_version == BOOTSTRAP_OLD_VERSION and new_version == BOOTSTRAP_NEW_VERSION
    ):
        raise ReleaseVersionError("new version must differ from the previous version")

    claude_path, claude_catalog, plugin_files = _load_plugin_files(root)
    observed: dict[str, str] = {}
    for plugin in plugin_files:
        for label, payload in (
            ("portable manifest", plugin.portable),
            ("Codex manifest", plugin.codex),
            ("Claude catalog", plugin.claude_entry),
        ):
            version = payload.get("version")
            if not isinstance(version, str):
                raise ReleaseVersionError(f"{plugin.name} {label} has no string version")
            observed[f"{plugin.name} {label}"] = _require_semver(version, f"{plugin.name} {label} version")

    is_bootstrap = old_version == BOOTSTRAP_OLD_VERSION and new_version == BOOTSTRAP_NEW_VERSION
    if not is_bootstrap:
        drift = {label: version for label, version in observed.items() if version != old_version}
        if drift:
            details = ", ".join(f"{label}={version}" for label, version in sorted(drift.items()))
            raise ReleaseVersionError(f"version drift from {old_version}: {details}")

    for plugin in plugin_files:
        plugin.portable["version"] = new_version
        plugin.codex["version"] = new_version
        plugin.claude_entry["version"] = new_version

    changed = {claude_path}
    for plugin in plugin_files:
        changed.update((plugin.portable_path, plugin.codex_path))

    for plugin in plugin_files:
        _write_json(plugin.portable_path, plugin.portable)
        _write_json(plugin.codex_path, plugin.codex)
    _write_json(claude_path, claude_catalog)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("old_version", nargs="?", help="previous version (Craft also sets CRAFT_OLD_VERSION)")
    parser.add_argument("new_version", nargs="?", help="new version (Craft also sets CRAFT_NEW_VERSION)")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    old_version = os.environ.get("CRAFT_OLD_VERSION") or args.old_version
    new_version = os.environ.get("CRAFT_NEW_VERSION") or args.new_version
    if not old_version or not new_version:
        parser.error("old and new versions are required through Craft variables or positional arguments")

    try:
        changed = sync_versions(args.root, old_version, new_version)
    except ReleaseVersionError as exc:
        parser.exit(1, f"version synchronization failed: {exc}\n")

    for path in sorted(changed):
        print(path.relative_to(args.root.resolve()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
