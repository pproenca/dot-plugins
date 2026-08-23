# Structural guidance

How to shape the model once the entities are known. Source: [Ontology structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance/).

## Normalization and derived properties

**Store each fact once. Use derived properties for convenience.**

Two kinds of computed value, with different homes:

| Kind | Depends on | Where it belongs | Example |
| ---- | ---------- | ---------------- | ------- |
| Pre-computed | Stable inputs on the same object | Pipeline transform | `fullName` from `firstName` + `lastName` |
| Dynamically derived | Linked objects, or values changed by actions | Derived property | Count of linked employees |

Avoid: the same value stored on several object types; properties going stale because someone copies them by hand; one fact requiring writes to several objects; count properties maintained manually instead of computed from links.

**Scale caveat:** derived properties are cheap below roughly 10k objects. Above that, watch latency — selective denormalization can be justified, but write the rationale down in `DECISIONS.md`.

## Structs

Group semantically related fields into a struct instead of flattening them into separate properties.

Use a struct for:
- Multi-field values — address components, coordinates.
- Values carrying metadata — an LLM output with its confidence score and source.
- Multi-valued properties needing reducer logic to surface the most relevant value.

Structs keep a multi-field concept cohesive, allow provenance and confidence to travel with the value, and let you designate main fields for interface and query behaviour. This matters most for model outputs: capture value, confidence, model, and timestamp together rather than scattering them.

## Interfaces

Interfaces are the primary tool for reuse and extensibility.

Reach for one when:
- Several object types share common properties.
- A workflow should apply across types — scheduling logic for vehicles, equipment, and facilities alike.
- You need a taxonomic grouping — `MilitaryAsset` implemented by aircraft, vessels, and ground vehicles.
- You want multi-level abstraction — interfaces extending other interfaces.

If platform tooling does not yet support the workflow you want against an interface, still define the interface and duplicate the workflow per type as a temporary measure. That establishes the foundation for consolidation later.

## Links and object-backed link types

Links represent semantically meaningful relationships that answer a clear domain question.

| Scenario | Use |
| -------- | --- |
| Meaningful relationship with no metadata of its own | Direct link |
| The relationship itself carries data — dates, roles, status, allocation | Object-backed link |

Example: `Employee → VentureStaffing → Venture` puts role, `startDate`, and allocation on the joining object, where they belong, instead of ambiguously on the employee.

Avoid: links that exist only because two datasets share a foreign key; multi-valued properties standing in for a relationship; relationship metadata lost because the link is direct.

## Logic placement

The remedy for the Golden Hammer. Match the mechanism to the job:

| Job | Mechanism |
| --- | --------- |
| A human makes a decision and records it | Action type |
| Aggregation, pre-computation, heavy transformation | Pipeline (batch) |
| Continuous low-latency processing | Pipeline (streaming) |
| React to an event without a human | Automation |
| Complex real-time computation on demand | Function |
| Recurring builds | Schedule |

State the choice and its reason wherever logic is defined.

## Security design

Express security semantically, least privilege first.

- **Row-level** controls which objects a user sees.
- **Column-level** controls which properties they see on those objects.
- **Cell-level** is the intersection of the two.

Start restrictive and open up deliberately.

Avoid duplicating object types for security purposes — the schemas drift apart and the duplication becomes permanent. Avoid ad-hoc filtering in application code; the Ontology should enforce the policy so every consumer inherits it.

## Object type groups

Organize types into groups so large ontologies stay navigable, and mark non-semantic helper types as hidden to keep views clean.
