"""End-to-end checks for the swarm-forge install scripts.

These guard the property that makes the plugin usable offline: installing a pack
must produce a project that is fully self-contained -- it carries its own engine
and Acceptance Pipeline tooling, and holds no path back into the plugin, so it
keeps working when the plugin is upgraded, moved, or removed.
"""

import os
import shutil
import subprocess

import pytest
from conftest import PLUGINS_DIR

SWARM_FORGE = PLUGINS_DIR / "swarm-forge"
INSTALL_PACK = SWARM_FORGE / "skills" / "swarm-forge" / "scripts" / "install_pack.sh"
SQUAD = PLUGINS_DIR / "swarm-forge-squad"
INSTALL_SQUAD = SQUAD / "skills" / "swarm-forge-squad" / "scripts" / "install_squad.sh"

APS = "Acceptance-Pipeline-Specification"
APS_TOOLS = ("gherkin-parser", "ir-dry-checker", "gherkin-mutator")

# The install scripts refuse to run without these, matching the engine's own
# startup checks. Skip rather than fail on a host that lacks them.
REQUIRED_COMMANDS = ("zsh", "git", "tmux", "bb")
missing = [c for c in REQUIRED_COMMANDS if shutil.which(c) is None]
pytestmark = pytest.mark.skipif(
    bool(missing), reason="needs %s on PATH" % ", ".join(missing)
)


def run_install(script, args, cwd):
    return subprocess.run(
        [str(script), *args],
        capture_output=True,
        text=True,
        cwd=str(cwd),
    )


def is_executable(path):
    return path.is_file() and os.access(path, os.X_OK)


def files_mentioning(root, needle):
    """Every file under root whose bytes contain needle."""
    hits = []
    raw = needle.encode()
    for dirpath, _dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                with open(path, "rb") as handle:
                    if raw in handle.read():
                        hits.append(os.path.relpath(path, root))
            except OSError:
                continue
    return hits


@pytest.fixture(scope="module")
def installed(tmp_path_factory):
    project = tmp_path_factory.mktemp("swarm_project")
    result = run_install(INSTALL_PACK, ["four-pack", str(project)], project)
    assert result.returncode == 0, result.stderr
    return project


def test_pack_payload_is_installed(installed):
    forge = installed / "swarmforge"
    assert (forge / "swarmforge.conf").is_file()
    assert (forge / "constitution.prompt").is_file()
    for role in ("specifier", "coder", "refactorer", "architect"):
        assert (forge / "roles" / ("%s.prompt" % role)).is_file()


def test_shared_articles_merge_without_clobbering_pack_overrides(installed):
    articles = installed / "swarmforge" / "constitution" / "articles"
    names = {p.name for p in articles.glob("*.prompt")}
    # four-pack ships only project.prompt, so all three shared articles land.
    assert {"project.prompt", "engineering.prompt", "handoffs.prompt", "workflow.prompt"} <= names


def test_two_pack_keeps_its_own_article_overrides(tmp_path):
    project = tmp_path / "two"
    project.mkdir()
    result = run_install(INSTALL_PACK, ["two-pack", str(project)], project)
    assert result.returncode == 0, result.stderr
    # two-pack ships its own engineering/workflow; only handoffs is added.
    assert "kept pack's own" in result.stdout
    articles = project / "swarmforge" / "constitution" / "articles"
    pack_engineering = (SWARM_FORGE / "packs" / "two-pack" / "constitution" / "articles"
                        / "engineering.prompt").read_bytes()
    assert (articles / "engineering.prompt").read_bytes() == pack_engineering


def test_engine_is_copied_into_the_project(installed):
    scripts = installed / "swarmforge" / "scripts"
    assert is_executable(scripts / "swarmforge.sh")
    assert is_executable(scripts / "swarmforge.bb")
    assert (scripts / "pack" / "dashboard.html").is_file()
    for adapter in ("terminal-app", "iterm2", "ghostty", "windows-terminal", "none"):
        assert is_executable(scripts / "terminal-adapters" / ("%s.sh" % adapter))


def test_every_required_helper_is_present_and_executable(installed):
    """The engine hard-fails at startup on a missing or non-executable helper."""
    source = (SWARM_FORGE / "swarmforge" / "scripts" / "swarmforge.bb").read_text()
    block = source.split("(def required-helpers", 1)[1].split("])", 1)[0]
    helpers = [chunk.split('"')[0] for chunk in block.split('"')[1::2]]
    assert len(helpers) >= 30, "failed to parse required-helpers"
    scripts = installed / "swarmforge" / "scripts"
    assert [h for h in helpers if not is_executable(scripts / h)] == []


def test_close_swarm_sits_where_the_dashboard_looks_for_it(installed):
    """pack_web.bb resolves close-swarm two levels above scripts/."""
    assert is_executable(installed / "close-swarm")


def test_launcher_is_present_and_plugin_free(installed):
    swarm = installed / "swarm"
    assert is_executable(swarm)
    assert str(SWARM_FORGE) not in swarm.read_text()


def test_aps_tooling_is_preseeded(installed):
    tools = installed / ".swarmforge" / "tools" / APS
    assert (tools / "bb.edn").is_file()
    for tool in APS_TOOLS:
        assert is_executable(installed / ".swarmforge" / "bin" / tool)


def test_gitignore_covers_runtime_state(installed):
    entries = set((installed / ".gitignore").read_text().split())
    assert {".swarmforge/", ".worktrees/", "swarmforge/scripts/"} <= entries


def test_installed_project_holds_no_path_into_the_plugin(installed):
    """The property that makes the project survive a plugin upgrade or removal."""
    assert files_mentioning(installed, str(SWARM_FORGE)) == []


def test_update_refreshes_engine_without_touching_the_pack(installed):
    conf = installed / "swarmforge" / "swarmforge.conf"
    before = conf.read_bytes()
    (installed / "swarmforge" / "scripts" / "swarmforge.sh").unlink()
    result = run_install(INSTALL_PACK, ["--update", str(installed)], installed)
    assert result.returncode == 0, result.stderr
    assert is_executable(installed / "swarmforge" / "scripts" / "swarmforge.sh")
    assert conf.read_bytes() == before


def test_unknown_pack_is_rejected(tmp_path):
    result = run_install(INSTALL_PACK, ["no-such-pack", str(tmp_path)], tmp_path)
    assert result.returncode != 0
    assert "unknown pack" in result.stderr


def test_squad_install_is_self_contained(tmp_path):
    project = tmp_path / "squad"
    project.mkdir()
    result = run_install(INSTALL_SQUAD, [str(project)], project)
    assert result.returncode == 0, result.stderr
    assert is_executable(project / "swarm")
    assert is_executable(project / "close-swarm")
    assert is_executable(project / "swarmforge" / "scripts" / "swarmforge.sh")
    assert (project / "swarmforge" / "role-templates" / "implementer.contract.edn").is_file()
    for tool in APS_TOOLS:
        assert is_executable(project / ".swarmforge" / "tools" / "bin" / tool)
        assert (project / ".swarmforge" / "tools" / "manifests" / ("%s.manifest" % tool)).is_file()
    # squad_tool must never derive a clone URL for the vendored APS tools.
    table = (project / "swarmforge" / "tool-table.edn").read_text()
    assert "github.com/unclebob/%s" % APS not in table
    assert files_mentioning(project, str(SQUAD)) == []
