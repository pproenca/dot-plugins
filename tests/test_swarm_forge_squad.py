"""Guards for the swarm-forge-squad plugin's host checks.

Squad is a separate engine from the packs, so its doctor checks different
assumptions: it addresses agents by tmux session name rather than by pane, its
`squad_tool require` fails closed instead of installing on demand, and every
worker template is paired with a capability contract the leader reads when it
assigns work.
"""

import shutil
import subprocess

import pytest
from conftest import PLUGINS_DIR

SQUAD = PLUGINS_DIR / "swarm-forge-squad"
SKILL = SQUAD / "skills" / "swarm-forge-squad" / "scripts"
INSTALL = SKILL / "install_squad.sh"
DOCTOR = SKILL / "doctor.sh"

missing = [c for c in ("bb", "tmux", "git", "zsh") if shutil.which(c) is None]
needs_tools = pytest.mark.skipif(bool(missing), reason="needs %s on PATH" % ", ".join(missing))


def install(project):
    project.mkdir(parents=True, exist_ok=True)
    result = subprocess.run([str(INSTALL), str(project), "--no-verify"],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return project


def doctor(project):
    return subprocess.run([str(DOCTOR), str(project)], capture_output=True, text=True)


def test_squad_targets_sessions_not_panes():
    """Squad's immunity to the pack cockpit's pane bug is a property worth pinning.

    If squad ever starts addressing panes, it inherits that whole failure mode,
    and its doctor would no longer be checking the right thing.
    """
    for name in ("squadd/web.clj", "squad_dashboard_request.clj"):
        source = (SQUAD / "swarmforge" / "scripts" / name).read_text()
        assert '".0"' not in source, "%s started addressing tmux panes by index" % name


@needs_tools
def test_doctor_passes_on_a_fresh_install(tmp_path):
    project = install(tmp_path / "project")
    result = doctor(project)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "squad reaches an agent session" in result.stdout
    assert "close-swarm stops sessions cleanly" in result.stdout


@needs_tools
def test_doctor_catches_a_tool_table_that_would_clone(tmp_path):
    """The offline guarantee lives in the tool table; a revert must be caught."""
    project = install(tmp_path / "project")
    table = project / "swarmforge" / "tool-table.edn"
    table.write_text(table.read_text().replace(
        "vendored:Acceptance-Pipeline-Specification",
        "github.com/unclebob/Acceptance-Pipeline-Specification"))
    result = doctor(project)
    assert result.returncode != 0
    assert "points APS at GitHub" in result.stdout


@needs_tools
def test_doctor_catches_an_unseeded_tool_cache(tmp_path):
    """squad_tool require fails closed, so a missing wrapper stops a role dead."""
    project = install(tmp_path / "project")
    (project / ".swarmforge" / "tools" / "bin" / "gherkin-parser").unlink()
    result = doctor(project)
    assert result.returncode != 0
    assert "missing from the tool cache" in result.stdout


@needs_tools
def test_doctor_catches_a_template_without_its_contract(tmp_path):
    project = install(tmp_path / "project")
    (project / "swarmforge" / "role-templates" / "qa.contract.edn").unlink()
    result = doctor(project)
    assert result.returncode != 0
    assert "templates and contracts disagree" in result.stdout
