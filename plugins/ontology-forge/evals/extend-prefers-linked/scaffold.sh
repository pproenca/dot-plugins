#!/usr/bin/env bash
# Stages a minimal in-production Equipment type for the extension case.
set -euo pipefail
mkdir -p ontology/object-types ontology/link-types
cat > ontology/object-types/equipment.yaml <<'YAML'
apiName: equipment
displayName: Equipment
pluralDisplayName: Equipment
description: A serviceable piece of plant the maintenance team maintains.
status: active
primaryKey: equipmentId
titleProperty: equipmentName
properties:
  equipmentId:
    type: string
    description: Stable identifier from the asset register.
    required: true
  equipmentName:
    type: string
    description: Name the maintenance team uses for this equipment.
    required: true
  serialNumber:
    type: string
    description: Manufacturer serial number.
  manufacturer:
    type: string
    description: Who built it.
YAML
cat > ontology/DECISIONS.md <<'MD'
# Decisions

## Equipment is a core type

**Date:** 2026-08-01

Equipment is read by the maintenance scheduling app, the inspection workflow, and
the parts-ordering app. Treat its shape as stable.
MD
