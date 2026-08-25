---
name: write-contracts
description: "Stage 04 of ontology design. Use when /write-contracts, 'write the data contracts', 'ODCS contract', 'Open Data Contract Standard', 'contract for this dataset', or pinning down what an upstream source guarantees and what the ontology guarantees its consumers. Writes contracts strictly conforming to ODCS v3.1.0 and validates every one against the vendored JSON schema before reporting them written."
---

# Write data contracts

Stage 04. The model exists and its sources are mapped; now pin down the guarantees on both
sides. Output is `ontology/contracts/`, every file conforming to Open Data Contract Standard
**v3.1.0**.

Read [../ontology-forge/references/odcs.md](../ontology-forge/references/odcs.md) before writing
anything. It carries the field tables, the ontology-to-ODCS mapping, and — most usefully — which
constraints the schema enforces and which it silently lets through.

Two directions, never mixed in one file:

- **Inbound** (`contracts/inbound/`) — what an upstream dataset guarantees *you*. One per source
  dataset from stage 03.
- **Outbound** (`contracts/outbound/`) — what the ontology guarantees its *consumers*. One per
  object type others read.

## Start

Read `ontology/STATUS.md` first — the position, open questions, and thin-evidence decisions from
earlier stages, per [status-format.md](../ontology-forge/references/status-format.md).

Open a todolist with one entry per phase.

1. Direction
2. Ground
3. Draft
4. Guarantees
5. Validate
6. Write

## Phase 1: Direction

Establish which direction is being written and for what. If the user has not said, ask — **one
question, never a second question mark** ([interviewing.md](../ontology-forge/references/interviewing.md)).

The two directions are different work with different risks, so do not write both in one pass.
Finish one, checkpoint, then start the other.

## Phase 2: Ground

**For inbound contracts**, read `ontology/mappings/`. Stage 03 already recorded, per object type,
which datasets back it, their grain, their freshness, the transformations needed, and which
columns were deliberately excluded. That is most of a contract. Read the mapping before asking the
user anything — a question whose answer is already in `mappings/` spends their attention for
nothing.

**For outbound contracts**, read `ontology/object-types/`, `link-types/`, and `interfaces/`. The
object type *is* the schema; the mapping tells you the physical names underneath.

Read `DECISIONS.md` either way. A property that is deliberately denormalized, or a source that
deliberately loses records, is a contract term — not a detail to smooth over.

## Phase 3: Draft

One file per dataset (inbound) or per object type (outbound), named
`<name>.odcs.yaml`.

Fill the five required fields first: `apiVersion: v3.1.0`, `kind: DataContract`, a fresh UUID for
`id`, a SemVer `version`, and a `status` from the five legal values. Add `name` — the schema
allows omitting it, and a directory of UUID-only contracts is unreadable.

Then the schema section, using the mapping table in
[odcs.md](../ontology-forge/references/odcs.md): object type to a `schema[]` entry, property to a
`properties[]` entry, `logicalType` for the ODCS type with the source system's type in
`physicalType`, link type to a `relationships[]` entry.

Four rules while drafting:

**Describe everything.** Every `schema[]` entry and every property takes a `description`. None are
required by the schema and a contract of undescribed columns validates cleanly while being
worthless. Reuse the ontology's descriptions — they are already in business language, which is the
whole reason stage 01 wrote them.

**`required` is nullability, and it defaults to `false`.** Say it explicitly on every property.
Silence declares the whole dataset nullable, which is almost never what the source guarantees.

**Never invent a field name.** If the standard has no field for something, it goes in
`customProperties` with a camelCase `property` key. A plausible-looking invented field is exactly
what v3.1.0's strictness exists to reject.

**Say what a contract cannot express.** ODCS has no interface and no action type. Where a property
is populated by an action rather than by the source, or where its shape comes from an interface,
put that in the `description` — otherwise the contract reads as though the source provides it.

## Phase 4: Guarantees

The quality checks and SLAs are the part a contract is actually for. A schema listing is
documentation; a guarantee is a contract.

For each `schema[]` entry, write the checks that would catch the failures stage 03 was worried
about. Prefer `type: library` with a standard `metric` — it is portable. Reach for `type: sql`
only when no metric expresses the rule, and say in `description` what the query means.

Give every check a `dimension` and a `businessImpact`. A check nobody can connect to a
consequence gets silenced the first time it fires on a Sunday.

For SLAs, the ones that earn their place are `frequency` (how often it lands), `latency` (how
stale it may be), and `retention`. Take the values from the freshness stage 03 recorded.

**On an inbound contract, never invent a threshold.** It is a claim about someone else's system.
An unagreed contract asserting four-hour latency is worse than no contract, because it reads as
agreed. Where a value has not been negotiated, leave the field out and record it in `STATUS.md`
as an open question naming the team that owes the answer.

## Phase 5: Validate

Run the validator on everything written. This is not optional — it is the difference between
"written to ODCS" and "written in a style resembling ODCS":

```bash
scripts/validate_contract.py ontology/contracts
```

It checks against the vendored v3.1.0 schema, so it works offline and pins the version. Fix every
error and re-run until clean. Do not report a contract written while the validator disagrees.

Then check what the schema cannot, because a clean run does not mean a good contract:

- `status` is one of `proposed`, `draft`, `active`, `deprecated`, `retired`. The schema treats
  these as examples, so `status: live` passes and is wrong. Same trap for `slaProperties[].driver`.
- Every object and property has a real description, not a restated name.
- `required` is stated on every property rather than defaulted.
- Every quality check would actually catch something. `rowCount mustBeGreaterThan 0` passes
  validation and detects nothing.
- Nothing landed in `customProperties` that has a real ODCS field.

## Phase 6: Write

Files go to `ontology/contracts/inbound/` and `ontology/contracts/outbound/`.

Append to `ontology/DECISIONS.md` anything the contract settled that the model did not already
record: an agreed threshold, an accepted gap in an upstream guarantee, a property the contract
had to describe as action-populated.

## Finish

Update `ontology/STATUS.md` — see [status-format.md](../ontology-forge/references/status-format.md):

- Mark stage 04 `done` for the direction written, naming the contracts produced and the validator
  result.
- Every unnegotiated SLA or quality threshold goes under **Open questions**, naming the team that
  owes the answer. These are the contract's real gaps and they are invisible in a file that
  validates cleanly.
- Any guarantee taken from one person's recollection rather than an agreement goes under **Thin
  evidence**.
- Set **Next** to the other direction if one is outstanding, otherwise `/ontology-forge:audit-ontology`.

Then report: the contracts written, the validator result, and every guarantee still unagreed.

Hand back to [forge](../forge/SKILL.md) if it invoked this stage.

**A contract is a design specification, like the rest of the model.** Writing one does not
register it with any catalog, enforce anything, or run a single check. Say so plainly rather than
letting a validated file imply an enforced guarantee.

Contracts are files under `ontology/contracts/`. Do not publish them as an artifact or render
them as a page — a contract is reviewed in a diff, by the team on the other side of it.
