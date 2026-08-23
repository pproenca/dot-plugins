# Answer key — poisoned fixture

Every defect below was planted deliberately. This is the scoring sheet for `audit-ontology`:
**recall = distinct planted defects found ÷ 24**.

Do not show this file to the model under test. It lives outside `ontology/` so a
skill reading the model does not pick it up.

## Anti-patterns planted (all eight)

| # | Anti-pattern | Where | Expected rules |
| - | ------------ | ----- | -------------- |
| 1 | System Silos | `hrSystemEmployee` + `badgeSystemEmployee` — one person, two source systems | `DUP-1`, `DUP-2`, `DUP-4` |
| 2 | Department Silos | `salesCustomer` + `supportCustomer` — one customer, two departments | `DUP-1`, `DUP-3`, `DUP-4` |
| 3 | Kitchen Sink | `salesCustomer`: `_crm_extracted_at`, `row_hash`, `last_etl_update_timestamp`, `_crm_internal_record_id` | `SHAPE-5`, `SHAPE-6` |
| 4 | God Object | `asset` — 30 properties, 29 optional, `assetType` discriminator with 5 values, three descriptions saying meaning "varies by assetType" | `SHAPE-1`, `SHAPE-2`, `SHAPE-3`, `SHAPE-4` |
| 5 | Golden Hammer | `calculateRegionalSalesTotals` — batch aggregation as an action, no parameters, no human decision | `ACT-3`, `ACT-5` |
| 6 | Action Sprawl | 12 `set*` actions on `hrSystemEmployee`, each modifying one property | `ACT-1`, `ACT-2`, `ACT-4` |
| 7 | Time Machine | `contractV2`, `contract2024`, plus `version` / `isCurrent` / `revision` properties | `SHAPE-7`, `SHAPE-8` |
| 8 | Misnomer | `items` (plural type name) with `value`, `type`, `date`, `name`, `id`, `dtLastInspMod`, `fieldX`, and no descriptions anywhere | `NAME-1`, `NAME-3`, `NAME-4`, `NAME-7`, `SHAPE-9` |

## Structural defects planted

| # | Defect | Where | Expected rule |
| - | ------ | ----- | ------------- |
| 9 | Copied fact | `hrSystemEmployee.managerName` duplicates the linked manager's name | `STRUCT-3` |
| 10 | Manual count | `hrSystemEmployee.directReportCount` not marked derived | `STRUCT-2` |
| 11 | Manual count | `facility.openWorkOrderCount` not marked derived | `STRUCT-2` |
| 12 | Metadata on a direct link | `employeeVenture` is `backing: direct` but its description names role, start date and allocation | `STRUCT-4` |
| 13 | Generic link name | `relatedItems` | `NAME-2` |
| 14 | Unnamed link side | `relatedItems.to` has no `apiName` | `NAME-6` |
| 15 | Should be a struct | `facility` — five `address*` properties sharing a prefix | `STRUCT-6` |
| 16 | Dangling interfaces | `facility` implements `inspectable` and `schedulable`; neither is defined | `STRUCT-7` |
| 17 | Types duplicated for security | `publicPatient` + `restrictedPatient` | `STRUCT-8` |
| 18 | Fact stored twice | `email` on both `salesCustomer` and `supportCustomer`, no shared property | `STRUCT-1` |

## Platform violations planted

| # | Violation | Where | Expected rule |
| -- | --------- | ----- | ------------- |
| 19 | Derived + required | `facility.inspectionScore` | `PLAT-1` |
| 20 | Derived + constraints | `facility.inspectionScore` has a `range` | `PLAT-2` |
| 21 | Derived primary key | `facility.primaryKey` is `derivedFacilityKey`, marked derived | `PLAT-3` |
| 22 | Traversal too deep | `facility.inspectionScore.via` is 4 hops | `PLAT-4` |
| 23 | Derived, described as searchable | `facility.inspectionScore` description says "searchable and filterable" | `PLAT-9` |
| 24 | Missing aggregation | `facility.inspectionScore` has no `aggregation`. **Not independently scoreable:** every link in its `via` chain is undefined, so cardinality is unknowable from the files. An auditor that reports this as *unevaluable* is more correct than one that asserts it | `PLAT-5` (expect "not reviewed") |

## Referential integrity (defects 25-27)

These were **not planted deliberately** — they are artifacts of how the fixture was
generated, discovered by an audit run on 2026-08-23 and confirmed against the files.
They are kept because they are realistic: a handed-over ontology mid-migration looks
exactly like this. They are now part of the expected findings.

| # | Defect | Where | Expected rule |
| -- | ------ | ----- | ------------- |
| 25 | 10 of 12 `set*` actions modify properties `hrSystemEmployee` never declares — it holds `fullName`, not `firstName`/`lastName`, and has no `phone`, `department`, `manager`, `location`, `startDate`, `grade`, `costCentre` or `badgeNumber` | `action-types/set*.yaml` | `REF-1` |
| 26 | `employeeVenture.to` names a `venture` object type that does not exist | `link-types/employeeVenture.yaml` | `REF-3` |
| 27 | All five link types in `facility`'s two `via` chains are undefined | `object-types/facility.yaml` | `REF-4` |

## Also true, though not planted

Findable and correct; credit but do not require:

- **Four date-naming conventions** coexist: `badgeIssuedDate`, `dateOfBirth`, bare `date`, `dtLastInspMod` (`NAME-5`).
- **Opaque title properties**: `asset.titleProperty` is `assetId`; both contract types use `contractId`. An identifier as the human-facing title.

## Scoring

- **Pass:** ≥ 20 of 24 found, with all eight anti-patterns represented.
- **Severity sanity:** the God Object, System Silos, and security-duplicated types must land in **Critical**; misnomers and missing descriptions in **Minor**.
- **No fabrication:** a finding is a false positive only if it is **not true of the files**. Do not score precision by absence from this list — this key has already been wrong once. Verify the claim against the fixture first; if it holds, it is a correct finding and this key is what needs updating. More than two claims that are demonstrably false of the files is a fail.
