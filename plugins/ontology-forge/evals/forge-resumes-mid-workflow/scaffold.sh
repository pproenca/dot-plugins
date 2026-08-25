#!/usr/bin/env bash
# Stages a workflow abandoned partway through stage 02, with a live open question.
set -euo pipefail
mkdir -p ontology/object-types ontology/link-types
cat > ontology/STATUS.md <<'MD'
# Ontology status

**Stage:** 02 design-ontology — phase 3 of 7 (Links)
**Directory:** ontology/
**Updated:** 2026-08-18

## Stages

| Stage | State | Produced |
| ----- | ----- | -------- |
| 01 understand-domain | done | DOMAIN-BRIEF.md, GLOSSARY.md (18 terms) |
| 02 design-ontology | in progress | 2 object types, 0 link types |
| 03 map-sources | not started | — |

## Open questions

- [ ] Dispatch and billing both say "job". Dispatch means the visit; billing means the
      invoiced line. Raised stage 01. Blocks whether `Job` is one type or two.

## Thin evidence

- `Vessel.class` valid values taken from one operator's spreadsheet. Needs the fleet
  team to confirm the full set.

## Not yet modelled

- Crew rostering — deferred, brief section 5.

## Next

`/ontology-forge:design-ontology` — resume at phase 3.
MD
cat > ontology/DOMAIN-BRIEF.md <<'MD'
# Domain brief

## Scope
Scheduling vessel maintenance visits and reconciling them against invoices.

## Entities
- Vessel — a ship in the managed fleet.
- Port — where a visit happens.

## Open questions
- "Job" means different things to dispatch and to billing.
MD
cat > ontology/GLOSSARY.md <<'MD'
# Glossary

**Vessel** — a ship in the managed fleet.
**Port** — a facility where maintenance visits take place.
**Job** — CONFLICT. Dispatch: a scheduled visit. Billing: an invoiced line item.
MD
cat > ontology/object-types/vessel.yaml <<'YAML'
apiName: vessel
displayName: Vessel
pluralDisplayName: Vessels
description: A ship in the managed fleet.
primaryKey: imoNumber
titleProperty: vesselName
properties:
  imoNumber:
    type: string
    description: IMO number, the stable global identifier for a ship.
    required: true
  vesselName:
    type: string
    description: Name the fleet team uses for this vessel.
    required: true
YAML
cat > ontology/object-types/port.yaml <<'YAML'
apiName: port
displayName: Port
pluralDisplayName: Ports
description: A facility where maintenance visits take place.
primaryKey: unLocode
titleProperty: portName
properties:
  unLocode:
    type: string
    description: UN/LOCODE identifying the port.
    required: true
  portName:
    type: string
    description: Name in common use for the port.
    required: true
YAML
