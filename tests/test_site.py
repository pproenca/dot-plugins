import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD_SCRIPT = ROOT / "scripts" / "build_marketplace_site.py"


def test_marketplace_site_builds_from_catalog(tmp_path):
    output = tmp_path / "site"
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT), "--output", str(output)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    data = json.loads((output / "data" / "plugins.json").read_text())
    catalog = json.loads((ROOT / ".agents" / "plugins" / "marketplace.json").read_text())

    assert [plugin["name"] for plugin in data["plugins"]] == [plugin["name"] for plugin in catalog["plugins"]]
    assert data["pluginCount"] == len(catalog["plugins"])
    assert data["skillCount"] == sum(plugin["skillCount"] for plugin in data["plugins"])
    assert (output / ".nojekyll").exists()
    assert all((output / plugin["icon"]).exists() for plugin in data["plugins"] if plugin["icon"])
