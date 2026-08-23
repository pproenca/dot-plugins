# The ontology spec format

## What this is, and what it is not

Foundry's Ontology Manager is the system of record. Types live there and are addressed by RID; there is no official on-disk YAML that round-trips into the platform.

So these files are a **design-time specification**: a diffable, reviewable artifact capturing the model *and the reasoning behind it*, which a human then implements in Ontology Manager or feeds to whatever provisioning the organization has. Treat them as the design document, not deployable configuration. Never tell the user these files change a live ontology.

What that buys: the model gets code review, decisions get version history, and an agent can read the whole ontology without platform access.

Element names and definitions follow [vocabulary.md](vocabulary.md).

## Layout

```text
ontology/
├── DOMAIN-BRIEF.md           # stage 01
├── GLOSSARY.md               # stage 01
├── DECISIONS.md              # why the model is shaped this way
├── object-types/<apiName>.yaml
├── link-types/<apiName>.yaml
├── interfaces/<apiName>.yaml
├── action-types/<apiName>.yaml
├── shared-properties/<apiName>.yaml
├── value-types/<apiName>.yaml
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
groups: [maintenance]       # object type groups, for search and exploration
hidden: false               # true for non-semantic technical types
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
    constraints:
      regex: '^WO-\d{5}$'
  raisedDate:
    type: timestamp
    description: When the work order was raised.
    required: true
  workOrderStatus:
    type: string
    description: Lifecycle state of the work order.
    valueType: workOrderStatusEnum
    constraints:
      enum: [draft, approved, inProgress, blocked, complete, cancelled]
  estimatedHours:
    type: double
    description: Planned technician hours. Null until the work order is approved.
    constraints:
      range: {min: 0, max: 500}
  openDurationDays:
    type: integer
    description: Days between raisedDate and completion, or today if still open.
    derived: true
    derivation: >
      Computed from raisedDate and completedDate at query time. Depends on the
      current date, so it cannot be pre-computed in a batch.
  partsUsedCount:
    type: integer
    description: How many parts this work order consumed.
    derived: true
    via: [workOrderParts]        # link path, at most 3 hops
    aggregation: count           # required when any hop is a "many" cardinality
    derivation: Counts linked part objects; storing it would go stale on every edit.
```

A derived property **cannot** be `required`, cannot carry `constraints`, cannot be the `primaryKey`, and cannot be text-searched. If the property needs any of those, store it instead and say why in `DECISIONS.md`. `via` holds the link path — at most three hops — and `aggregation` takes one of `count`, `average`, `sum`, `min`, `max`, `approximateCardinality`, `exactCardinality`, `collectList`, `collectSet`. See [platform-constraints.md](platform-constraints.md).

**`derived: true`** marks a property computed rather than stored, and `derivation` must say where the computation lives and why — see the placement table in [structural-guidance.md](structural-guidance.md).

**`hidden: true`** marks a non-semantic type that exists for a technical workflow rather than modelling the domain. It stays available to builders without cluttering default views.

**`constraints`** uses the value type constraint vocabulary in [vocabulary.md](vocabulary.md): `enum`, `range`, `regex`, `rid`, `uuid`, `unique`, `nested`, `elements`.

## Struct property

Group semantically related fields rather than flattening them:

```yaml
  address:
    type: struct
    array: true
    description: Known addresses for this facility, most recently occupied first.
    mainFields: [street, city, state, postalCode, country]
    reducers:                       # primary first; later entries break ties
      - by: lastOccupied
        take: latest                # numeric: highest|lowest · temporal: latest|earliest
      - by: datasource              # string: first|last · boolean: trueFirst|falseFirst
        take: first
    fields:
      street:      {type: string}
      city:        {type: string}
      state:       {type: string}
      postalCode:  {type: string, constraints: {regex: '^\d{5}(-\d{4})?$'}}
      country:     {type: string}
      geopoint:    {type: geopoint}
      lastOccupied: {type: timestamp, description: Used for reducer sorting.}
      datasource:  {type: string, description: Which source supplied this address.}
      llmConfidence: {type: double, description: Extraction confidence, 0-1.}
```

Ten `address*` properties tied together only by a naming convention is the shape this replaces.

A reducer picks one element of an array for **display and interface implementation** — the stored array is untouched. The reduced value cannot be filtered or queried, and an interface action targeting it will error, because reduction has no inverse. Reducers apply to numeric, temporal, string, and boolean arrays, and to struct arrays by one of their fields; see [platform-constraints.md](platform-constraints.md) for the unsupported types.

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

One link type, two sides — `from` and `to` are the two traversable directions of a single type, not two separate links. Both `apiName` values must read as plain English from their own side, and both are settled together. A link type may also relate an object type to itself. When the relationship carries its own data, use an object-backed link and name the joining type in domain language:

```yaml
apiName: employeeVenture
displayName: Employee to Venture
description: Which ventures an employee is staffed to, and in what capacity.
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
extends: []                 # interfaces may extend other interfaces, layering inherited properties
properties:
  lastInspectionDate:
    type: timestamp
    description: Most recent completed inspection.
    required: true
  inspectionStatus:
    type: string
    description: Outcome of the most recent inspection.
    constraints:
      enum: [passed, passedWithActions, failed, overdue]
    required: true
implementedBy: [asset, vessel, facility]
```

Define interface properties locally, as above, rather than reaching for shared properties by default — that is the recommended shape. Interfaces are abstract: no backing dataset, never instantiated directly.

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
    constraints:
      enum: [resolved, partiallyResolved, referredOnward]
  actualHours:
    type: double
    required: true
    constraints:
      range: {min: 0, max: 500}
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
validation:
  - The work order must be in inProgress before it can be closed.
```

One action, one business operation. An action modifying a single property whose name reads `Set X` is Action Sprawl; an action with no parameters requiring human input is probably pipeline or automation work. Both are in [anti-patterns.md](anti-patterns.md).

## Shared property

```yaml
apiName: lastInspectionDate
displayName: Last Inspection Date
type: timestamp
description: Most recent completed inspection, consistent across all inspectable types.
usedBy: [asset, vessel, facility]
```

## Value type

```yaml
apiName: workOrderStatusEnum
displayName: Work Order Status
baseType: string
description: Lifecycle states a work order may occupy.
constraints:
  enum:
    values: [draft, approved, inProgress, blocked, complete, cancelled]
    caseSensitive: true
```

Prefer a constraint over a prose rule — the schema enforces it rather than depending on every writer to remember.

## Mapping

The stage 3 artifact. One file per object type.

```yaml
objectType: workOrder
sources:
  - dataset: /Maintenance/clean/work_orders
    role: primary
    grain: One row per work order.
    primaryKey: wo_id -> workOrderId
    propertyMappings:
      wo_num: workOrderNumber
      raised_ts: raisedDate
      status_cd: workOrderStatus
    transformations:
      - Map status_cd through the code table to the workOrderStatus enum.
      - raised_ts is UTC in source; no conversion needed.
    excluded:
      - _ingested_at: ETL metadata, no business meaning.
      - row_hash: pipeline artifact.
      - src_system_id: internal identifier, no business meaning.
  - dataset: /Scheduling/clean/wo_estimates
    role: supplementary
    grain: One row per work order, present only once approved.
    joinOn: wo_id
    propertyMappings:
      est_hours: estimatedHours
precedence: >
  Where both sources carry a value, the maintenance system wins; scheduling is
  a planning overlay and lags by up to a day.
coverage: >
  ~3% of scheduling rows have no maintenance match. These are dropped; see
  DECISIONS.md.
logicPlacement:
  - value: openDurationDays
    mechanism: derived-property
    rationale: Depends on today's date, so it cannot be pre-computed in a batch.
  - value: assetOpenWorkOrderCount
    mechanism: derived-property
    rationale: Counts linked objects; storing it on the asset would go stale.
  - value: workOrderNumber normalization
    mechanism: pipeline-batch
    rationale: Stable input, same pipeline, zero runtime cost.
unmapped:
  - property: estimatedHours
    reason: No source until the scheduling feed lands. Populated by hand meanwhile.
```

`excluded` matters as much as `propertyMappings` — it records that a column was considered and rejected, which is what stops the Kitchen Sink creeping back on the next pass.

`mechanism` takes one of `action`, `pipeline-batch`, `pipeline-streaming`, `automation`, `function`, `schedule`, `derived-property`.

## DECISIONS.md

Append-only. One entry per decision a future reader would otherwise have to reverse-engineer:

```markdown
## Merged HrEmployee and BadgeEmployee into Employee

**Date:** 2026-08-23
**Principle:** Domain-driven design; System Silos anti-pattern.

Two types described one person. Joined on `nationalId` in a pipeline, with HR
authoritative for name and job title, badge authoritative for access dates.

**Tradeoff:** Badge records with no HR match are dropped — roughly 40
contractors. Revisit when the contractor feed is onboarded.
```

Record accepted compromises too, with the condition that should trigger revisiting each. An undocumented shortcut is indistinguishable from an error — and the audit will report it as one.
