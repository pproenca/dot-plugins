#!/usr/bin/env bash
# Install the SwarmForge squad workflow into a project directory.
#
# Copies the squad payload and engine into the project, and pre-seeds the APS
# tooling so nothing reaches the network. The result is self-contained — it keeps
# working if this plugin is moved or uninstalled.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
PAYLOAD="$PLUGIN_ROOT/swarmforge"
ENGINE_DIR="$PAYLOAD/scripts"
CLOSE_SWARM="$PLUGIN_ROOT/close-swarm"
APS_NAME="Acceptance-Pipeline-Specification"
APS_SRC="$PLUGIN_ROOT/vendor/$APS_NAME"

# Marker replacing the github source in the project's tool-table for APS tools.
# squad_tool.clj only derives a clone URL for sources starting with "github.com/",
# so a non-github source makes the install path purely local.
APS_SOURCE="vendored:$APS_NAME"
APS_TOOLS="gherkin-parser:gherkin-parser ir-dry-checker:gherkin-ir-dry-checker gherkin-mutator:gherkin-mutator"

usage() {
  echo "Usage: install_squad.sh [project-dir] [--no-verify]" >&2
  echo "       install_squad.sh --update [project-dir] [--no-verify]" >&2
  echo >&2
  echo "Runs doctor.sh afterwards to check this host against the squad engine's" >&2
  echo "assumptions; --no-verify skips it." >&2
  echo >&2
  echo "Installs the squad workflow, or refreshes the engine and tooling of an" >&2
  echo "existing project without touching its confs, roles, or role-templates." >&2
  exit 1
}

case "${1:-}" in -h|--help) usage ;; esac

# --no-verify may appear anywhere; strip it before positional parsing.
VERIFY=1
args=()
for arg in "$@"; do
  if [[ "$arg" == "--no-verify" ]]; then VERIFY=0; else args+=("$arg"); fi
done
set -- "${args[@]+${args[@]}}"

UPDATE_ONLY=0
if [[ "${1:-}" == "--update" ]]; then
  UPDATE_ONLY=1
  shift
fi

PROJECT_ROOT="$(cd "${1:-.}" && pwd)"
TARGET="$PROJECT_ROOT/swarmforge"

# --- preflight -------------------------------------------------------------
missing=()
for cmd in zsh git tmux bb; do
  command -v "$cmd" >/dev/null 2>&1 || missing+=("$cmd")
done
if [[ ${#missing[@]} -gt 0 ]]; then
  echo "Error: SwarmForge needs these on PATH: ${missing[*]}" >&2
  echo "  bb is Babashka: brew install borkdude/brew/babashka" >&2
  exit 1
fi

for required in "$ENGINE_DIR" "$APS_SRC"; do
  if [[ ! -d "$required" ]]; then
    echo "Error: this plugin is incomplete, missing $required" >&2
    exit 1
  fi
done

if [[ $UPDATE_ONLY -eq 1 && ! -f "$TARGET/swarmforge.conf" ]]; then
  echo "Error: squad is not installed at $PROJECT_ROOT (missing swarmforge/swarmforge.conf)." >&2
  exit 1
fi

# --- payload ---------------------------------------------------------------
# Everything under swarmforge/ except the engine is project payload.
if [[ $UPDATE_ONLY -eq 0 ]]; then
  mkdir -p "$TARGET"
  for entry in "$PAYLOAD"/*; do
    name="$(basename "$entry")"
    [[ "$name" == "scripts" ]] && continue
    cp -R "$entry" "$TARGET/"
  done
fi

# --- engine ----------------------------------------------------------------
rm -rf "$TARGET/scripts"
mkdir -p "$TARGET/scripts"
cp -R "$ENGINE_DIR/." "$TARGET/scripts/"
find "$TARGET/scripts" -type f \( -name '*.sh' -o -name '*.clj' \) -exec chmod 755 {} +

cp "$CLOSE_SWARM" "$PROJECT_ROOT/close-swarm"
chmod 755 "$PROJECT_ROOT/close-swarm"

# --- APS tooling, pre-seeded into squad's tool cache -----------------------
CACHE="$PROJECT_ROOT/.swarmforge/tools"
mkdir -p "$CACHE/bin" "$CACHE/src" "$CACHE/cache" "$CACHE/manifests" "$CACHE/locks"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

for pair in $APS_TOOLS; do
  tool="${pair%%:*}"
  bb_task="${pair##*:}"
  rm -rf "$CACHE/src/$tool"
  mkdir -p "$CACHE/src/$tool"
  cp -R "$APS_SRC/." "$CACHE/src/$tool/"
  cat > "$CACHE/bin/$tool" <<EOF
#!/usr/bin/env bash
exec bb --config "$CACHE/src/$tool/bb.edn" $bb_task "\$@"
EOF
  chmod 755 "$CACHE/bin/$tool"
  cat > "$CACHE/manifests/$tool.manifest" <<EOF
tool: $tool
source: $APS_SOURCE
version: latest
executable: $CACHE/bin/$tool
registered_at: $NOW
EOF
done

# Point the project's tool table at the vendored copy so squad_tool never
# derives a clone URL for these three.
TOOL_TABLE="$TARGET/tool-table.edn"
if [[ -f "$TOOL_TABLE" ]]; then
  tmp="$(mktemp)"
  sed "s|\"github.com/unclebob/$APS_NAME\"|\"$APS_SOURCE\"|g" "$TOOL_TABLE" > "$tmp"
  mv "$tmp" "$TOOL_TABLE"
fi

# --- launcher --------------------------------------------------------------
cat > "$PROJECT_ROOT/swarm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$SCRIPT_DIR/swarmforge/scripts" ]]; then
  echo "SwarmForge engine missing at swarmforge/scripts." >&2
  echo "Re-run install_squad.sh --update from the swarm-forge-squad plugin." >&2
  exit 1
fi
exec "$SCRIPT_DIR/swarmforge/scripts/swarmforge.sh" "$@"
EOF
chmod 755 "$PROJECT_ROOT/swarm"

# --- git hygiene -----------------------------------------------------------
touch "$PROJECT_ROOT/.gitignore"
for entry in '.swarmforge/' '.worktrees/' '.squad/'; do
  grep -qxF "$entry" "$PROJECT_ROOT/.gitignore" || echo "$entry" >> "$PROJECT_ROOT/.gitignore"
done

# --- report ----------------------------------------------------------------
if [[ $UPDATE_ONLY -eq 1 ]]; then
  echo "Updated the engine and APS tooling in $PROJECT_ROOT"
else
  echo "Installed the squad workflow into $PROJECT_ROOT"
  echo "  persistent roles: $(ls "$TARGET/roles" | grep '\.prompt$' | sed 's/\.prompt$//' | tr '\n' ' ')"
  echo "  worker templates: $(ls "$TARGET/role-templates" | grep '\.prompt$' | sed 's/\.prompt$//' | tr '\n' ' ')"
fi
echo "  engine:   swarmforge/scripts/ ($(find "$TARGET/scripts" -type f | wc -l | tr -d ' ') files, project-local)"
echo "  tooling:  .swarmforge/tools/bin/ (gherkin-parser, ir-dry-checker, gherkin-mutator)"

if [[ $VERIFY -eq 1 && -x "$SELF_DIR/doctor.sh" ]]; then
  echo
  # Catch a host whose configuration breaks an engine assumption now, rather
  # than silently in the middle of a swarm.
  if ! "$SELF_DIR/doctor.sh" "$PROJECT_ROOT"; then
    echo >&2
    echo "Install completed, but this host failed the checks above." >&2
    exit 1
  fi
fi

echo
echo "Review swarmforge/squad.conf before starting, then:  cd $PROJECT_ROOT && ./swarm"
