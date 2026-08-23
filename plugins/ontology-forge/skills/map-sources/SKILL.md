---
name: map-sources
description: "Stage 03 of ontology design. Use when /map-sources, 'map source data', 'back these object types with datasets', or deciding whether logic belongs in an action, a pipeline, a function, or a derived property. Maps real datasets and columns onto an existing object model, records what was deliberately excluded, and places every piece of logic in the right layer."
metadata:
  disable-model-invocation: "true"
---

# Map source data and logic

Stage 03 of three. The model exists; now connect it to real data and decide where computation lives. The output is `ontology/mappings/`.

The direction matters: **source data is mapped onto the model, never the reverse.** When a source cannot fill a property, that is a finding about the data, not a reason to reshape the model.

Read [spec-format.md](../ontology-forge/references/spec-format.md) and [structural-guidance.md](../ontology-forge/references/structural-guidance.md) first.

## Start

Open a todolist with one entry per phase.

1. Inventory
2. Map
3. Exclude
4. Reconcile
5. Place logic
6. Write

## Phase 1: Inventory

Read the object types under `ontology/object-types/`. If there are none, run [design-ontology](../design-ontology/SKILL.md) first — mapping without a model produces a transcription of the source schema, which is the failure this whole workflow exists to prevent.

Then establish what data exists. Ask the user where the sources are, and read whatever they can point you at: DDL, dbt manifests, CSV headers, dataset schemas, sample rows, existing pipeline code. Search the repository before asking.

For each source, record its name, grain (one row per what?), and how fresh it is.

## Phase 2: Map

One mapping file per object type.

For each object type:

**Find the primary source.** The dataset whose grain matches the object type. If no single dataset does, the object type needs several sources joined — record how they join and which is authoritative.

**Map the primary key first.** No stable key means no object type. Say so rather than inventing a surrogate quietly.

**Map each property to a column.** Note any transformation needed: code tables to be resolved, units to be normalized, timestamps to be zoned, strings to be trimmed to a valid-value set.

**Record unmapped properties.** A property with no source is not a failure — it may be populated by an action, derived, or waiting on a feed that has not landed. Record which, so nobody assumes the data is there.

## Phase 3: Exclude

Go through every column in every source and decide explicitly: mapped, or excluded with a reason.

Exclude ETL metadata, internal system IDs, row hashes, debug timestamps, and anything failing *would someone need to see, search, or filter by this?*

Write the exclusions down. The `excluded` list is what stops the Kitchen Sink creeping back in the next time someone re-runs the mapping — without it, the next pass has no record that a column was considered and rejected.

## Phase 4: Reconcile

Where one object type draws on several sources, resolve the conflicts now:

- **Precedence.** When two sources disagree, which wins, and why? Write the reason, not just the rule.
- **Coverage.** Which records exist in one source but not another? What happens to them? Silently dropping rows is a decision that belongs in `DECISIONS.md`.
- **Keys.** Is the join key stable and unique in both? If not, the merge will produce duplicates or lose rows.

If the same entity arrives from several systems, that is a pipeline join upstream, not several object types. Several object types here is the System Silos anti-pattern — see [anti-patterns.md](../ontology-forge/references/anti-patterns.md).

## Phase 5: Place logic

For each computed value in the model, choose the mechanism deliberately. This is the Golden Hammer remedy:

| Job | Mechanism |
| --- | --------- |
| A human decides something and records it | Action type |
| Aggregation, pre-computation, heavy transformation | Pipeline (batch) |
| Continuous low-latency processing | Pipeline (streaming) |
| React to an event with no human involved | Automation |
| Complex real-time computation on demand | Function |
| Recurring builds | Schedule |

And for derived values specifically:

- Computable from stable inputs on the same object → pipeline transform.
- Depends on linked objects, or on values that actions change → derived property.

Never store a count that could be derived from links, and never store one fact on two object types. If scale forces denormalization, that is allowed — with the rationale and the scale threshold written into `DECISIONS.md`.

Record the mechanism and its rationale for every computed value.

## Phase 6: Write

Write one file per object type under `ontology/mappings/`, shaped as in [spec-format.md](../ontology-forge/references/spec-format.md), covering sources, property mappings, transformations, exclusions, precedence, logic placement, and unmapped properties.

Append to `ontology/DECISIONS.md` every reconciliation rule, dropped-record decision, and denormalization accepted under scale pressure.

## Finish

Report:

- Object types with no viable source.
- Properties left unmapped, and why.
- Records expected to be lost in reconciliation.
- Any place the data pushed back on the model — where the domain says one thing and the sources cannot support it. This is the most valuable output of the stage; do not bury it.

Do not quietly reshape the model to fit the data. Bring the conflict to the user and let them decide.
