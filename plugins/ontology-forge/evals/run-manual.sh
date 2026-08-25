#!/usr/bin/env bash
# Stopgap runner, for use while `claude plugin eval` is in early access.
#
# Reads the same case format the official runner consumes -- prompt.md frontmatter,
# graders/*.md with a type:, case.yaml for the scaffold -- so nothing here is a second
# format to migrate later. Once early access lands, run the real thing instead:
#
#   claude plugin eval . --scaffold --ablation with-without --runs 3
#
# and delete this script.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

body() { awk 'NR==1 && $0=="---" {inside=1; next} inside && $0=="---" {inside=0; next} !inside' "$1"; }
frontmatter() { awk 'NR==1 && $0=="---" {inside=1; next} inside && $0=="---" {exit} inside' "$1"; }

if [[ "${1:-}" == "--list" || -z "${1:-}" ]]; then
  echo "Cases:"
  for d in "$here"/*/; do
    [[ -f "$d/prompt.md" ]] || continue
    tags="$(frontmatter "$d/prompt.md" | sed -n 's/^tags: //p')"
    printf '  %-34s %s\n' "$(basename "$d")" "${tags:-}"
  done
  echo
  echo "Usage: ./run-manual.sh <case>"
  exit 0
fi

case_dir="$here/$1"
[[ -f "$case_dir/prompt.md" ]] || { echo "No such case: $1" >&2; exit 1; }

work="$(mktemp -d)"
cd "$work"
if [[ -f "$case_dir/scaffold.sh" ]]; then
  bash "$case_dir/scaffold.sh"
  [[ -f "$case_dir/case.yaml" ]] || echo "warning: scaffold.sh with no case.yaml -- the official runner will not stage it" >&2
fi

echo "Workspace: $work"
[[ -d ontology ]] && echo "Staged:    $(find ontology -type f | wc -l | tr -d ' ') ontology files"
echo
echo "──────── CASE ─────────"
frontmatter "$case_dir/prompt.md"
echo "──────── PROMPT ───────"
body "$case_dir/prompt.md"
echo "──────── GRADERS ──────"
for g in "$case_dir"/graders/*.md; do
  echo
  echo "### $(basename "$g" .md)  [$(frontmatter "$g" | sed -n 's/^type: //p')]"
  frontmatter "$g" | grep -vE '^(type|name):' || true
  body "$g"
done
echo
echo "───────────────────────"
echo "Run Claude in $work, then score the response against the graders above."
echo "Deterministic graders (regex, tool_used, file_exists) are checkable without judgement."
