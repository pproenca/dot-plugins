#!/usr/bin/env bash
# Manual runner for the eval suite, for use while `claude plugin eval` is gated.
set -euo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--list" || -z "${1:-}" ]]; then
  echo "Cases:"
  for d in "$here"/*/; do
    [[ -f "$d/prompt.md" ]] && echo "  $(basename "$d")"
  done
  echo
  echo "Usage: ./run-manual.sh <case>"
  exit 0
fi

case_dir="$here/$1"
[[ -f "$case_dir/prompt.md" ]] || { echo "No such case: $1" >&2; exit 1; }

work="$(mktemp -d)"
cd "$work"
[[ -f "$case_dir/scaffold.sh" ]] && bash "$case_dir/scaffold.sh"

echo "Workspace: $work"
[[ -d ontology ]] && echo "Staged:    $(find ontology -type f | wc -l | tr -d ' ') ontology files"
echo
echo "──────── PROMPT ────────"
cat "$case_dir/prompt.md"
echo "──────── GRADERS ───────"
for g in "$case_dir"/graders/*.md; do
  echo
  echo "### $(basename "$g" .md)"
  cat "$g"
done
echo
echo "────────────────────────"
echo "Run Claude in $work, then score the response against the graders above."
