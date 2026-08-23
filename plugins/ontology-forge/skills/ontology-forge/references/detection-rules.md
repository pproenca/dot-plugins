# Detection rules

Mechanical checks the [audit-ontology](../../audit-ontology/SKILL.md) lanes run against the YAML under `ontology/`. Each rule turns an indicator from [anti-patterns.md](anti-patterns.md) or [structural-guidance.md](structural-guidance.md) into something computable.

**These rules find candidates, not verdicts.** Every threshold is a heuristic, and a model can violate one deliberately for a reason recorded in `DECISIONS.md`. A rule firing means *go read the file*; it never means *report a finding*. Confirm each hit against the actual definition before it reaches the report, and drop it if `DECISIONS.md` already accepts it.

## Duplication lane

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `DUP-1` | object types, pairwise | Jaccard similarity of property `apiName` sets | ≥ 0.6 | System or Department Silos |
| `DUP-2` | object type `apiName` / `displayName` | Contains a source-system token: `hr`, `sap`, `crm`, `salesforce`, `workday`, `oracle`, `legacy`, `system`, `source` | any | System Silos |
| `DUP-3` | object type `apiName` / `displayName` | Contains a department token: `sales`, `support`, `billing`, `finance`, `marketing`, `ops` | any | Department Silos |
| `DUP-4` | object types | Two or more types whose `primaryKey` property has the same name or obvious semantic (`employeeId`, `customerId`) | ≥ 2 | Same entity modelled twice |
| `DUP-5` | object types | Three or more types sharing ≥ 2 identically-named properties not covered by any interface or shared property | ≥ 3 types | Rule-of-three violation; wants an interface |

## Type-shape lane

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `SHAPE-1` | object type | Property count vs median across all object types | > 2× median | God Object |
| `SHAPE-2` | object type | Share of properties not marked `required: true` | > 60% | Sparse type — God Object |
| `SHAPE-3` | object type | Has a property named `type`, `category`, `kind`, `class`, or `subtype` with `validValues` length ≥ 4 | present | Discriminator switching property meaning |
| `SHAPE-4` | property `description` | Matches `depends on`, `varies by`, `depending on`, `only applies`, `when the type is` | any | Conditional semantics — God Object |
| `SHAPE-5` | property `apiName` | Matches `^_`, `_(at\|ts)$`, `^row_`, `hash`, `etl`, `ingest`, `batch`, `sequence`, `internal`, `debug`, `audit`, `_version$` | any | Kitchen Sink |
| `SHAPE-6` | property `apiName` | Is snake_case while sibling properties are camelCase | any | Uncurated source column |
| `SHAPE-7` | object type or property `apiName` / `displayName` | Matches `v\d+$`, `_v\d`, or a bare year `(19\|20)\d{2}` | any | Time Machine |
| `SHAPE-8` | object type | Has a property named `version`, `revision`, or `isCurrent` | any | Time Machine |
| `SHAPE-9` | property | No `description`, or description shorter than 20 characters | any | Undocumented element |

## Behaviour lane

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `ACT-1` | action types | Count grouped by `appliesTo` | > 10 per object type | Action Sprawl |
| `ACT-2` | action type | `apiName` matches `^(set\|update\|change\|edit)[A-Z]` **and** `modifies` has exactly one entry | both | Action Sprawl |
| `ACT-3` | action type | `parameters` is empty or absent | any | No human input — likely pipeline or automation work (Golden Hammer) |
| `ACT-4` | action type | `businessOperation` field missing | any | Action not tied to a real process |
| `ACT-5` | action type | `description` mentions `calculate`, `aggregate`, `recompute`, `batch`, `for all`, `every` | any | Batch work wearing an action's clothes |
| `ACT-6` | mappings | `logicPlacement` entry without a `rationale` | any | Unjustified mechanism choice |
| `ACT-7` | mappings | `logicPlacement` `mechanism` is not one of `action`, `pipeline-batch`, `pipeline-streaming`, `automation`, `function`, `schedule`, `derived-property` | any | Mechanism outside the placement table |

## Naming lane

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `NAME-1` | any `apiName` | Exact match against the blocklist in [naming.md](naming.md) | any | Misnomer |
| `NAME-2` | link `apiName` | Matches `related`, `link\d`, `assoc`, `ref\d`, `xref` | any | Misnomer |
| `NAME-3` | object type `apiName` | Plural form | any | Object types are singular |
| `NAME-4` | property `apiName` | Encodes type or system convention: `^(dt\|str\|num\|n\|b\|fld)[A-Z]`, or matches `field\d` | any | Misnomer |
| `NAME-5` | date properties across the ontology | More than one date-naming convention in use (`createdDate` alongside `dateOfCreation` or `created_ts`) | ≥ 2 conventions | Inconsistent naming |
| `NAME-6` | link type | `from.apiName` or `to.apiName` missing | any | Link not named from both directions |
| `NAME-7` | any element | `description` absent | any | Undocumented element |

## Structure lane

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `STRUCT-1` | properties across object types | Same `apiName` on ≥ 2 types, not declared in `shared-properties/` and not from an implemented interface | ≥ 2 | One fact stored twice |
| `STRUCT-2` | property | `apiName` matches `count$`, `total$`, `^num[A-Z]`, `sum$` and `derived` is not `true` | any | Manually maintained count that should derive from links |
| `STRUCT-3` | property | `apiName` mirrors a linked type's property (`customerName` on `Order` where `Order → Customer` exists) | any | Embedded entity that should be a link |
| `STRUCT-4` | link type | `backing: direct` while `description` mentions `role`, `date`, `status`, `allocation`, `percentage`, `capacity` | any | Wants an object-backed link |
| `STRUCT-5` | link type | `apiName` matches a property ending `Id` on either endpoint | any | Foreign key masquerading as a link |
| `STRUCT-6` | object types | Group of properties sharing a name prefix (`addressStreet`, `addressCity`, `addressPostalCode`) | ≥ 3 sharing a prefix | Should be a struct |
| `STRUCT-7` | interfaces | Declared in an object type's `implements` but no file in `interfaces/` | any | Dangling interface reference |
| `STRUCT-8` | object types | Two types with near-identical property sets where one name suggests a security variant (`Public*`, `Restricted*`, `*Sensitive`) | any | Types duplicated for security |
| `STRUCT-9` | derived property | `derived: true` with no `derivation` text | any | Underspecified computation |
| `STRUCT-10` | object type | No `primaryKey`, or `primaryKey` naming no declared property | any | Type cannot be instantiated |

## Referential-integrity lane

Every element that names another element must name one that exists. These are the
cheapest checks in the file and they catch the damage a half-finished migration leaves
behind — a real audit found ten of these in a 26-file model where every other rule was
already firing.

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `REF-1` | action type | A `modifies[].property` the `appliesTo` type does not declare | any | Action writes to a property that does not exist |
| `REF-2` | action type | `appliesTo` names no object type on disk | any | Action targets a missing type |
| `REF-3` | link type | `from.objectType` or `to.objectType` names no object type on disk | any | Link endpoint missing |
| `REF-4` | derived property | A `via` entry names no link type on disk | any | Traversal path is broken |
| `REF-5` | object type | An `implements` entry names no interface on disk | any | Dangling interface — same as `STRUCT-7` |
| `REF-6` | link type | `backing: object-backed` with a `through` naming no object type on disk | any | Joining type missing |
| `REF-7` | object type | `titleProperty` names no declared property | any | Title cannot render |

A dangling reference is a fact about the files, not a judgement, so these do not need the
usual "read it in context before reporting" caution — though they do still need the
*count* reported honestly, since one missing type can produce dozens of hits.

## Platform-constraint lane

These check the model against what the platform can actually express, per [platform-constraints.md](platform-constraints.md). A hit here is usually a specification error rather than a design smell.

| ID | Target | Check | Threshold | Suggests |
| -- | ------ | ----- | --------- | -------- |
| `PLAT-1` | property | `derived: true` together with `required: true` | any | Derived properties cannot be required |
| `PLAT-2` | property | `derived: true` together with a `constraints` block or a `valueType` | any | Derived properties cannot carry constraints |
| `PLAT-3` | object type | `primaryKey` names a property marked `derived: true` | any | Primary keys cannot be derived |
| `PLAT-4` | property | `derived: true` with a `via` path longer than 3 hops | > 3 | Exceeds the traversal limit |
| `PLAT-5` | property | `derived: true`, `via` crosses a "many" cardinality link, no `aggregation` | any | Aggregation is required on many-cardinality hops |
| `PLAT-6` | property | `reducers` on an array whose base type is Attachment, Cipher Text, Geohash, Geoshape, Geotemporal Series Reference, Marking, Media Reference, Time Dependent, or Vector | any | Reducers unsupported for this base type |
| `PLAT-7` | action type | Targets a property that is `derived` or reached through a reducer or struct main field | any | The action will error — no inverse exists |
| `PLAT-8` | link type | `from.objectType` and `to.objectType` are in different ontologies | any | Cross-ontology links are unsupported |
| `PLAT-9` | property | `derived: true` and the property is described as searchable or filterable | any | Derived properties cannot be text-searched |

## Reporting

Group hits by lane, then verify. In the report, cite the rule ID alongside the finding so the reader can see what triggered it and judge the threshold for themselves — `SHAPE-1` firing on a type with 40 properties against a median of 12 is a different conversation from one with 15 against 7.

Log any rule you could not run — because the model uses a different layout, or the relevant field is absent throughout — under **Not reviewed**. A rule that silently did not execute reads as a rule that passed.
