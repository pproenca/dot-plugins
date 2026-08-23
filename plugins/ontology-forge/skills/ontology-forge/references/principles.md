# Design principles

Four principles, in priority order. When two conflict, the higher one wins.

Source: [Ontology best practices](https://www.palantir.com/docs/foundry/ontology/ontology-best-practices/).

## 1. Domain-driven design

**Model the real world, not the source data.**

- Object types represent semantically meaningful concepts — `Patient`, `WorkOrder`, `Vessel` — not database tables.
- Links embody real relationships, not join keys.
- Names come from business language (`lastInspectionDate`), not system conventions (`dtLastInspMod`).
- Resist 1:1 column-to-property mapping. A source table is evidence about the domain, not a description of it.

The test: could a domain expert who has never seen the source systems read the object type and recognise their own work in it? If not, the model is describing a database.

## 2. Do not repeat yourself — the rule of three

**If you built the same thing three times, refactor.**

- One duplicate is coincidence. Two is a pattern. Three triggers refactoring.
- Deduplicate near-identical object types across teams into one shared type.
- Extract shared derived-property logic into interfaces or functions.

Applies to object types, property logic, and action types alike.

## 3. Open for extension, closed for modification

**Protect core models. Enable builders to extend them.**

- Established types stay stable. New requirements extend rather than modify core definitions.
- Team-specific needs become linked object types or new interface implementations.
- Avoid breaking changes to production types — they cascade across every application built on them.

This is the principle that governs [extend-ontology](../../extend-ontology/SKILL.md). Adding a property to a core type is a modification; adding a linked type that carries the new concept is an extension.

## 4. Composition over deep hierarchies

**Favour multiple inheritance via interfaces. Keep things pluggable.**

- Design focused interfaces around capabilities: `Inspectable`, `Schedulable`, `Billable`.
- Implement several interfaces on one type rather than building deep inheritance chains.
- Target interfaces, not concrete types, in workflows — that is what makes the workflow reusable.

The failure mode this prevents is the single-inheritance combinatorial: types like `SchedulableBuilding` that fuse unrelated concepts because the model has no interfaces.

## Seven working guidelines

1. **Model reality, not systems.** Real-world entities, not source-system representations.
2. **Curate intentionally.** Every property earns its place with clear business or technical value.
3. **Collaborate across teams.** Siloed teams produce duplicate entities. Involve every stakeholder who touches the concept.
4. **Keep object types focused.** One distinct entity per type.
5. **Choose the right tool.** Actions for human decisions; pipelines for automation. See the placement table in [structural-guidance.md](structural-guidance.md).
6. **Use interfaces for abstraction.** Shared characteristics become interfaces, never wide sparse types.
7. **Document your decisions.** Record why each object type, property, and link exists.

## Pragmatism

Deadlines are real. The guidance is not to refuse a reasonable compromise, but to name it:

- Build the reasonable solution, with a stated path to the better one.
- Name tradeoffs explicitly — "denormalising this works at today's scale and needs revisiting past 10k objects".
- Prefer incremental improvement to big-bang refactors.
- Defend the invariants that are expensive to fix later: naming quality, semantic clarity, security design.

> The Ontology is the software that powers your organization.

Every shortcut is a shortcut in production software, and should be recorded in `DECISIONS.md` as one.
