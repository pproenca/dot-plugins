#!/usr/bin/env zsh
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: swarm-cleanup.sh <tmux-socket> <window-ids-file> [session ...]" >&2
  exit 1
fi

TMUX_SOCKET="$1"
WINDOW_IDS_FILE="$2"
WORKING_DIR="$(cd "$(dirname "$WINDOW_IDS_FILE")/.." && pwd)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Prefer the backend the launcher actually resolved for this swarm. Guessing
# here is how teardown ends up driving a terminal the swarm never used.
TERMINAL_BACKEND="${SWARMFORGE_TERMINAL_BACKEND:-}"
if [[ -z "$TERMINAL_BACKEND" && -f "$WORKING_DIR/.swarmforge/env.tsv" ]]; then
  TERMINAL_BACKEND="$(awk -F'\t' '$1=="terminal-backend" {print $2; exit}' \
    "$WORKING_DIR/.swarmforge/env.tsv" 2>/dev/null || true)"
fi
TERMINAL_BACKEND="${TERMINAL_BACKEND:-terminal-app}"
shift
shift

has_command() {
  command -v "$1" &>/dev/null
}

source "$SCRIPT_DIR/swarm-terminal-adapter.sh"
load_terminal_backend "$TERMINAL_BACKEND"

if [[ -x "$SCRIPT_DIR/pack_board.sh" ]]; then
  "$SCRIPT_DIR/pack_board.sh" archive-all --root "$WORKING_DIR" || true
fi

if has_command bb; then
  bb "$SCRIPT_DIR/stop_handoff_daemon.bb" "$WORKING_DIR" 2>/dev/null || true
else
  DAEMON_PID_FILE="$WORKING_DIR/.swarmforge/daemon/handoffd.pid"
  if [[ -f "$DAEMON_PID_FILE" ]]; then
    daemon_pid="$(< "$DAEMON_PID_FILE")"
    if [[ "$daemon_pid" == <-> ]]; then
      kill -TERM "$daemon_pid" 2>/dev/null || true
    fi
    rm -f "$DAEMON_PID_FILE"
  fi
fi

for session in "$@"; do
  tmux -S "$TMUX_SOCKET" kill-session -t "$session" 2>/dev/null || true
done

sleep 1

if [[ -f "$WINDOW_IDS_FILE" ]]; then
  while IFS= read -r window_id; do
    [[ -n "$window_id" ]] || continue
    terminal_close_window "$window_id"
  done < "$WINDOW_IDS_FILE"
fi
