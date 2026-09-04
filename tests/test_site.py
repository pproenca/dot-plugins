import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_marketplace_site.py"


def run_build(output: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), "--output", str(output), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )


def test_marketplace_site_builds_from_catalog(tmp_path):
    output = tmp_path / "site"
    result = run_build(output)

    assert result.returncode == 0, result.stderr
    data = json.loads((output / "data" / "plugins.json").read_text())
    catalog = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())

    assert [plugin["name"] for plugin in data["plugins"]] == [plugin["name"] for plugin in catalog["plugins"]]
    assert data["pluginCount"] == len(catalog["plugins"])
    assert data["skillCount"] == sum(plugin["skillCount"] for plugin in data["plugins"])
    assert (output / ".nojekyll").exists()
    assert all((output / plugin["icon"]).exists() for plugin in data["plugins"] if plugin["icon"])
    assert {Path(plugin["icon"]).suffix for plugin in data["plugins"] if plugin["icon"]} == {".png"}


def test_marketplace_site_accepts_matching_expected_version(tmp_path):
    output = tmp_path / "site"
    manifest = json.loads((ROOT / "plugins" / "pstack" / ".codex-plugin" / "plugin.json").read_text())

    result = run_build(output, "--expected-version", manifest["version"])

    assert result.returncode == 0, result.stderr
    data = json.loads((output / "data" / "plugins.json").read_text())
    assert {plugin["version"] for plugin in data["plugins"]} == {manifest["version"]}


def test_marketplace_site_rejects_mismatched_expected_version(tmp_path):
    output = tmp_path / "site"
    expected_version = "999.0.0"

    result = run_build(output, "--expected-version", expected_version)

    assert result.returncode != 0
    assert f"do not match expected release version {expected_version}" in result.stderr
    assert not (output / "data" / "plugins.json").exists()
