# The ontology spec format

## What this is, and what it is not

Foundry's Ontology Manager is the system of record. Types live there and are addressed by RID; there is no official on-disk YAML that round-trips into the platform.

So these files are a **design-time specification**: a diffable, reviewable artifact that captures the model *and the reasoning behind it*, which a human then implements in Ontology Manager or feeds to whatever provisioning the organization has built. Treat them as the design document, not as deployable configuration. Never tell the user these files change a live ontology.

What that buys: the model gets code review, decisions get version history, and an agent can read the whole ontology without platform access.

## Layout

```text
ontology/
├── DECISIONS.md              # why the model is shaped this way; every tradeoff taken
├── GLOSSARY.md               # domain terms, agreed with stakeholders
├── object-types/<apiName>.yaml
├── link-types/<apiName>.yaml
├── interfaces/<apiName>.yaml
├── action-types/<apiName>.yaml
├── shared-properties/<apiName>.yaml
└── mappings/<objectTypeApiName>.yaml
```

Default to `ontology/` at the repository root. If the user already has a directory, use theirs.

## Object type

```yaml
apiName: workOrder
displayName: Work Order
pluralDisplayName: Work Orders
description: >
  A unit of maintenance work raised against an asset, from request through
  completion. One work order covers one asset and one intervention.
status: active              # experimental | active | deprecated
groups: [maintenance]
implements: [inspectable, schedulable]
primaryKey: workOrderId
titleProperty: workOrderNumber
properties:
  workOrderId:
    type: string
    description: Stable identifier, sourced from the maintenance system.
    required: true
  workOrderNumber:
    type: string
    description: Human-facing reference shown to technicians, e.g. WO-10423.
    required: true
  raisedDate:
    type: timestamp
    description: When the work order was raised.
  workOrderStatus:
    type: string
    description: Lifecycle state.
    valueType: workOrderStatusEnum
    validValues: [draft, approved, inProgress, blocked, complete, cancelled]
  estimatedHours:
    type: double
    description: Planned technician hours. Null until the work order is approved.
  openDurationDays:
    type: integer
    description: Days between raisedDate and completion, or today if still open.
    derived: true
    derivation: Computed from raisedDate and completedDate.
```

`derived: true` marks a property computed rather than stored. Record where the computation lives — see the logic placement table in [structural-guidance.md](structural-guidance.md).

## Link type

```yaml
apiName: workOrderAsset
displayName: Work Order to Asset
description: The asset this work order is carried out on.
backing: direct             # direct | object-backed
cardinality: many-to-one    # one-to-one | one-to-many | many-to-one | many-to-many
from:
  objectType: workOrder
  apiName: asset            # workOrder.asset
to:
  objectType: asset
  apiName: workOrders       # asset.workOrders
```

Both `apiName` values must read as plain English from their own side. When the relationship carries its own data, use `backing: object-backed` and name the joining object type:

```yaml
apiName: employeeVenture
displayName: Employee to Venture
backing: object-backed
through: ventureStaffing    # object type holding role, startDate, allocation
cardinality: many-to-many
from: {objectType: employee, apiName: ventures}
to: {objectType: venture, apiName: staff}
```

## Interface

```yaml
apiName: inspectable
displayName: Inspectable
description: >
  Anything subject to periodic inspection. Implemented by assets, vessels and
  facilities so inspection workflows target the interface, not each type.
extends: []
properties:
  lastInspectionDate:
    type: timestamp
    description: Most recent completed inspection.
    required: true
  inspectionIntervalDays:
    type: integer
    description: Required days between inspections.
    required: true
implementedBy: [asset, vessel, facility]
```

## Action type

```yaml
apiName: closeWorkOrder
displayName: Close Work Order
description: >
  Records a technician completing the work: captures outcome, actual hours and
  parts used, and moves the work order to complete.
appliesTo: workOrder
businessOperation: >
  A technician finishing a job at the asset and signing it off.
parameters:
  outcome:
    type: string
    required: true
    validValues: [resolved, partiallyResolved, referredOnward]
  actualHours:
    type: double
    required: true
  notes:
    type: string
    required: false
modifies:
  - property: workOrderStatus
    to: complete
  - property: completedDate
    to: now()
sideEffects:
  - Creates a completionRecord object linked to this work order.
  - Notifies the requesting supervisor.
```

One action, one business operation. If the action modifies a single property and its name reads `Set X`, it is Action Sprawl — see [anti-patterns.md](anti-patterns.md).

## Shared property

```yaml
apiName: lastInspectionDate
displayName: Last Inspection Date
type: timestamp
description: Most recent completed inspection, consistent across all inspectable types.
usedBy: [asset, vessel, facility]
```

## Mapping

The stage 3 artifact. One file per object type.

```yaml
objectType: workOrder
sources:
  - dataset: /Maintenance/clean/work_orders
    role: primary
    primaryKey: wo_id -> workOrderId
    propertyMappings:
      wo_num: workOrderNumber
      raised_ts: raisedDate
      status_cd: workOrderStatus
    transformations:
      - Map status_cd through the code table to the workOrderStatus valid values.
    excluded:
      - _ingested_at: ETL metadata, no business meaning.
      - row_hash: pipeline artifact.
  - dataset: /Scheduling/clean/wo_estimates
    role: supplementary
    joinOn: wo_id
    propertyMappings:
      est_hours: estimatedHours
precedence: >
  Where both sources carry a value, the maintenance system wins; scheduling is
  a planning overlay and lags.
logicPlacement:
  - value: openDurationDays
    mechanism: derived-property
    rationale: Depends on today's date, so it cannot be pre-computed in a batch.
  - value: assetOpenWorkOrderCount
    mechanism: derived-property
    rationale: Counts linked objects; must not be stored on the asset.
unmapped:
  - property: estimatedHours
    reason: No source yet. Populated by hand until the scheduling feed lands.
```

`excluded` is as important as `propertyMappings` — it is the record that a column was considered and rejected, which is what stops the Kitchen Sink creeping back in on the next pass.

## DECISIONS.md

Append-only. One entry per decision that a future reader would otherwise have to reverse-engineer:

```markdown
## Merged HrEmployee and BadgeEmployee into Employee

**Date:** 2026-08-23
**Principle:** Domain-driven design; System Silos anti-pattern.

Two types described one person. Joined on `nationalId` in a pipeline, with HR
taking precedence on name and badge taking precedence on access dates.

**Tradeoff:** Badge records with no HR match are dropped. Roughly 40 contractors.
Revisit when the contractor feed is onboarded.
```

Record accepted compromises too. An undocumented shortcut is indistinguishable from an error.
