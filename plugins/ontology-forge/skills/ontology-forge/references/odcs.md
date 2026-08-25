# Open Data Contract Standard v3.1.0

**Pinned version: v3.1.0. Checked against the standard on 2026-08-25.** This file ages the way
[platform-constraints.md](platform-constraints.md) does. The vendored schema at
`vendor/odcs/odcs-json-schema-v3.1.0.json` is the authority; where this file and the schema
disagree, the schema wins and this file is wrong.

Every contract sets `apiVersion: v3.1.0` and `kind: DataContract`. Never write a contract that
claims a version the vendored schema cannot check.

## What makes v3.1.0 strict

The root sets `additionalProperties: false` and subschemas set `unevaluatedProperties: false`
throughout. A field the standard does not define is a hard error, not a tolerated extension.
There is exactly one legal place for anything outside the standard:

```yaml
customProperties:
  - property: foundryObjectType     # camelCase
    value: workOrder
```

Run `scripts/validate_contract.py` on every contract before reporting it written. Guessing at a
field name that reads plausibly is the failure mode this standard is built to prevent.

## Required fields

Five, and only five, at the top level:

| Field | Value |
| ----- | ----- |
| `apiVersion` | `v3.1.0` |
| `kind` | `DataContract` |
| `id` | A UUID. Stable for the life of the contract — it is what survives renames. |
| `version` | SemVer for *this contract*, not the data. Breaking schema change is a major bump. |
| `status` | `proposed`, `draft`, `active`, `deprecated`, or `retired`. |

`name` is optional in the schema. Always write one anyway — a contract identified only by UUID is
unreadable in a directory listing.

## What the schema catches, and what it cannot

This distinction decides how much care each field needs. The schema is a strong check, not a
complete one.

**Mechanically enforced** — the validator fails the file:

- The five required fields, and `apiVersion` / `kind` against their enums.
- Any undefined field, anywhere (`additionalProperties` / `unevaluatedProperties`).
- `logicalType` ∈ `string, date, timestamp, time, number, integer, object, array, boolean`.
- `quality[].type` ∈ `text, library, sql, custom`; `quality[].dimension` ∈ `accuracy,
  completeness, conformity, consistency, coverage, timeliness, uniqueness`;
  `quality[].metric` ∈ `nullValues, missingValues, invalidValues, duplicateValues, rowCount`.
- `authoritativeDefinitions[].type` ∈ `businessDefinition, transformationImplementation,
  videoTutorial, tutorial, implementation`.
- `support[].tool` ∈ `email, slack, teams, discord, ticket, googlechat, other`;
  `support[].scope` ∈ `interactive, announcements, issues, notifications`.
- `servers[].type` against the platform list, with per-type required fields (Snowflake needs
  `account`, `database`, `schema`; Postgres needs `host`, `port`, `database`).
- `id` fields against the StableId pattern, and relationship targets against the reference
  patterns.

**Not enforced — yours to get right:**

- **`status`.** The five values are `examples` in the schema, not an `enum`. `status: live`
  validates and is wrong. Use the five.
- **`slaProperties[].driver`.** Same trap: `regulatory`, `analytics`, `operational` are examples,
  not an enum.
- **Whether descriptions are true.** Every object and property takes a `description`, none are
  required, and a contract of undescribed columns passes validation while being worthless.
- **Whether `required` means what you think.** It is nullability, and it defaults to `false`.
  Silence declares every column nullable.
- **Whether the quality checks would actually catch anything.** `rowCount mustBeGreaterThan 0`
  validates and detects nothing.

## Structure

```yaml
apiVersion: v3.1.0
kind: DataContract
id: 3f2a91c4-7b8e-4d21-9c33-1a5e6f0b7d42
name: crm_customer_export
version: 1.0.0
status: active
domain: sales
tenant: AcmeCorp

description:
  purpose: What this data is for.
  limitations: Where it must not be used, and why.
  usage: How consumers are expected to read it.

servers:
  - server: crm-warehouse
    type: snowflake
    account: acme-eu
    database: RAW
    schema: CRM

schema:
  - name: crm_customer                 # required
    physicalName: CRM_CUSTOMER_V2
    physicalType: table
    logicalType: object
    businessName: Customer
    description: One row per customer known to the CRM.
    dataGranularityDescription: One row per customer_id. No history.
    properties:
      - name: customer_id
        physicalName: CUSTOMER_ID
        logicalType: string
        physicalType: VARCHAR(36)
        required: true
        unique: true
        primaryKey: true
        primaryKeyPosition: 1
        classification: internal
        description: Stable CRM identifier for the customer.
        examples: ["8f14e45f-ceea-467a-9e6c-6b1f2a3d4c5b"]
      - name: signup_date
        logicalType: date
        physicalType: DATE
        logicalTypeOptions:
          format: yyyy-MM-dd
        required: true
        description: Date the customer account was opened.
    quality:
      - type: library
        metric: rowCount
        mustBeGreaterThan: 10000
        dimension: completeness
        severity: error
        businessImpact: operational
        description: A collapse below this means the extract truncated.
    relationships:
      - type: foreignKey
        from: [crm_customer.region_code]
        to: [reference_region.code]

slaProperties:
  - property: frequency
    value: 1
    unit: d
    element: crm_customer.signup_date
    driver: operational
  - property: latency
    value: 4
    unit: h
    element: crm_customer.signup_date

team:
  name: crm-platform
  members:
    - username: a.silva
      role: Owner
      dateIn: "2026-01-12"

support:
  - channel: "#crm-data"
    tool: slack
    scope: issues

customProperties:
  - property: backsObjectTypes
    value: [customer]
```

Ordering is free. Group the fundamentals first — a reader scanning a directory of contracts
should see `name`, `version`, and `status` without scrolling.

## Quality checks

Four `type` values, and the choice is not cosmetic:

| `type` | Use for | Required with it |
| ------ | ------- | ---------------- |
| `library` | The five standard metrics — the portable option, runs anywhere | `metric` |
| `sql` | A check the metrics cannot express | `query` |
| `custom` | An engine-specific check | `engine`, `implementation` |
| `text` | A rule stated for humans, with nothing executing it | — |

Prefer `library`. Reach for `sql` only when no metric fits, and say in `description` what the
query means — a reader should not have to parse SQL to learn the rule.

Operators: `mustBe`, `mustNotBe`, `mustBeGreaterThan`, `mustBeGreaterOrEqualTo`, `mustBeLessThan`,
`mustBeLessOrEqualTo`, `mustBeBetween`, `mustNotBeBetween`.

Every check carries `dimension` and `businessImpact`. A check nobody can connect to a consequence
gets silenced the first time it fires on a Sunday.

## Ontology elements to ODCS

The two models line up. Hold the mapping steady so a reader can move between them:

| Ontology element | ODCS |
| ---------------- | ---- |
| Object type | One `schema[]` entry, `logicalType: object` |
| `apiName` | `schema[].name` |
| `displayName` | `schema[].businessName` |
| Backing dataset or table | `schema[].physicalName` plus `servers[]` |
| Property | `schema[].properties[]` entry |
| Property `type` | `logicalType`, with the source column type in `physicalType` |
| Property required | `required: true` |
| Primary key | `primaryKey: true` with `primaryKeyPosition` from 1 |
| Value constraints | `logicalTypeOptions` — `pattern`, `minimum`, `maxLength`, `format` |
| Link type | `relationships[]`, `type: foreignKey` |
| Object-backed link | Its own `schema[]` entry, with a relationship each way |
| Interface | No ODCS equivalent. Record it in `customProperties`, and repeat the shared properties on each implementing entry. |
| Action type | No equivalent. Contracts describe data at rest, not operations. |
| Security marking | `classification` on the property |
| Mapping exclusions | Not represented — they stay in `ontology/mappings/` |

Two of these deserve care. **An interface does not survive the crossing** — ODCS has no shared
shape, so the properties get repeated per contract, and `customProperties` is the only record
that they came from one interface. **Actions have no home at all**; a contract cannot express
that a human writes a value, so an action-populated property looks source-populated unless the
description says otherwise. Say so.

## Inbound and outbound

Two directions, never mixed in one file. They have different owners, different servers, and
opposite consequences when broken.

| | Inbound | Outbound |
| --- | --- | --- |
| Describes | An upstream dataset backing object types | An object type as a product for consumers |
| Written with | The producing team | Your team |
| `servers` | The upstream system | Where the ontology-backed data is served |
| `team` | The producer's owner | Your owner |
| A breach means | Your model is fed bad data | You broke your consumers |
| Lives in | `ontology/contracts/inbound/` | `ontology/contracts/outbound/` |

An inbound contract is a claim about someone else's system. Never invent its SLAs or quality
thresholds — an unagreed contract asserting a four-hour latency is worse than no contract,
because it reads as agreed. Where a value is not yet negotiated, leave the field out and record
the gap in `STATUS.md` under open questions.

## Sources

- [Open Data Contract Standard](https://bitol-io.github.io/open-data-contract-standard/latest/) — the specification.
- [odcs-json-schema-v3.1.0.json](https://github.com/bitol-io/open-data-contract-standard/blob/main/schema/odcs-json-schema-v3.1.0.json) — vendored under `vendor/odcs/`.

ODCS is a Bitol project under the Linux Foundation AI & Data, licensed Apache 2.0. This plugin is
an independent work and is not affiliated with or endorsed by Bitol.
