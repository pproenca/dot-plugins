#!/usr/bin/env bash
# Verify that this host satisfies the SwarmForge squad engine's assumptions.
#
# Squad is a different engine from the packs, so this checks what squad
# actually relies on rather than reusing the pack checks wholesale. Notably
# squad addresses agents by tmux session name everywhere -- squadd/web.clj and
# squad_dashboard_request.clj both target the bare session -- so it is immune to
# the pane-base-index defect that affects the pack cockpit. What it does depend
# on is that session-scoped delivery works at all on this host.
#
# Usage: doctor.sh [project-dir]
set -uo pipefail   # deliberately not -e: every check should run

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
PROJECT_ROOT=""
if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  echo "Usage: doctor.sh [project-dir]" >&2
  exit 1
fi
if [[ $# -ge 1 ]]; then
  PROJECT_ROOT="$(cd "$1" && pwd)" || exit 1
fi

ENGINE="$PLUGIN_ROOT/swarmforge/scripts"
if [[ -n "$PROJECT_ROOT" && -d "$PROJECT_ROOT/swarmforge/scripts" ]]; then
  ENGINE="$PROJECT_ROOT/swarmforge/scripts"
fi

PASS=0; FAIL=0; SKIP=0
TMPDIR_DOC=""; DOC_SOCK=""; TD_SOCK=""

cleanup() {
  [[ -n "$DOC_SOCK" ]] && { tmux -S "$DOC_SOCK" kill-server >/dev/null 2>&1; rm -f "$DOC_SOCK"; }
  [[ -n "$TD_SOCK" ]] && { tmux -S "$TD_SOCK" kill-server >/dev/null 2>&1; rm -f "$TD_SOCK"; }
  [[ -n "$TMPDIR_DOC" && -d "$TMPDIR_DOC" ]] && rm -rf "$TMPDIR_DOC"
  return 0
}
trap cleanup EXIT

ok()   { printf '  \033[0;32mok\033[0m    %s\n' "$1"; PASS=$((PASS+1)); }
bad()  { printf '  \033[0;31mFAIL\033[0m  %s\n' "$1"; [[ $# -gt 1 ]] && printf '        %s\n' "$2"; FAIL=$((FAIL+1)); }
skip() { printf '  \033[1;33mskip\033[0m  %s\n' "$1"; SKIP=$((SKIP+1)); }

echo "SwarmForge squad doctor"
echo "  plugin:  $PLUGIN_ROOT"
[[ -n "$PROJECT_ROOT" ]] && echo "  project: $PROJECT_ROOT"
echo "  engine:  $ENGINE"
echo

# --- 1. prerequisites -------------------------------------------------------
echo "Prerequisites"
for cmd in zsh git tmux bb; do
  if command -v "$cmd" >/dev/null 2>&1; then ok "$cmd"; else bad "$cmd is not on PATH" "The squad launcher cannot start without it."; fi
done
backends=""
for cmd in codex claude copilot grok; do
  command -v "$cmd" >/dev/null 2>&1 && backends="$backends $cmd"
done
if [[ -n "$backends" ]]; then ok "agent backend:$backends"; else bad "no agent CLI found" "Need one of codex, claude, copilot, grok."; fi
# Squad's engine bb.edn is {:paths ["."]} -- no deps, so no JDK at runtime.
# Only `bb test` needs one, which is why this is informational.
if command -v java >/dev/null 2>&1 && java -version >/dev/null 2>&1; then
  ok "JDK present (only needed to run squad's own test suite)"
else
  skip "no JDK: squad runs fine, but 'bb test' in the plugin will not"
fi
echo

# --- 2. engine integrity ----------------------------------------------------
# Mirror the launcher's own rule: everything in required-helpers must exist and
# be executable, except the entries it exempts (bb.edn is config, not a script).
echo "Engine"
if [[ -f "$ENGINE/swarmforge.clj" ]]; then
  helpers=$(sed -n '/(def required-helpers/,/])/p' "$ENGINE/swarmforge.clj" | grep -o '"[^"]*"' | tr -d '"')
  exempt=$(sed -n '/(def non-executable-helpers/,/})/p' "$ENGINE/swarmforge.clj" | grep -o '"[^"]*"' | tr -d '"')
  missing=""
  for h in $helpers; do
    if [[ ! -e "$ENGINE/$h" ]]; then
      missing="$missing $h"
    elif [[ ! -x "$ENGINE/$h" ]]; then
      case " $exempt " in *" $h "*) : ;; *) missing="$missing $h" ;; esac
    fi
  done
  for a in terminal-app iterm2 ghostty windows-terminal none; do
    [[ -x "$ENGINE/terminal-adapters/$a.sh" ]] || missing="$missing terminal-adapters/$a.sh"
  done
  if [[ -z "$missing" ]]; then
    ok "all required helpers usable ($(echo "$helpers" | wc -w | tr -d ' ') + 5 adapters)"
  else
    bad "missing or not usable:$missing" "Re-run install_squad.sh --update."
  fi
  if [[ -f "$ENGINE/squadd/dashboard.html" ]]; then ok "squad dashboard.html present"
  else bad "squadd/dashboard.html missing" "The dashboard will fail at request time."; fi
else
  bad "engine not found at $ENGINE"
fi
echo

# --- 3. session-scoped delivery --------------------------------------------
# Squad addresses every agent by session name. This checks that primitive
# against this host's real tmux configuration. It is not a full squadd
# round-trip: it verifies the targeting squad relies on, not the web layer.
echo "Agent delivery (session-scoped, this host's tmux configuration)"
if ! command -v tmux >/dev/null 2>&1; then
  skip "needs tmux"
else
  TMPDIR_DOC="$(mktemp -d)"
  DOC_SOCK="/tmp/sq-doctor-$$.sock"   # AF_UNIX paths cap near 104 bytes
  rm -f "$DOC_SOCK"
  received="$TMPDIR_DOC/received.txt"
  # No -f: use the host's real tmux config, which is the point.
  if tmux -S "$DOC_SOCK" new-session -d -s swarmforge-squad-leader -n "Squad Leader" \
       "cat > $received" >/dev/null 2>&1; then
    # Read this while the server is still up: the probe session exits below.
    pane_base="$(tmux -S "$DOC_SOCK" show-options -gwqv pane-base-index 2>/dev/null)"
    [[ -z "$pane_base" ]] && pane_base=0
    probe="squad-doctor-probe-$$"
    if tmux -S "$DOC_SOCK" send-keys -t swarmforge-squad-leader -l "$probe" >/dev/null 2>&1 \
       && tmux -S "$DOC_SOCK" send-keys -t swarmforge-squad-leader C-m >/dev/null 2>&1; then
      sleep 1
      tmux -S "$DOC_SOCK" send-keys -t swarmforge-squad-leader C-d >/dev/null 2>&1
      sleep 1
      if [[ -s "$received" ]] && grep -q "$probe" "$received" 2>/dev/null; then
        ok "squad reaches an agent session (host pane-base-index=$pane_base; squad targets sessions, not panes)"
      else
        bad "text never reached the agent session" \
            "squadd chat, clarifications, and assignments will silently do nothing."
      fi
    else
      bad "tmux send-keys to a session name failed" \
          "squad targets agents by session everywhere; it cannot drive them on this host."
    fi
  else
    skip "could not start a tmux server on $DOC_SOCK"
  fi
fi
echo

# --- 4. teardown ------------------------------------------------------------
echo "Teardown"
if ! command -v tmux >/dev/null 2>&1 || ! command -v bb >/dev/null 2>&1; then
  skip "needs tmux and bb"
elif [[ ! -f "$PLUGIN_ROOT/close-swarm" ]]; then
  skip "close-swarm not found"
else
  td="$TMPDIR_DOC/teardown"
  mkdir -p "$td/.swarmforge/daemon" "$td/swarmforge/scripts"
  cp -R "$ENGINE/." "$td/swarmforge/scripts/" 2>/dev/null
  cp "$PLUGIN_ROOT/close-swarm" "$td/close-swarm"; chmod 755 "$td/close-swarm"
  TD_SOCK="/tmp/sq-doctor-td-$$.sock"; rm -f "$TD_SOCK"
  if tmux -S "$TD_SOCK" new-session -d -s swarmforge-squad-td -n Doctor 'sleep 120' >/dev/null 2>&1; then
    echo "$TD_SOCK" > "$td/.swarmforge/tmux-socket"; : > "$td/.swarmforge/window-ids"
    printf 'squad-leader\tmaster\t%s\tswarmforge-squad-td\tDoctor\tcodex\ttask\n' "$td" > "$td/.swarmforge/roles.tsv"
    printf '1\tsquad-leader\tswarmforge-squad-td\tDoctor\tcodex\n' > "$td/.swarmforge/sessions.tsv"
    "$td/close-swarm" "$td" >/dev/null 2>&1
    sleep 1
    if tmux -S "$TD_SOCK" list-sessions >/dev/null 2>&1; then
      bad "close-swarm left tmux sessions running" \
          "Agents would survive teardown. Try SWARMFORGE_TERMINAL=none ./close-swarm and report the difference."
      tmux -S "$TD_SOCK" kill-server >/dev/null 2>&1
    else
      ok "close-swarm stops sessions cleanly"
    fi
    rm -f "$TD_SOCK"; TD_SOCK=""
  else
    skip "could not start a tmux server for the teardown check"
  fi
fi
echo

# --- 5. project-scoped checks ----------------------------------------------
if [[ -n "$PROJECT_ROOT" ]]; then
  echo "Project"
  if [[ -f "$PROJECT_ROOT/swarmforge/swarmforge.conf" && -f "$PROJECT_ROOT/swarmforge/squad.conf" ]]; then
    ok "squad installed (roster + squad.conf)"
  else
    bad "squad is not installed at $PROJECT_ROOT" "Run install_squad.sh $PROJECT_ROOT"
  fi

  templates=$(ls "$PROJECT_ROOT/swarmforge/role-templates"/*.prompt 2>/dev/null | wc -l | tr -d ' ')
  contracts=$(ls "$PROJECT_ROOT/swarmforge/role-templates"/*.contract.edn 2>/dev/null | wc -l | tr -d ' ')
  if [[ "$templates" -gt 0 && "$templates" == "$contracts" ]]; then
    ok "$templates worker templates, each with a capability contract"
  else
    bad "worker templates and contracts disagree ($templates prompts, $contracts contracts)" \
        "A template without its contract stalls when the leader tries to assign it."
  fi

  table="$PROJECT_ROOT/swarmforge/tool-table.edn"
  if [[ -f "$table" ]]; then
    if grep -q 'github.com/unclebob/Acceptance-Pipeline-Specification' "$table"; then
      bad "tool-table still points APS at GitHub" \
          "squad_tool will try to clone it. Run install_squad.sh --update $PROJECT_ROOT"
    else
      ok "APS tools point at the vendored copy (no clone on use)"
    fi
  else
    bad "tool-table.edn missing"
  fi

  aps_ok=1
  for tool in gherkin-parser ir-dry-checker gherkin-mutator; do
    bin="$PROJECT_ROOT/.swarmforge/tools/bin/$tool"
    man="$PROJECT_ROOT/.swarmforge/tools/manifests/$tool.manifest"
    [[ -x "$bin" && -f "$man" ]] || aps_ok=0
  done
  if [[ $aps_ok -eq 1 ]]; then ok "APS tooling pre-seeded in squad's tool cache (offline)"
  else bad "APS tooling missing from the tool cache" \
           "squad_tool require fails closed, so roles needing it will stop. Run install_squad.sh --update."; fi

  if grep -rl "$PLUGIN_ROOT" "$PROJECT_ROOT" >/dev/null 2>&1; then
    bad "project references the plugin directory" \
        "It will break when the plugin is upgraded or removed. Run install_squad.sh --update."
  else
    ok "self-contained (no path back into the plugin)"
  fi
  echo
fi

printf 'Summary: %d ok' "$PASS"
[[ $SKIP -gt 0 ]] && printf ', %d skipped' "$SKIP"
[[ $FAIL -gt 0 ]] && printf ', \033[0;31m%d failed\033[0m' "$FAIL"
printf '\n'
if [[ $FAIL -gt 0 ]]; then
  echo "This host does not satisfy the squad engine's assumptions. Fix the failures above before starting a swarm." >&2
  exit 1
fi
exit 0
