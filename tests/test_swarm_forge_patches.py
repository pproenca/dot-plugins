"""Guards for the local patches applied to the vendored swarm-forge engine.

The engine is vendored verbatim so it can be re-vendored with a plain copy.
`plugins/swarm-forge/patches/` holds the deliberate exceptions. A re-vendor that
forgets to re-apply them would silently reintroduce bugs that are invisible from
the UI, so these tests fail loudly instead.

The pane-base-index test is behavioral: it stands up a real tmux server
configured the way a typical `.tmux.conf` configures one, drives the dashboard's
own task-post entry point, and asserts the text actually reached the pane.
"""

import os
import shutil
import subprocess

import pytest
from conftest import PLUGINS_DIR

SWARM_FORGE = PLUGINS_DIR / "swarm-forge"
SCRIPTS = SWARM_FORGE / "swarmforge" / "scripts"
PACK_WEB = SCRIPTS / "pack_web.bb"
PATCHES = SWARM_FORGE / "patches"
DOCTOR = SWARM_FORGE / "skills" / "swarm-forge" / "scripts" / "doctor.sh"

missing = [c for c in ("bb", "tmux") if shutil.which(c) is None]
needs_tools = pytest.mark.skipif(bool(missing), reason="needs %s on PATH" % ", ".join(missing))


def test_patches_are_documented():
    assert (PATCHES / "README.md").is_file()
    assert list(PATCHES.glob("*.patch")), "no patch files recorded"


def test_pane_target_does_not_hardcode_pane_zero():
    """The upstream bug: every cockpit write lands on a pane that may not exist."""
    source = PACK_WEB.read_text()
    assert '":" window ".0"' not in source, (
        "pack_web.bb hardcodes tmux pane .0 again -- re-apply patches/0001"
    )
    assert "defn pane-base-index" in source


def test_teardown_steps_are_isolated():
    source = PACK_WEB.read_text()
    assert "defn teardown-step!" in source, (
        "teardown lost its per-step isolation -- re-apply patches/0001"
    )
    assert "(catch Exception _))\n      (System/exit 0)" not in source, (
        "teardown failures are being swallowed again -- re-apply patches/0001"
    )


@needs_tools
def test_cockpit_reaches_the_agent_pane_when_pane_base_index_is_one(tmp_path):
    """End to end against a real tmux server with pane-base-index 1.

    Without the patch this delivers nothing at all, while the API still reports
    success -- so a text-only assertion would not be enough.
    """
    root = tmp_path / "project"
    (root / ".swarmforge" / "board").mkdir(parents=True)
    received = tmp_path / "received.txt"
    # tmux sockets are AF_UNIX paths, which are limited to ~104 bytes.
    sock = "/tmp/sf-panebase-test.sock"

    def tmux(*args, check=True):
        return subprocess.run(["tmux", "-S", sock, *args], capture_output=True,
                              text=True, check=check)

    subprocess.run(["rm", "-f", sock], check=False)
    try:
        tmux("-f", "/dev/null", "new-session", "-d", "-s", "boot", "sleep 120")
        tmux("set-option", "-g", "base-index", "1")
        tmux("set-option", "-gw", "pane-base-index", "1")
        tmux("kill-session", "-t", "boot")
        tmux("new-session", "-d", "-s", "swarmforge-coder", "-n", "Coder",
             "cat > %s" % received)

        assert tmux("show-options", "-gwqv", "pane-base-index").stdout.strip() == "1"

        (root / ".swarmforge" / "roles.tsv").write_text(
            "coder\tmaster\t%s\tswarmforge-coder\tCoder\tcodex\ttask\n" % root
        )
        (root / ".swarmforge" / "tmux-socket").write_text(sock + "\n")

        result = subprocess.run(
            ["bb", str(PACK_WEB), "--test-post-task", str(root), "demo", "Hello cockpit"],
            capture_output=True, text=True, cwd=str(SCRIPTS),
        )
        assert result.returncode == 0, result.stderr

        tmux("send-keys", "-t", "swarmforge-coder", "C-d", check=False)
        subprocess.run(["sleep", "1"], check=False)

        delivered = received.read_text() if received.exists() else ""
        assert "Hello cockpit" in delivered, (
            "cockpit injection never reached the pane (delivered=%r) -- "
            "pane-base-index handling regressed" % delivered
        )
    finally:
        tmux("kill-server", check=False)
        subprocess.run(["rm", "-f", sock], check=False)


@needs_tools
def test_upstream_suite_still_passes_with_the_patch(tmp_path):
    """The patch must not fork upstream's own tests: they stay byte-identical."""
    result = subprocess.run(["bb", "test"], capture_output=True, text=True,
                            cwd=str(SWARM_FORGE))
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 failures, 0 errors" in (result.stdout + result.stderr)


def test_launcher_is_the_only_producer_of_host_facts():
    """One producer per fact. That is the whole point of the contract.

    The bugs in patches/0001 both came from a second component re-deriving
    something the launcher had already resolved, so a reader growing its own
    `detect-tmux-base-indexes` is the regression to catch.
    """
    launcher = (SCRIPTS / "swarmforge.bb").read_text()
    assert "defn write-env-file!" in launcher, "launcher no longer records the contract"
    assert "detect-tmux-base-indexes" in launcher

    for reader in ("pack_web.bb", "handoffd.bb", "pack_board.bb"):
        source = (SCRIPTS / reader).read_text()
        assert "detect-tmux-base-indexes" not in source, (
            "%s re-derives a fact the launcher already recorded" % reader
        )


def test_readers_consume_the_contract():
    pack_web = (SCRIPTS / "pack_web.bb").read_text()
    assert "env.tsv" in pack_web, "the dashboard no longer reads the host contract"
    cleanup = (SCRIPTS / "swarm-cleanup.sh").read_text()
    assert "env.tsv" in cleanup, "cleanup no longer reads the recorded terminal backend"
    assert 'SWARMFORGE_TERMINAL_BACKEND:-terminal-app' not in cleanup, (
        "cleanup guesses the terminal backend again instead of reading it"
    )


@needs_tools
def test_contract_round_trips_from_launcher_to_dashboard(tmp_path):
    """Plant a non-default index in the contract; the dashboard must follow it.

    Uses the argv stub so this asserts the chosen target exactly, with no tmux
    server involved.
    """
    project = tmp_path / "project"
    (project / ".swarmforge" / "board").mkdir(parents=True)
    (project / ".swarmforge" / "roles.tsv").write_text(
        "coder\tmaster\t%s\tswarmforge-coder\tCoder\tcodex\ttask\n" % project
    )
    (project / ".swarmforge" / "tmux-socket").write_text("/tmp/sf-unused.sock\n")
    (project / ".swarmforge" / "env.tsv").write_text(
        "tmux-pane-base-index\t7\ntmux-window-base-index\t3\nterminal-backend\tnone\n"
    )
    argv = tmp_path / "argv.edn"
    result = subprocess.run(
        ["bb", str(SCRIPTS / "pack_web.bb"), "--test-post-task", str(project), "t", "hello"],
        capture_output=True, text=True, cwd=str(SCRIPTS),
        env={**os.environ, "SWARMFORGE_TMUX_STUB": str(argv)},
    )
    assert result.returncode == 0, result.stderr
    assert "swarmforge-coder:Coder.7" in argv.read_text(), (
        "the dashboard ignored the recorded pane-base-index"
    )


@needs_tools
def test_doctor_passes_on_this_host(tmp_path):
    """The doctor must agree that this host satisfies the engine's assumptions."""
    project = tmp_path / "project"
    project.mkdir()
    install = SWARM_FORGE / "skills" / "swarm-forge" / "scripts" / "install_pack.sh"
    setup = subprocess.run([str(install), "two-pack", str(project), "--no-verify"],
                           capture_output=True, text=True)
    assert setup.returncode == 0, setup.stderr

    result = subprocess.run([str(DOCTOR), str(project)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "cockpit text reaches the agent pane" in result.stdout


@needs_tools
def test_doctor_fails_when_the_engine_regresses(tmp_path):
    """A doctor that cannot fail is worthless.

    Reverse-apply the recorded patch inside an installed project to restore the
    genuine upstream engine, then confirm the doctor refuses it. This also
    proves the patch in `patches/` is a faithful, reversible description of the
    divergence.

    Note both halves of the patch have to go: the fix restores the correct pane
    index *and* adds a session-scoped fallback, and either one alone still
    delivers. That redundancy is deliberate.
    """
    project = tmp_path / "project"
    project.mkdir()
    install = SWARM_FORGE / "skills" / "swarm-forge" / "scripts" / "install_pack.sh"
    subprocess.run([str(install), "two-pack", str(project), "--no-verify"],
                   capture_output=True, text=True, check=True)

    # Revert the whole series, newest first, the way a patch series unwinds.
    patch_files = sorted(PATCHES.glob("*.patch"), reverse=True)
    assert patch_files, "no patches recorded"
    for patch_file in patch_files:
        reverted = subprocess.run(["patch", "-R", "-p1", "-i", str(patch_file)],
                                  cwd=str(project), capture_output=True, text=True)
        assert reverted.returncode == 0, "%s: %s%s" % (
            patch_file.name, reverted.stdout, reverted.stderr)

    engine = (project / "swarmforge" / "scripts" / "pack_web.bb").read_text()
    assert '":" window ".0"' in engine, "reverse-apply did not restore the upstream bug"

    result = subprocess.run([str(DOCTOR), str(project)], capture_output=True, text=True)
    assert result.returncode != 0, "doctor passed an engine that cannot reach its agents"
    assert "never reached the agent pane" in result.stdout
