#!/usr/bin/env bash
# Verify that this host actually satisfies the SwarmForge engine's assumptions.
#
# The point is to fail here, at install time, rather than silently mid-swarm.
# The engine resolves several facts about the host at launch -- the tmux
# pane-base-index, the terminal backend -- and other programs re-derive them.
# A host whose configuration breaks one of those derivations produces failures
# that are invisible from the UI: the cockpit reports success while delivering
# nothing. These checks exercise the real machinery against this host's real
# configuration.
#
# Usage: doctor.sh [project-dir]
#   With a project, also checks that project's engine, tooling, and that it
#   holds no path back into the plugin.
set -uo pipefail   # deliberately not -e: every check should run

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
PROJECT_ROOT=""
if [[ $# -ge 1 && "${1:-}" != "-h" && "${1:-}" != "--help" ]]; then
  PROJECT_ROOT="$(cd "$1" && pwd)" || exit 1
fi
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: doctor.sh [project-dir]" >&2
  exit 1
fi

# Prefer the project's own engine when there is one: that is the code that will
# actually run.
ENGINE="$PLUGIN_ROOT/swarmforge/scripts"
if [[ -n "$PROJECT_ROOT" && -d "$PROJECT_ROOT/swarmforge/scripts" ]]; then
  ENGINE="$PROJECT_ROOT/swarmforge/scripts"
fi

PASS=0; FAIL=0; SKIP=0
TMPDIR_DOC=""; DOC_SOCK=""

cleanup() {
  [[ -n "$DOC_SOCK" ]] && tmux -S "$DOC_SOCK" kill-server >/dev/null 2>&1
  [[ -n "$DOC_SOCK" ]] && rm -f "$DOC_SOCK"
  [[ -n "$TMPDIR_DOC" && -d "$TMPDIR_DOC" ]] && rm -rf "$TMPDIR_DOC"
  return 0
}
trap cleanup EXIT

ok()   { printf '  \033[0;32mok\033[0m    %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[0;31mFAIL\033[0m  %s\n' "$1"; [[ $# -gt 1 ]] && printf '        %s\n' "$2"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[1;33mskip\033[0m  %s\n' "$1"; SKIP=$((SKIP+1)); }

echo "SwarmForge doctor"
echo "  plugin:  $PLUGIN_ROOT"
[[ -n "$PROJECT_ROOT" ]] && echo "  project: $PROJECT_ROOT"
echo "  engine:  $ENGINE"
echo

# --- 1. prerequisites -------------------------------------------------------
echo "Prerequisites"
for cmd in zsh git tmux bb; do
  if command -v "$cmd" >/dev/null 2>&1; then ok "$cmd"; else bad "$cmd is not on PATH" "SwarmForge cannot start without it."; fi
done
backends=""
for cmd in codex claude copilot grok; do
  command -v "$cmd" >/dev/null 2>&1 && backends="$backends $cmd"
done
if [[ -n "$backends" ]]; then ok "agent backend:$backends"; else bad "no agent CLI found" "Need one of codex, claude, copilot, grok."; fi
echo

# --- 2. engine integrity ----------------------------------------------------
# The launcher hard-fails at startup on a missing or non-executable helper, so
# check the same set it checks.
echo "Engine"
if [[ -f "$ENGINE/swarmforge.bb" ]]; then
  missing_helpers=""
  helpers=$(sed -n '/(def required-helpers/,/])/p' "$ENGINE/swarmforge.bb" | grep -o '"[^"]*"' | tr -d '"')
  for h in $helpers; do
    [[ -x "$ENGINE/$h" ]] || missing_helpers="$missing_helpers $h"
  done
  for a in terminal-app iterm2 ghostty windows-terminal none; do
    [[ -x "$ENGINE/terminal-adapters/$a.sh" ]] || missing_helpers="$missing_helpers terminal-adapters/$a.sh"
  done
  if [[ -z "$missing_helpers" ]]; then
    ok "all required helpers present and executable ($(echo "$helpers" | wc -w | tr -d ' ') + 5 adapters)"
  else
    bad "missing or non-executable:$missing_helpers" "Re-run install_pack.sh --update."
  fi
  if [[ -f "$ENGINE/pack/dashboard.html" ]]; then ok "cockpit dashboard.html present"
  else bad "pack/dashboard.html missing" "The dashboard will 500 at request time."; fi
else
  bad "engine not found at $ENGINE"
fi
echo

# --- 3. the check that matters: can the cockpit reach an agent pane? --------
# This is the failure that reports success. The engine resolves
# pane-base-index at launch; the dashboard must agree with it. We stand up a
# tmux server using THIS host's configuration and drive the dashboard's own
# task-post entry point.
echo "Cockpit -> agent delivery (this host's tmux configuration)"
if ! command -v tmux >/dev/null 2>&1 || ! command -v bb >/dev/null 2>&1; then
  skip "needs tmux and bb"
elif [[ ! -f "$ENGINE/pack_web.bb" ]]; then
  skip "pack_web.bb not found"
else
  TMPDIR_DOC="$(mktemp -d)"
  # AF_UNIX paths are capped near 104 bytes; keep the socket short.
  DOC_SOCK="/tmp/sf-doctor-$$.sock"
  rm -f "$DOC_SOCK"
  root="$TMPDIR_DOC/project"
  mkdir -p "$root/.swarmforge/board"
  received="$TMPDIR_DOC/received.txt"

  # No -f: use the host's real tmux config, which is the whole point.
  if tmux -S "$DOC_SOCK" new-session -d -s swarmforge-doctor -n Doctor "cat > $received" >/dev/null 2>&1; then
    pane_base="$(tmux -S "$DOC_SOCK" show-options -gwqv pane-base-index 2>/dev/null)"
    [[ -z "$pane_base" ]] && pane_base=0
    actual_pane="$(tmux -S "$DOC_SOCK" list-panes -t swarmforge-doctor -F '#{pane_index}' 2>/dev/null | head -1)"
    printf 'doctor\tmaster\t%s\tswarmforge-doctor\tDoctor\tcodex\ttask\n' "$root" > "$root/.swarmforge/roles.tsv"
    echo "$DOC_SOCK" > "$root/.swarmforge/tmux-socket"

    probe="swarmforge-doctor-probe-$$"
    bb "$ENGINE/pack_web.bb" --test-post-task "$root" doctor-check "$probe" >/dev/null 2>&1
    sleep 1
    tmux -S "$DOC_SOCK" send-keys -t swarmforge-doctor C-d >/dev/null 2>&1
    sleep 1

    if [[ -s "$received" ]] && grep -q "$probe" "$received" 2>/dev/null; then
      ok "cockpit text reaches the agent pane (pane-base-index=$pane_base, pane=$actual_pane)"
    else
      bad "cockpit text never reached the agent pane (pane-base-index=$pane_base, actual pane=$actual_pane)" \
          "New Task, chat, and clarification answers will silently do nothing on this host, while the dashboard still reports success. See patches/README.md."
    fi
  else
    skip "could not start a tmux server on $DOC_SOCK"
  fi
fi
echo

# --- 4. teardown actually tears down ---------------------------------------
echo "Teardown"
if ! command -v tmux >/dev/null 2>&1 || ! command -v bb >/dev/null 2>&1; then
  skip "needs tmux and bb"
else
  td="$TMPDIR_DOC/teardown"
  mkdir -p "$td/.swarmforge/daemon" "$td/swarmforge"
  cp -R "$ENGINE/." "$td/swarmforge/scripts/" 2>/dev/null
  [[ -f "$PLUGIN_ROOT/close-swarm" ]] && cp "$PLUGIN_ROOT/close-swarm" "$td/close-swarm" && chmod 755 "$td/close-swarm"
  td_sock="/tmp/sf-doctor-td-$$.sock"; rm -f "$td_sock"
  if tmux -S "$td_sock" new-session -d -s swarmforge-doctor-td -n Doctor 'sleep 120' >/dev/null 2>&1; then
    echo "$td_sock" > "$td/.swarmforge/tmux-socket"; : > "$td/.swarmforge/window-ids"
    printf 'doctor\tmaster\t%s\tswarmforge-doctor-td\tDoctor\tcodex\ttask\n' "$td" > "$td/.swarmforge/roles.tsv"
    printf '1\tdoctor\tswarmforge-doctor-td\tDoctor\tcodex\n' > "$td/.swarmforge/sessions.tsv"
    bb "$td/swarmforge/scripts/pack_web.bb" --test-teardown "$td" TEARDOWN >/dev/null 2>&1
    sleep 1
    if tmux -S "$td_sock" list-sessions >/dev/null 2>&1; then
      bad "teardown left tmux sessions running" \
          "Agents would survive the cockpit's Teardown button. Check .swarmforge/dashboard.log."
      tmux -S "$td_sock" kill-server >/dev/null 2>&1
    else
      ok "teardown stops sessions cleanly"
    fi
    rm -f "$td_sock"
  else
    skip "could not start a tmux server for the teardown check"
  fi
fi
echo

# --- 5. project-scoped checks ----------------------------------------------
if [[ -n "$PROJECT_ROOT" ]]; then
  echo "Project"
  if [[ -f "$PROJECT_ROOT/swarmforge/swarmforge.conf" ]]; then ok "pack installed"
  else bad "no pack at $PROJECT_ROOT" "Run install_pack.sh <pack> $PROJECT_ROOT"; fi

  aps_ok=1
  for tool in gherkin-parser ir-dry-checker gherkin-mutator; do
    if [[ -x "$PROJECT_ROOT/.swarmforge/bin/$tool" ]]; then
      "$PROJECT_ROOT/.swarmforge/bin/$tool" >/dev/null 2>&1
      status=$?
      # These print usage and exit non-zero with no args; only a missing
      # interpreter or source tree makes them fail to run at all.
      [[ $status -ge 126 ]] && aps_ok=0
    else
      aps_ok=0
    fi
  done
  if [[ $aps_ok -eq 1 ]]; then ok "APS tooling pre-seeded and runnable (offline)"
  else bad "APS tooling missing or not runnable" "Run install_pack.sh --update $PROJECT_ROOT"; fi

  if grep -rl "$PLUGIN_ROOT" "$PROJECT_ROOT" >/dev/null 2>&1; then
    bad "project references the plugin directory" \
        "It will break when the plugin is upgraded or removed. Run install_pack.sh --update."
  else
    ok "self-contained (no path back into the plugin)"
  fi
  echo
fi

# --- summary ----------------------------------------------------------------
printf 'Summary: %d ok' "$PASS"
[[ $SKIP -gt 0 ]] && printf ', %d skipped' "$SKIP"
[[ $FAIL -gt 0 ]] && printf ', \033[0;31m%d failed\033[0m' "$FAIL"
printf '\n'
if [[ $FAIL -gt 0 ]]; then
  echo "This host does not satisfy the engine's assumptions. Fix the failures above before starting a swarm." >&2
  exit 1
fi
exit 0
