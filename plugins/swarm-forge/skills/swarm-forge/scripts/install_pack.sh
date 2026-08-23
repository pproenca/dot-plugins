#!/usr/bin/env bash
# Install a SwarmForge pack into a project directory.
#
# Does locally exactly what upstream's `./swarm` bootstrap does over the network:
# lays down the pack payload, the shared engine, and the APS tooling. The result
# is self-contained — it keeps working if this plugin is moved or uninstalled.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLUGIN_ROOT="$(cd "$SELF_DIR/../../.." && pwd)"
PACKS_DIR="$PLUGIN_ROOT/packs"
ENGINE_DIR="$PLUGIN_ROOT/swarmforge/scripts"
SHARED_ARTICLES="$PLUGIN_ROOT/swarmforge/constitution/articles"
CLOSE_SWARM="$PLUGIN_ROOT/close-swarm"
APS_NAME="Acceptance-Pipeline-Specification"
APS_SRC="$PLUGIN_ROOT/vendor/$APS_NAME"

# tool name -> bb task, mirroring the catalog in swarmforge/scripts/swarm_tool.bb
APS_TOOLS="gherkin-parser:gherkin-parser ir-dry-checker:gherkin-ir-dry-checker gherkin-mutator:gherkin-mutator"

usage() {
  echo "Usage: install_pack.sh <pack> [project-dir] [--no-verify]" >&2
  echo "       install_pack.sh --update [project-dir] [--no-verify]" >&2
  echo >&2
  echo "Runs doctor.sh afterwards to check this host against the engine's" >&2
  echo "assumptions; --no-verify skips it." >&2
  echo >&2
  echo "Installs a pack, or refreshes the engine and tooling of an existing project" >&2
  echo "without touching its swarmforge.conf, roles, or constitution." >&2
  echo >&2
  echo "Packs:" >&2
  for p in "$PACKS_DIR"/*/; do
    [[ -d "$p" ]] || continue
    echo "  $(basename "$p")" >&2
  done
  exit 1
}

[[ $# -ge 1 ]] || usage
case "${1:-}" in -h|--help) usage ;; esac

# --no-verify may appear anywhere; strip it before positional parsing.
VERIFY=1
args=()
for arg in "$@"; do
  if [[ "$arg" == "--no-verify" ]]; then VERIFY=0; else args+=("$arg"); fi
done
set -- "${args[@]+${args[@]}}"
[[ $# -ge 1 ]] || usage

UPDATE_ONLY=0
if [[ "$1" == "--update" ]]; then
  UPDATE_ONLY=1
  shift
  PACK=""
else
  PACK="$1"
  shift
  PACK_DIR="$PACKS_DIR/$PACK"
  if [[ ! -d "$PACK_DIR" ]]; then
    echo "Error: unknown pack '$PACK'." >&2
    usage
  fi
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
  echo "Error: no pack installed at $PROJECT_ROOT (missing swarmforge/swarmforge.conf)." >&2
  echo "Install one first: install_pack.sh <pack> $PROJECT_ROOT" >&2
  exit 1
fi

# --- pack payload ----------------------------------------------------------
if [[ $UPDATE_ONLY -eq 0 ]]; then
  mkdir -p "$TARGET"
  cp -R "$PACK_DIR/." "$TARGET/"

  # Shared constitution articles, without clobbering a pack's own override.
  # Upstream documents this step but never implemented it; see the plugin README.
  mkdir -p "$TARGET/constitution/articles"
  installed_articles=()
  skipped_articles=()
  for article in "$SHARED_ARTICLES"/*.prompt; do
    [[ -e "$article" ]] || continue
    name="$(basename "$article")"
    if [[ -e "$TARGET/constitution/articles/$name" ]]; then
      skipped_articles+=("$name")
    else
      cp "$article" "$TARGET/constitution/articles/$name"
      installed_articles+=("$name")
    fi
  done
fi

# --- engine ----------------------------------------------------------------
# The engine lives in the project, exactly where upstream's curl bootstrap puts
# it. Nothing in the project may reference this plugin's path.
rm -rf "$TARGET/scripts"
mkdir -p "$TARGET/scripts"
cp -R "$ENGINE_DIR/." "$TARGET/scripts/"
find "$TARGET/scripts" -type f \( -name '*.sh' -o -name '*.bb' \) -exec chmod 755 {} +

# close-swarm sits two levels above scripts/, which is where pack_web.bb looks
# for it when the cockpit's Teardown runs.
cp "$CLOSE_SWARM" "$PROJECT_ROOT/close-swarm"
chmod 755 "$PROJECT_ROOT/close-swarm"

# --- APS tooling, pre-seeded so nothing reaches the network ----------------
# This is the directory swarm_tool.bb's source-dir computes when
# SWARMFORGE_TOOL_SRC is unset, so `ensure` finds bb.edn and skips its clone.
TOOLS_DIR="$PROJECT_ROOT/.swarmforge/tools/$APS_NAME"
BIN_DIR="$PROJECT_ROOT/.swarmforge/bin"
rm -rf "$TOOLS_DIR"
mkdir -p "$TOOLS_DIR" "$BIN_DIR"
cp -R "$APS_SRC/." "$TOOLS_DIR/"

for pair in $APS_TOOLS; do
  tool="${pair%%:*}"
  bb_task="${pair##*:}"
  cat > "$BIN_DIR/$tool" <<EOF
#!/usr/bin/env bash
exec bb --config "$TOOLS_DIR/bb.edn" $bb_task "\$@"
EOF
  chmod 755 "$BIN_DIR/$tool"
done

# --- launcher --------------------------------------------------------------
cat > "$PROJECT_ROOT/swarm" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -d "$SCRIPT_DIR/swarmforge/scripts" ]]; then
  echo "SwarmForge engine missing at swarmforge/scripts." >&2
  echo "Re-run install_pack.sh --update from the swarm-forge plugin." >&2
  exit 1
fi
exec "$SCRIPT_DIR/swarmforge/scripts/swarmforge.sh" "$@"
EOF
chmod 755 "$PROJECT_ROOT/swarm"

# --- git hygiene -----------------------------------------------------------
touch "$PROJECT_ROOT/.gitignore"
for entry in '.swarmforge/' '.worktrees/' 'swarmforge/scripts/'; do
  grep -qxF "$entry" "$PROJECT_ROOT/.gitignore" || echo "$entry" >> "$PROJECT_ROOT/.gitignore"
done

# --- report ----------------------------------------------------------------
if [[ $UPDATE_ONLY -eq 1 ]]; then
  echo "Updated the engine and APS tooling in $PROJECT_ROOT"
  echo "  pack left as-is: $(head -1 "$TARGET/swarmforge.conf" >/dev/null 2>&1 && echo "swarmforge.conf, roles/, constitution untouched")"
else
  echo "Installed pack '$PACK' into $PROJECT_ROOT"
  echo "  roles:    $(ls "$TARGET/roles" | sed 's/\.prompt$//' | tr '\n' ' ')"
  if [[ ${#installed_articles[@]} -gt 0 ]]; then
    echo "  articles: added ${installed_articles[*]}"
  fi
  if [[ ${#skipped_articles[@]} -gt 0 ]]; then
    echo "            kept pack's own ${skipped_articles[*]}"
  fi
fi
echo "  engine:   swarmforge/scripts/ ($(find "$TARGET/scripts" -type f | wc -l | tr -d ' ') files, project-local)"
echo "  tooling:  .swarmforge/bin/ (gherkin-parser, ir-dry-checker, gherkin-mutator)"

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
echo "Start the swarm with:  cd $PROJECT_ROOT && ./swarm"
