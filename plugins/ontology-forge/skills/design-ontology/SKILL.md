---
name: design-ontology
description: "Stage 02 of ontology design. Use when /design-ontology, 'design the ontology', 'model this domain', or turning a domain understanding into object types, properties, link types, interfaces and action types. Produces the ontology YAML specification with every element named in business language, checked against the anti-pattern catalog, and with the reasoning recorded in DECISIONS.md."
metadata:
  disable-model-invocation: "true"
---

# Design the ontology

Stage 02 of three. Turn the domain picture into a specified object model. The output is YAML under `ontology/` plus the decisions behind it.

Read [../ontology-forge/references/principles.md](../ontology-forge/references/principles.md), [naming.md](../ontology-forge/references/naming.md), [vocabulary.md](../ontology-forge/references/vocabulary.md), and [spec-format.md](../ontology-forge/references/spec-format.md) before starting.

## Start

Open a todolist with one entry per phase.

1. Ground
2. Types
3. Links
4. Interfaces
5. Actions
6. Screen
7. Write

## Phase 1: Ground

Read `ontology/DOMAIN-BRIEF.md` and `ontology/GLOSSARY.md` if stage 01 produced them.

If they do not exist, do not proceed on assumption. Either run [understand-domain](../understand-domain/SKILL.md), or — when the user has the domain clearly in their head and wants to move — spend a focused round establishing the entities, events, relationships, and workflows, and write the brief before designing. Ten minutes here prevents a model that has to be thrown away.

If an `ontology/` already exists with types in it, this is an extension, not a design. Switch to [extend-ontology](../extend-ontology/SKILL.md).

## Phase 2: Object types

One object type per distinct real-world entity or event.

For each, decide in this order:

**Name.** Singular concrete noun, from the glossary, in business language. Check it against the blocklist in [naming.md](../ontology-forge/references/naming.md).

**Primary key.** What makes one instance distinguishable. If no stable key exists in the domain, say so — that is a real finding, not a detail to paper over with a surrogate.

**Title property.** What a human sees in a search result.

**Properties.** Every one earns its place. For each, ask: *would someone need to see, search, or filter by this?* If the answer is no, it stays in the backing dataset. Prefer too few now — properties are cheap to add and expensive to remove once applications read them.

**Description.** What it means, and for constrained values, what the valid values are.

Three shaping rules while you work:

- **Separate identity from observation.** Entities hold what they are; measurements and events go in their own types.
- **Never embed another entity.** `order.customerName` is a link waiting to be modelled. Use the link.
- **Group related fields into a struct** rather than flattening — address components, coordinates, a model output with its confidence. See [structural-guidance.md](../ontology-forge/references/structural-guidance.md).
- **Check what the platform can express** before committing a property to `derived`, a reducer, or an interface-targeting workflow. A derived property cannot be required, constrained, or a primary key. [platform-constraints.md](../ontology-forge/references/platform-constraints.md) has the limits.

## Phase 3: Links

Every relationship from the brief becomes a link type, named so it reads as English from both sides.

For each: name both directions, set cardinality, then ask whether the relationship carries data of its own — a role, a date range, an allocation, a status. If it does, it needs an object-backed link, and that joining object gets a domain name (`VentureStaffing`, not `EmployeeVentureJoin`).

A link that exists only because two datasets share a foreign key is not a link. Delete it.

## Phase 4: Interfaces

Look across the types for shared shape.

Two triggers:
- **Capability** — several types participate in the same workflow. `Inspectable`, `Schedulable`, `Billable`.
- **Taxonomy** — several types are kinds of one broader thing that workflows aggregate over. `MilitaryAsset` over aircraft, vessels, ground vehicles.

Design the interface around the capability, keep it focused, and let a type implement several. Never widen one type to absorb another's properties — that is the God Object, and interfaces exist precisely to avoid it.

Where a shared property is genuinely the same fact across types, define it once as a shared property.

## Phase 5: Action types

One action per business operation — a thing a person decides and records, named after that decision.

Bundle every property change that operation implies into the one action. Use optional parameters for fields that vary. Record side effects.

Before writing any action, check the placement table in [structural-guidance.md](../ontology-forge/references/structural-guidance.md). If no human is deciding anything, it is not an action: it is a pipeline, an automation, or a function. Write down which, and why.

Stop and reconsider if an action name reads `Set X` or `Update X`, or if one object type is accumulating more than about ten actions.

## Phase 6: Screen

Screen the whole model against [anti-patterns.md](../ontology-forge/references/anti-patterns.md) before writing files. Walk all eight — System Silos, Kitchen Sink, Department Silos, God Object, Golden Hammer, Action Sprawl, Time Machine, Misnomer — and fix what you find.

Then check the model answers the questions:

- Walk each workflow from the brief through the types and links. Any dead end is a missing link.
- For each type, ask whether a domain expert would recognise their own work in it.
- Check no fact is stored in two places.

## Phase 7: Write

Write the YAML in the shapes given in [spec-format.md](../ontology-forge/references/spec-format.md): `object-types/`, `link-types/`, `interfaces/`, `action-types/`, `shared-properties/`.

Then write `ontology/DECISIONS.md`. One entry per decision a future reader would otherwise have to reverse-engineer — merges, splits, what became an interface and why, every accepted shortcut with the condition that should trigger revisiting it.

## Finish

Report what was created, then say plainly:

- Which parts of the domain brief are not yet modelled.
- Which decisions were made on thin evidence and want a stakeholder's confirmation.
- That this is a design specification, and Ontology Manager remains the system of record.

Offer stage 03: `/ontology-forge:map-sources`.
