#!/usr/bin/env bash
# Stages the poisoned fixture as the working ontology.
# ANSWER-KEY.md is deliberately NOT copied — the model under test must not see it.
set -euo pipefail
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/../fixtures/poisoned" && pwd)"
cp -R "$src/ontology" ./ontology
