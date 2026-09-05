#!/usr/bin/env python3
"""Build the dependency-free GitHub Pages marketplace from plugin manifests."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "site"
CATALOG_PATH = ROOT / ".agents" / "plugins" / "marketplace.json"
REPOSITORY_URL = "https://github.com/pproenca/dot-plugins"


class MarketplaceVersionError(ValueError):
    pass


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_plugin(entry: dict, output_dir: Path) -> dict:
    plugin_dir = ROOT / entry["source"]["path"]
    manifest = load_json(plugin_dir / ".codex-plugin" / "plugin.json")
    interface = manifest.get("interface", {})
    skill_names = sorted(path.parent.name for path in (plugin_dir / "skills").glob("*/SKILL.md"))

    icon_source = plugin_dir / interface.get("logo", "")
    icon_name = f"{manifest['name']}{icon_source.suffix.lower()}"
    if icon_source.is_file():
        shutil.copy2(icon_source, output_dir / "assets" / "icons" / icon_name)

    return {
        "name": manifest["name"],
        "displayName": interface.get("displayName", manifest["name"]),
        "version": manifest["version"],
        "description": manifest["description"],
        "shortDescription": interface.get("shortDescription", manifest["description"]),
        "longDescription": interface.get("longDescription", manifest["description"]),
        "author": manifest.get("author", {}).get("name", "Unknown"),
        "license": manifest.get("license"),
        "category": interface.get("category", entry.get("category", "Other")),
        "brandColor": interface.get("brandColor", "#d8ff53"),
        "capabilities": interface.get("capabilities", []),
        "prompts": interface.get("defaultPrompt", []),
        "keywords": manifest.get("keywords", []),
        "skills": skill_names,
        "skillCount": len(skill_names),
        "icon": f"assets/icons/{icon_name}" if icon_source.is_file() else None,
        "homepage": manifest.get("homepage") or interface.get("websiteURL") or REPOSITORY_URL,
        "source": f"{REPOSITORY_URL}/tree/master/plugins/{manifest['name']}",
    }


def build(output_dir: Path, expected_version: str | None = None) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    shutil.copytree(SOURCE_DIR, output_dir)
    (output_dir / "assets" / "icons").mkdir(parents=True, exist_ok=True)

    catalog = load_json(CATALOG_PATH)
    plugins = [build_plugin(entry, output_dir) for entry in catalog["plugins"]]
    versions = {plugin["version"] for plugin in plugins}
    if expected_version is not None and versions != {expected_version}:
        raise MarketplaceVersionError(
            f"generated plugin versions {sorted(versions)} do not match expected release version {expected_version}"
        )

    payload = {
        "marketplace": catalog.get("interface", {}).get("displayName", catalog["name"]),
        "repository": REPOSITORY_URL,
        "pluginCount": len(plugins),
        "skillCount": sum(plugin["skillCount"] for plugin in plugins),
        "plugins": plugins,
    }
    data_dir = output_dir / "data"
    data_dir.mkdir(exist_ok=True)
    (data_dir / "plugins.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (output_dir / ".nojekyll").touch()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "_site")
    parser.add_argument("--expected-version")
    args = parser.parse_args()
    try:
        build(args.output.resolve(), args.expected_version)
    except MarketplaceVersionError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
