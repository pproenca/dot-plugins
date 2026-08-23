# Design principles

Four principles drawn from field experience across government and commercial implementations, in priority order. Where two conflict, the higher-priority one wins.

Distilled from [Ontology best practices](https://www.palantir.com/docs/foundry/ontology/ontology-best-practices/).

| Priority | Principle | Core idea |
| -------- | --------- | --------- |
| 1 | Domain-driven design | Model the real world, not the source data |
| 2 | Do not repeat yourself | If you built the same thing three times, refactor |
| 3 | Open for extension, closed for modification | Protect core models; enable builders to extend them |
| 4 | Composition over deep hierarchies | Favour multiple inheritance via interfaces; keep things pluggable |

---

## 1. Domain-driven design

**The ontology models the real world, not the source data.**

Objects represent semantically meaningful concepts — a `Patient`, a `WorkOrder`, a `Vessel` — not database tables, API responses, or spreadsheet tabs. Links represent real relationships ("this patient visited this facility"), not join keys or foreign-key artifacts.

When asked to "ontologize a dataset", resist mapping columns 1:1 and calling it done. A well-designed ontology feels intuitive: a person or an AI agent should navigate it without friction, because its structure matches how they already think about the domain.

**Warning signs.**
- Object types mirror source tables rather than domain entities.
- Properties map 1:1 from source columns without curation.
- Names follow source conventions (`dtLastInspMod`) rather than business language (`lastInspectionDate`).
- The model was designed by looking at data rather than understanding the domain.
- A single source row containing several entities is modelled as one object type.

**Example.** A CSV with `order_id`, `customer_name`, `customer_email`, `product_sku`, `quantity` describes at least three entities, not one. Modelling it as a single `OrderData` type loses two of them. The domain shape is `Order` (with `orderId`, `quantity`) linked to `Customer` (`name`, `email`) and `Product` (`sku`).

| Problem | Impact |
| ------- | ------ |
| Unintuitive model | People and agents cannot navigate it, because it does not match how they think |
| Fragile coupling to source | Source schema changes break ontology consumers |
| Missed relationships | Entities embedded as columns cannot be linked, searched, or reasoned about |
| Poor reuse | Types shaped by one system's schema are hard for other teams to adopt |

**In practice.**
- **Identify entities before looking at schemas.** Work with stakeholders on what concepts matter. One dataset often describes several.
- **Separate identity from observation.** If a row is a measurement or event *about* an entity, the entity and the observation are different object types.
- **Name things for humans.** Prefer `person.children` over `person.linkedChildPersonObjects`; `equipment.lastInspectionDate` over `equipment.dtLastInspMod`.
- **Model the domain, then map the data.** Understand, design, then map — never replicate the data's shape.
- **Mark non-semantic types hidden.** Technical types that serve a workflow rather than modelling the domain stay available to builders without cluttering default views.

---

## 2. Do not repeat yourself (rule of three)

**If you built the same thing three times, refactor.**

Duplicated types, redundant properties, and copy-pasted workflows are a maintenance burden and a context problem — for humans and for agents reasoning about the ontology. The goal is one canonical representation per concept and one canonical workflow per operation. One instance is coincidence, two is a pattern, three means refactor.

**Warning signs.**
- Several object types share the same property set and similar links.
- The same derived-property or action logic appears on several types.
- Different teams have built near-identical types for slightly different purposes.
- Copy-pasted workflows exist with minor variations.

**Example.** Sales, support, and finance each build a customer type with overlapping schemas. Either consolidate to one `Customer` carrying `salesStatus`, `supportTier`, and `billingAccountId`, or — if the shapes are genuinely distinct — define a `CustomerBase` interface holding `name`, `email`, `phone` and implement it from `SalesLead`, `SupportContact`, and `BillingAccount`.

| Problem | Impact |
| ------- | ------ |
| Maintenance burden | Every change replicated across duplicates; missed updates cause drift |
| Ambiguous context | Nobody can tell which near-identical type is canonical |
| Inconsistent behaviour | Duplicated logic diverges over time and produces conflicting results |
| Wasted effort | Teams rebuild the same thing instead of collaborating on one model |

**In practice.** Audit for duplicates and decide whether they are one type with a distinguishing property or several types sharing an interface. Extract repeated derived-property or action logic into an interface or shared function. Unify team-specific copies into one canonical type with appropriate security or filtering.

---

## 3. Open for extension, closed for modification

**Protect core models. Enable builders to extend them.**

Once a type, interface, or workflow is field-tested and in production, its core structure should be stable. Other teams should build on top of it — new types implementing an interface, new workflows consuming existing objects — without editing the core model.

**Warning signs.**
- Frequent breaking changes to established types cascading through dependent applications.
- New use cases requiring modification of core types rather than extension.
- Teams needing to edit shared interfaces or actions for team-specific needs.
- Security changes for one team's extension affecting other consumers.

**Example.** A core `Equipment` type and `Inspectable` interface are in production when a new team needs certification tracking. Adding `certificationAuthority`, `certificationExpiry`, `certificationStatus`, and `lastCertAudit` to `Equipment` leaves four properties null for all non-certified equipment and forces existing consumers to absorb the change. Instead, leave `Equipment` untouched and add a linked `EquipmentCertification` type plus a `Certifiable` interface.

| Problem | Impact |
| ------- | ------ |
| Breaking changes | Modifications to core types break dependent applications, actions, and workflows |
| Scope creep | Core types accumulate properties for every use case, trending toward a God Object |
| Entangled ownership | Several teams modify one type, creating conflicts and unclear accountability |
| Security leakage | Extending without clean boundaries can widen data access unintentionally |

**In practice.** Decide which properties and links are genuinely fundamental, and lock those down. Design core types anticipating that others will build on them. When adding, ask whether it belongs on the core type or on an extension — a linked type, a new interface implementation, a new property namespace. Keep security boundaries well defined so extension does not widen access.

---

## 4. Composition over deep hierarchies

**Favour multiple inheritance via interfaces. Keep things pluggable.**

The Ontology supports multiple inheritance through interfaces, so an entity can compose behaviour from several focused abstractions instead of sitting in a single-inheritance chain.

**Warning signs.**
- Deep single-inheritance chains whose middle types exist only to combine capabilities.
- Combination types like `SchedulableBuilding` or `InspectableVehicle` fusing unrelated concepts.
- Workflows coupled to specific object types when they could target a shared interface.
- Adding a capability requires restructuring the hierarchy.

**Example.** An `Arena` is both a building and a schedulable resource. The hierarchy `Asset → PhysicalAsset → Building → SchedulableBuilding → Arena` needs a new intermediate type for every capability combination — a schedulable warehouse would need another branch. Composing a `Building` interface (`address`, `squareFootage`) with a `SchedulableResource` interface (`schedulingCalendar`, `bookingPolicy`) and having `Arena` implement both means a schedulable warehouse just implements the same two.

| Problem | Impact |
| ------- | ------ |
| Combinatorial explosion | Every capability combination needs a new intermediate type |
| Brittle hierarchies | Parent changes cascade unpredictably through descendants |
| Limited reuse | Workflows bound to a deep type cannot serve others with the same capability |
| Semantic distortion | Contrived parents like `SchedulableBuilding` model nothing real, violating principle 1 |

**In practice.** Design interfaces around capabilities or roles — `Inspectable`, `Schedulable`, `Billable`, `Depreciable`. Use taxonomic interfaces such as `MilitaryAsset` (implemented by `Aircraft`, `Vessel`, `GroundVehicle`) for drilldown and aggregation. Target interfaces when building actions, functions, and applications. Compose rather than inherit.

---

## Working guidelines

A practical checklist, each grounded in a principle or anti-pattern:

| Guideline | Grounded in |
| --------- | ----------- |
| **Model reality, not systems.** Types represent real-world entities, not source-system or department representations. | Domain-driven design |
| **Curate intentionally.** Every property has clear business or technical value. | Normalization and derived properties |
| **Collaborate across teams.** Design involves stakeholders from several teams — silos are a leading cause of duplication. | Do not repeat yourself |
| **Keep object types focused.** One distinct entity per type. | Domain-driven design |
| **Choose the right tool.** Actions for human or agentic decisions; pipelines for automated transformation. | The Golden Hammer |
| **Use interfaces for abstraction.** Shared characteristics become interfaces, not wide sparse types. | Composition over deep hierarchies |
| **Document your decisions.** Record types, properties, and links. | — |

---

## Pragmatism and tradeoffs

**These principles are guides, not laws.** Deadlines, legacy systems, partial platform support, and team skill levels all mean the ideal design is not always reachable today.

| Guideline | Detail |
| --------- | ------ |
| Steer toward good design without being a roadblock | If something must ship under a tight deadline, build something reasonable now with a clear path to improvement |
| Name the tradeoffs explicitly | When recommending a shortcut, say what is traded away and when it will matter — denormalization may be fine now and want revisiting past 10k objects |
| Prefer incremental improvement over big-bang refactors | A slightly imperfect ontology in use and generating value beats a perfect one still being designed |
| Defend the critical invariants | Naming quality, semantic clarity, and security design are hard to fix later. Cut corners on implementation details, not on these |

> The Ontology is the software that powers your organization.

Treat it with the care of a production codebase — while still prioritising business value over perfection. Every accepted shortcut belongs in `DECISIONS.md` with the condition that should trigger revisiting it.
