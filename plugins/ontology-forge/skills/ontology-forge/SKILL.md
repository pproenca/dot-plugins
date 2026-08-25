---
name: ontology-forge
description: "Use whenever work touches an ontology, object model, or domain model — designing object types, properties, links, interfaces or action types; naming entities; deciding what becomes an object versus a property versus a link; or mapping source datasets onto a model. Also use for Palantir Foundry ontology questions and for judging whether a model is well shaped. Carries the design principles, structural guidance, naming conventions and anti-pattern catalog, and routes to the stage skills."
---

# Ontology Forge

Ontology design runs in four stages, in order:

**01 Understand the domain** → **02 Design the ontology** → **03 Map source data and logic** →
**04 Write the data contracts**

The order is the point. A model designed from source schemas describes a database; a model designed from the domain describes the organization and survives the next system migration.

## Route

Invoke the skill with the Skill tool. Do not answer from this file what a stage skill exists to
do — this one carries the principles, the stages carry the method.

| The user wants | Skill |
| -------------- | ----- |
| To be taken through the workflow, or does not know what comes next | [forge](../forge/SKILL.md) — `ontology-forge:forge` |
| To start from nothing, or to pin down what the domain actually is | [understand-domain](../understand-domain/SKILL.md) — `ontology-forge:understand-domain` |
| To turn a domain understanding into object types, links, interfaces, actions | [design-ontology](../design-ontology/SKILL.md) — `ontology-forge:design-ontology` |
| To connect real datasets to an existing model and decide where logic lives | [map-sources](../map-sources/SKILL.md) — `ontology-forge:map-sources` |
| To pin down what a source guarantees, or what the model guarantees consumers | [write-contracts](../write-contracts/SKILL.md) — `ontology-forge:write-contracts` |
| To add a new requirement to an ontology that already exists | [extend-ontology](../extend-ontology/SKILL.md) — `ontology-forge:extend-ontology` |
| To review a model for anti-patterns and structural problems | [audit-ontology](../audit-ontology/SKILL.md) — `ontology-forge:audit-ontology` |

**When the request spans stages, or the position is unclear, route to `forge`.** It reads
`ontology/STATUS.md`, reports where the work stands, and runs the stages in order with a
checkpoint at each boundary. Routing straight to a single stage is right only when the user
named the work precisely — "audit this", "add returns to the model".

Never run the stages out of order to reach the one that produces files fastest. A design
written before the domain is understood is the failure this workflow exists to prevent.

## The four principles

In priority order. When two conflict, the higher one wins. Full text in [references/principles.md](references/principles.md).

1. **Domain-driven design.** Model the real world, not the source data.
2. **Do not repeat yourself.** Built it three times? Refactor.
3. **Open for extension, closed for modification.** Protect core types; extend around them.
4. **Composition over deep hierarchies.** Focused interfaces, implemented several at a time.

## Load before advising

Read the reference that covers the question rather than answering from memory. These are short and specific:

- [references/interviewing.md](references/interviewing.md) — the one-question rule, how to sequence questions, and when to stop asking. Load before any stage that talks to the user.
- [references/principles.md](references/principles.md) — the four principles, seven working guidelines, and how to take a shortcut honestly.
- [references/anti-patterns.md](references/anti-patterns.md) — eight named failure modes with recognition signals and fixes.
- [references/structural-guidance.md](references/structural-guidance.md) — normalization and derived properties, structs, interfaces, object-backed links, logic placement, security.
- [references/naming.md](references/naming.md) — the naming table, the generic-name blocklist.
- [references/spec-format.md](references/spec-format.md) — the on-disk YAML shape for every element.
- [references/vocabulary.md](references/vocabulary.md) — Foundry's own element terms, the schema/instance split, and the value type constraint vocabulary.
- [references/detection-rules.md](references/detection-rules.md) — the anti-pattern indicators as mechanical checks, for auditing.
- [references/platform-constraints.md](references/platform-constraints.md) — what the platform can and cannot express today: derived-property and reducer limits, interface support levels, link mechanics. Check before committing a design to a capability.
- [references/odcs.md](references/odcs.md) — Open Data Contract Standard v3.1.0: the required fields, which constraints the schema enforces and which it silently lets through, and the ontology-element-to-ODCS mapping. Load before writing or reviewing any data contract.
- [references/status-format.md](references/status-format.md) — the shape of `ontology/STATUS.md`, the file that carries position, open questions, and thin-evidence decisions between stages and between sessions.

## Non-negotiables

**These files are a design specification, not deployable configuration.** Ontology Manager is the system of record. Never imply that writing YAML here changes a live ontology.

**Everything this workflow produces is a file under the model directory.** The brief, the glossary, the YAML, `DECISIONS.md`, `STATUS.md`, `AUDIT.md`. Never publish any of it as an artifact and never render it as a web page — not the audit report, not a model summary, not a diagram of the types, however much the content reads like a finished deliverable. The user reviews this work in a diff, in their repository, against the model it describes. A published copy is a second source of truth that goes stale on the next commit and cannot be code-reviewed. Diagram the model inline in the response if it helps the explanation.

**Every session leaves `ontology/STATUS.md` current.** Position, open questions, thin-evidence decisions. A stage that ends without updating it has dropped everything it could not resolve. See [references/status-format.md](references/status-format.md).

**Every element carries a description.** An object type, property, link, or action without one is unfinished.

**Every tradeoff goes in `DECISIONS.md`.** An accepted compromise that is written down is engineering; the same compromise undocumented is indistinguishable from a mistake.

**Name things in business language.** If reading a name requires knowing which team owns which upstream system, the name is wrong.

**One question per message.** Any stage that interviews the user asks one thing at a time and never emits a second question mark. Batched questions return one answer and a set of silences that become assumptions. See [references/interviewing.md](references/interviewing.md).

## Quick judgments

These come up constantly. Answer them the same way every time:

**Object type or property?** If it has its own identity, lifecycle, or things that link to it, it is an object type. If it only ever describes something else, it is a property.

**Property or link?** If the value is another entity, it is a link. `order.customerName` is embedded data; `order.customer → Customer` is the model.

**Link or object-backed link?** If the relationship itself carries data — a role, a date range, an allocation — it needs an object behind it.

**New type or interface?** Distinct entities that share characteristics get an interface. Never widen one type to cover both; that is how a God Object starts.

**Action or pipeline?** A human making a decision is an action. Everything else is a pipeline, an automation, or a function. See the placement table in [references/structural-guidance.md](references/structural-guidance.md).
