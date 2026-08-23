"""The repository is a marketplace: a catalog plus the plugins it lists.

Agent Plugins v1.1.0 defines the plugin package only — distribution is left to
each client (§4, and the spec's own framing of installation as client-owned).
The catalog is therefore a client artifact, `.claude-plugin/marketplace.json`,
and these tests hold the two halves together: every listed plugin exists and
conforms, and every plugin on disk is listed.
"""

import json
import subprocess
import sys

import pytest
from conftest import MARKETPLACE, PLUGINS_DIR, REPO_ROOT, VALIDATOR

CATALOG = json.loads(MARKETPLACE.read_text())
ENTRIES = CATALOG["plugins"]
IDS = [entry.get("name", "<unnamed>") for entry in ENTRIES]


def plugin_dir(entry):
    source = entry["source"]
    root = CATALOG.get("metadata", {}).get("pluginRoot")
    if isinstance(source, str) and not source.startswith("./") and "/" not in source and root:
        source = "%s/%s" % (root.rstrip("/"), source)
    return REPO_ROOT / source


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
