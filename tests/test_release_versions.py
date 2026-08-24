import json
from pathlib import Path

import pytest

from scripts.sync_plugin_versions import ReleaseVersionError, sync_versions


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n")


def marketplace(tmp_path: Path, versions: tuple[str, str] = ("0.1.1", "0.14.3")) -> Path:
    names = ("alpha", "beta")
    claude_entries = []
    codex_entries = []
    for name, version in zip(names, versions, strict=True):
        source = f"./plugins/{name}"
        write_json(tmp_path / source / "plugin.json", {"name": name, "version": version})
        write_json(tmp_path / source / ".codex-plugin" / "plugin.json", {"name": name, "version": version})
        claude_entries.append({"name": name, "source": source, "version": version})
        codex_entries.append({"name": name, "source": {"source": "local", "path": source}})

    write_json(tmp_path / ".claude-plugin" / "marketplace.json", {"plugins": claude_entries})
    write_json(tmp_path / ".agents" / "plugins" / "marketplace.json", {"plugins": codex_entries})
    return tmp_path


def all_versions(root: Path) -> set[str]:
    catalog = json.loads((root / ".claude-plugin" / "marketplace.json").read_text())
    versions = {entry["version"] for entry in catalog["plugins"]}
    for entry in catalog["plugins"]:
        plugin = root / entry["source"]
        versions.add(json.loads((plugin / "plugin.json").read_text())["version"])
        versions.add(json.loads((plugin / ".codex-plugin" / "plugin.json").read_text())["version"])
    return versions


def test_bootstrap_allows_divergent_versions(tmp_path):
    root = marketplace(tmp_path)
    sync_versions(root, "0.0.0", "0.15.0")
    assert all_versions(root) == {"0.15.0"}


def test_subsequent_release_accepts_prefixed_old_tag(tmp_path):
    root = marketplace(tmp_path, ("0.15.0", "0.15.0"))
    sync_versions(root, "v0.15.0", "0.16.0")
    assert all_versions(root) == {"0.16.0"}


@pytest.mark.parametrize("new_version", ["1", "1.2", "01.2.3", "1.2.3-"])
def test_rejects_invalid_new_semver(tmp_path, new_version):
    root = marketplace(tmp_path, ("0.15.0", "0.15.0"))
    with pytest.raises(ReleaseVersionError, match="not valid SemVer"):
        sync_versions(root, "0.15.0", new_version)


def test_rejects_version_drift_before_writing(tmp_path):
    root = marketplace(tmp_path, ("0.15.0", "0.14.3"))
    before = (root / "plugins" / "alpha" / "plugin.json").read_text()
    with pytest.raises(ReleaseVersionError, match="version drift"):
        sync_versions(root, "0.15.0", "0.15.1")
    assert (root / "plugins" / "alpha" / "plugin.json").read_text() == before


def test_rejects_catalog_disagreement(tmp_path):
    root = marketplace(tmp_path, ("0.15.0", "0.15.0"))
    codex_path = root / ".agents" / "plugins" / "marketplace.json"
    codex = json.loads(codex_path.read_text())
    codex["plugins"].pop()
    write_json(codex_path, codex)
    with pytest.raises(ReleaseVersionError, match="list different plugins"):
        sync_versions(root, "0.15.0", "0.15.1")


def test_rejects_missing_manifest_before_writing(tmp_path):
    root = marketplace(tmp_path, ("0.15.0", "0.15.0"))
    before = (root / "plugins" / "alpha" / "plugin.json").read_text()
    (root / "plugins" / "beta" / ".codex-plugin" / "plugin.json").unlink()
    with pytest.raises(ReleaseVersionError, match="required file is missing"):
        sync_versions(root, "0.15.0", "0.15.1")
    assert (root / "plugins" / "alpha" / "plugin.json").read_text() == before
