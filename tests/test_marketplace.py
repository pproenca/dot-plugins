"""The repository is a marketplace: client catalogs plus the plugins they list.

Agent Plugins v1.1.0 defines the plugin package only — distribution is left to
each client (§4, and the spec's own framing of installation as client-owned).
Catalogs are therefore client artifacts. Claude Code reads
`.claude-plugin/marketplace.json`; Codex reads
`.agents/plugins/marketplace.json`. These tests keep both catalogs and both
manifest formats in agreement with the portable plugin packages.
"""

import json
import subprocess
import sys

import pytest
from conftest import CODEX_MARKETPLACE, MARKETPLACE, PLUGINS_DIR, REPO_ROOT, VALIDATOR

CATALOG = json.loads(MARKETPLACE.read_text())
ENTRIES = CATALOG["plugins"]
IDS = [entry.get("name", "<unnamed>") for entry in ENTRIES]
CODEX_CATALOG = json.loads(CODEX_MARKETPLACE.read_text())
CODEX_ENTRIES = CODEX_CATALOG["plugins"]
CODEX_IDS = [entry.get("name", "<unnamed>") for entry in CODEX_ENTRIES]


def plugin_dir(entry):
    source = entry["source"]
    root = CATALOG.get("metadata", {}).get("pluginRoot")
    if isinstance(source, str) and not source.startswith("./") and "/" not in source and root:
        source = "%s/%s" % (root.rstrip("/"), source)
    return REPO_ROOT / source


def codex_plugin_dir(entry):
    source = entry["source"]
    assert source["source"] == "local"
    return REPO_ROOT / source["path"]


def test_catalog_has_required_fields():
    assert CATALOG["name"] and " " not in CATALOG["name"]
    assert CATALOG["owner"]["name"]
    assert isinstance(ENTRIES, list) and ENTRIES


def test_plugin_names_are_unique():
    assert len(IDS) == len(set(IDS))


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_source_is_a_relative_path_inside_the_marketplace(entry):
    """Relative sources resolve against the marketplace root, and `../` escapes it."""
    source = entry["source"]
    assert isinstance(source, str), "remote sources need their own reachability test"
    assert source.startswith("./") or "/" not in source
    assert ".." not in source.split("/")
    resolved = plugin_dir(entry).resolve()
    assert resolved.is_dir()
    assert resolved.is_relative_to(REPO_ROOT.resolve())


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_catalog_agrees_with_the_plugin_manifest(entry):
    """A stale catalog is how users get a plugin that isn't what the card promised."""
    manifest = json.loads((plugin_dir(entry) / "plugin.json").read_text())
    assert entry["name"] == manifest["name"]
    for field in ("version", "description", "license", "homepage"):
        if field in entry and field in manifest:
            assert entry[field] == manifest[field], field


@pytest.mark.parametrize("entry", ENTRIES, ids=IDS)
def test_listed_plugin_conforms(entry):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(plugin_dir(entry)), "--quiet"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_every_plugin_on_disk_is_listed():
    """An unlisted directory under plugins/ is invisible to users — catch the omission."""
    on_disk = {p.name for p in PLUGINS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")}
    assert on_disk == {plugin_dir(e).name for e in ENTRIES}


def test_codex_catalog_has_required_fields():
    assert CODEX_CATALOG["name"] == CATALOG["name"]
    assert CODEX_CATALOG["interface"]["displayName"]
    assert isinstance(CODEX_ENTRIES, list) and CODEX_ENTRIES
    assert len(CODEX_IDS) == len(set(CODEX_IDS))


@pytest.mark.parametrize("entry", CODEX_ENTRIES, ids=CODEX_IDS)
def test_codex_entry_is_installable(entry):
    assert entry["policy"] == {
        "installation": "AVAILABLE",
        "authentication": "ON_INSTALL",
    }
    assert entry["category"]

    plugin = codex_plugin_dir(entry).resolve()
    assert plugin.is_dir()
    assert plugin.is_relative_to(REPO_ROOT.resolve())

    manifest = json.loads((plugin / ".codex-plugin" / "plugin.json").read_text())
    portable_manifest = json.loads((plugin / "plugin.json").read_text())
    assert entry["name"] == manifest["name"] == portable_manifest["name"]
    for field in ("version", "description", "author", "homepage", "repository", "license", "keywords"):
        if field in manifest and field in portable_manifest:
            assert manifest[field] == portable_manifest[field], field


def test_client_catalogs_list_the_same_plugins():
    on_disk = {p.name for p in PLUGINS_DIR.iterdir() if p.is_dir() and not p.name.startswith(".")}
    assert set(CODEX_IDS) == set(IDS) == on_disk
