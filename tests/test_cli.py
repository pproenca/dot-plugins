"""End-to-end CLI contract, plus dogfooding the shipped skill."""

import json
import shutil
import subprocess
import sys

from conftest import SKILL_DIR, VALIDATOR, manifest, mcp_config, skill_md


def run_cli(*args):
    return subprocess.run(
        [sys.executable, str(VALIDATOR), *args], capture_output=True, text=True
    )


def test_exit_zero_on_conformant_plugin(build):
    root = build(manifest=manifest(), skills={"demo": skill_md()})
    result = run_cli(str(root))
    assert result.returncode == 0
    assert "PASS" in result.stdout


def test_exit_one_on_violation(build):
    root = build(manifest=manifest(name="Bad-Name"))
    result = run_cli(str(root))
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_exit_two_on_missing_directory(tmp_path):
    result = run_cli(str(tmp_path / "does-not-exist"))
    assert result.returncode == 2
    assert "not a directory" in result.stderr


def test_json_output_shape(build):
    root = build(manifest=manifest(), skills={"demo": skill_md()})
    payload = json.loads(run_cli(str(root), "--json").stdout)
    assert payload["conformant"] is True
    assert payload["spec_version"] == "1.0.0"
    assert payload["skills"] == 1
    assert payload["findings"] == []


def test_json_findings_carry_section_and_location(build):
    root = build(manifest=manifest(name="Bad-Name"))
    payload = json.loads(run_cli(str(root), "--json").stdout)
    assert payload["conformant"] is False
    finding = payload["findings"][0]
    assert set(finding) == {"level", "section", "where", "message"}
    assert finding["section"] == "5.5"


def test_quiet_suppresses_warnings(build):
    root = build(manifest=manifest(), mcp=mcp_config({"s": {"type": "stdio", "command": "npx"}}))
    assert "WARN" in run_cli(str(root)).stdout
    assert "WARN" not in run_cli(str(root), "--quiet").stdout


# --- dogfood ------------------------------------------------------------

def test_shipped_skill_conforms_to_agent_skills_spec(tmp_path):
    """The skill this repo ships must itself pass the validator it bundles.

    The skill is copied rather than symlinked: a symlink pointing back at the
    repo would resolve outside the temporary plugin root and be rejected by the
    containment rules, which is correct behaviour but not what is under test.
    """
    root = tmp_path / "plugin"
    (root / "skills").mkdir(parents=True)
    shutil.copytree(SKILL_DIR, root / "skills" / SKILL_DIR.name)
    (root / "plugin.json").write_text(json.dumps(manifest(name="agent-plugin-tools")))

    result = run_cli(str(root))
    assert result.returncode == 0, result.stdout
    assert "1 skill(s)" in result.stdout
