#!/usr/bin/env bash
# Stages the clean fixture as the working ontology.
set -euo pipefail
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/../fixtures/clean" && pwd)"
cp -R "$src/ontology" ./ontology
