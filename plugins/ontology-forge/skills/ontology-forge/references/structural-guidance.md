# Structural guidance

How to structure properties, relationships, and access control once the entities are known.

Distilled from [Ontology structural guidance](https://www.palantir.com/docs/foundry/ontology/ontology-structural-guidance/).

---

## Normalization and derived properties

**Store each fact once. Use derived properties for convenience.**

Copying values from linked objects onto a parent is risky: when the source changes, every copy must be updated. Normalization keeps data consistent; derived properties give the convenience of denormalized access without the upkeep.

Not all computed values are alike. What matters is whether a value can be safely pre-computed from stable inputs, or must stay in sync with dynamic change.

| Type | Characteristics | Tool | Example |
| ---- | --------------- | ---- | ------- |
| Pre-computed | Computed from properties on the same object; inputs rarely change, or change only through pipeline ingestion | Pipeline transform | `fullName = firstName + " " + lastName` — inputs are stable and updated in the same pipeline, so there is zero runtime overhead |
| Dynamically derived | Depends on linked objects, or on values changed by actions, automations, or other ontology-level operations | Derived property | `directReportCount` — employees are reassigned, onboarded, and offboarded through actions, and a derived count stays correct automatically |

When a value depends on changes made through actions, *every* action that could affect it must also update it. If any one fails to, the value stays wrong until somebody notices.

**Warning signs.**
- The same value stored as a property on several object types.
- Properties going stale because they are copies of values maintained elsewhere.
- Updating one real-world fact requiring writes to several objects.
- Count properties maintained by hand rather than computed from links.

**Example.** A `Manager` needs a count of direct reports. Storing `directReportCount: 5` as a manually maintained integer means updating it every time somebody joins or leaves. A derived property counting linked `Employee` objects at query time cannot drift. Likewise `Employee.managerName` copied from the linked manager breaks the moment that manager's name changes — the link already carries the answer.

**Performance.** Derived properties are evaluated at runtime:

| Scale | Recommendation |
| ----- | -------------- |
| Low to moderate (< ~10k objects per query) | Use derived properties freely; runtime evaluation is fast enough for most workflows |
| High (> ~10k objects per query) | Derived properties may add latency through higher-overhead query paths. Denormalization can be an appropriate tradeoff, but as a conscious, documented decision — never the default |

**Deriving is not always available.** A derived property cannot be required, cannot carry constraints, cannot be a primary key, and cannot be text-searched — and it traverses at most three link hops. When a fact must be mandatory, validated, searchable, or written by an action, it has to be stored, and the upkeep is the price. The full limitation list is in [platform-constraints.md](platform-constraints.md); check it before committing a property to `derived: true`.

**In practice.** Store each fact where it semantically belongs. Derive or aggregate from links at query time. Watch latency as scale grows. Document any denormalization with its rationale, its source of truth, and the strategy for keeping copies in sync.

---

## Structs

**Group semantically related fields into structs.**

When a property is naturally multi-field — an address with street, city, state, postal code — use a struct rather than flattening into separate properties. Structs preserve the semantic grouping and let richer metadata travel with the value.

| Scenario | Example |
| -------- | ------- |
| Multi-field values | Address (street, city, state, postal code); coordinates (geopoint, altitude) |
| Values with metadata | AI-generated outputs with confidence scores, source references, reasoning |
| Multi-valued properties with selection logic | Several phone numbers where a reducer surfaces the primary one |

**Example.** A `Facility` address flattened into `addressStreet`, `addressCity`, `addressState`, `addressPostalCode`, `addressCountry`, `addressGeopoint`, `addressLastOccupied`, `addressDatasource`, `addressLlmConfidence`, `addressLlmReasoning` is ten properties whose only connection is a naming convention. As a struct array it is one concept: `street`, `city`, `state`, `postalCode`, `country` as main fields, plus `geopoint`, `lastOccupied` for reducer sorting, `datasource`, `llmConfidence`, `llmReasoning`.

| Benefit | Detail |
| ------- | ------ |
| Semantic grouping | An address is one concept, not ten unrelated properties, and the model says so |
| Metadata capture | Source, confidence, and timestamps travel alongside the primary value |
| Reducer support | Reducers surface the most relevant value — the address with the most recent `lastOccupied` |
| Main field behaviour | A struct can designate main fields so it behaves like a simple property in interfaces and queries |

Structs matter most in AI-first workflows, where a model output has both a result and metadata about it — reasoning, sources, confidence. Capture those together rather than scattering them.

**In practice.** Find multi-field properties whose fields are always used together. Define the struct with clear field names and types. Designate a main field so it behaves like a simple property in most contexts. Use reducers for multi-valued struct properties — noting that a reduced value cannot itself be filtered or queried, and that interface actions targeting one will error, since reduction has no inverse. Supported base types and reducer options are in [platform-constraints.md](platform-constraints.md).

---

## Interfaces

**Use interfaces to build reusable, future-proof abstractions.**

Interfaces are the primary tool for the "do not repeat yourself" principle and for open/closed extensibility. They define a shared shape — properties, links, actions — that several types implement, so workflows can target the interface instead of each type.

| Scenario | Example |
| -------- | ------- |
| Common properties across types | `Inspectable` with `lastInspectionDate` and `inspectionStatus`, implemented by `Vehicle`, `Equipment`, `Facility` |
| Shared workflows | A scheduling workflow targeting `SchedulableResource` works for arenas, conference rooms, and vehicles unmodified |
| Taxonomic grouping | `MilitaryAsset` implemented by `Aircraft`, `Vessel`, `GroundVehicle` for drilldown aggregation |
| Multi-level abstraction | `SchedulableResource extends Trackable`, adding scheduling properties to a broader tracking abstraction |

**Example.** `Vehicle`, `Equipment`, and `Facility` each carrying `lastInspectionDate`, `inspectionStatus`, and their own near-identical "schedule inspection" action is three copies maintained independently. One `Inspectable` interface with one shared action, implemented by all three, leaves each type holding only what is genuinely its own — `make`/`model`/`mileage`, `serialNumber`/`warrantyExpiry`, `address`/`capacity`.

**What an interface is made of.** Interface properties, link type constraints, action type constraints, and metadata. Define the properties locally on the interface — that is the recommended approach — rather than reaching for shared properties by default. Interfaces can extend other interfaces, layering inherited properties, and an object type can implement several.

**Interfaces are abstract.** Unlike object types they have no backing dataset and cannot be instantiated directly, only as an implementing object type. An interface describes a shape; it never holds data.

**Platform reality.** Interface-backed workflows are not supported everywhere yet:

| Situation | Guidance |
| --------- | -------- |
| The interface is fully supported in your workflow | Target it directly — one workflow covers every implementing type |
| The interface is not yet supported in that context | Define it now and duplicate the workflow per type as a temporary measure. This is no less efficient than working without an interface, and it establishes a clear path to consolidation |

Current support levels are in [platform-constraints.md](platform-constraints.md) — check them before promising a workflow that targets an interface.

**In practice.** Where several types share properties, links, or actions, define the interface. Design around capability (`Inspectable`, `Schedulable`, `Billable`) or taxonomy (`MilitaryAsset`, `MedicalDevice`). Target interfaces in actions, functions, and applications. Extend interfaces from interfaces for layered abstraction. Scaffold now, consolidate later.

---

## Links and object-backed link types

**Links should represent semantically meaningful relationships.** Every link type answers a clear domain question: which facility did this patient visit? which team does this employee belong to? which equipment was used in this work order?

| Link type | Use when | Example |
| --------- | -------- | ------- |
| Direct link | The relationship is meaningful but carries no metadata of its own | `Employee → Department` |
| Object-backed link | The relationship carries its own metadata — dates, roles, status, allocation | `Employee → VentureStaffing → Venture`, with role, `startDate`, allocation |

Not every linking object needs to be visible everywhere. Some workflows want the join metadata, others just the connection — object-backed links let you expose either view.

**Example.** Employees assigned to ventures, where each assignment has a role and a start date. A direct `Employee → Venture` link has nowhere to put them. Putting `ventureRole` and `ventureStartDate` on `Employee` is ambiguous the moment somebody has two assignments. A `VentureStaffing` object carrying `role`, `startDate`, `allocationPercentage`, and `status` gives workflows both the direct view (`Employee → Venture`) and the detailed one.

| Problem | Impact |
| ------- | ------ |
| Lost metadata | Direct links cannot capture when, why, or in what capacity a relationship exists |
| Ambiguous multi-links | Properties like `ventureRole` on the source object break when an entity has several relationships |
| Meaningless links | Links existing only because two datasets share a foreign key add noise and confuse navigation |

**Mechanics worth knowing.** A link type is bidirectional by definition: one type, two sides, each with its own display and API name, each traversable independently. Creating a link type does not create a reverse one — the single type already goes both ways, which is why both names must be settled together. Link types can relate an object type to itself (`Direct Report ↔ Manager` on `Employee`). Links across different ontologies are not supported; use a shared ontology. Where two types relate many-to-many, datasources back the link type itself.

**In practice.** Validate the semantic meaning — ask whether the relationship matters in the domain, not whether the datasets join. Check whether it carries metadata, and use an object-backed link if so. Expose the level of detail each workflow needs. Name links so they read from both directions.

---

## Naming conventions

Covered in full in [naming.md](naming.md). The short version: consistent, descriptive naming is one of the highest-leverage investments in ontology quality, it makes the model navigable by humans and agents alike, and it is far harder to correct once the ontology is in use.

---

## Security design

**Design security semantically, following least privilege.**

Security should be expressed in domain terms, not data-infrastructure terms. Someone should be able to read a security configuration and understand what is protected and why.

| Layer | Controls | Example |
| ----- | -------- | ------- |
| Row-level | Which objects a user can view | VIP patients restricted to senior staff |
| Column-level | Which properties a user can view on visible objects | Clinical notes restricted to the care team |
| Cell-level (combined) | The intersection of both | VIP patients' clinical notes visible only to the senior care team |

**Example.** Splitting patients into `PublicPatient` and `RestrictedPatient` types duplicates the schema, and a property added to one is easily forgotten on the other. One `Patient` type with `diagnosis`, `clinicalNotes`, and `mentalHealthRecords` column-restricted to the care and psychiatry teams, plus row-level restriction of VIP patients to senior staff, achieves the same protection through policy — and the domain boundaries drive the access rules.

| Problem | Impact |
| ------- | ------ |
| Duplicated types for security | Schemas drift; properties added to one are forgotten on the other. Violates "do not repeat yourself" |
| Over-permissive defaults | Starting broad and restricting later risks exposure before lockdown completes |
| Ad-hoc filtering instead of policy | Security scattered through application code is fragile and hard to audit |
| Misaligned boundaries | Security boundaries that ignore domain boundaries are harder to reason about and likelier to have gaps |

**In practice.** Start restrictive and widen deliberately. Combine row- and column-level security for cell-level control. Align security with domain boundaries — a regional manager sees their region, a care team sees their patients — modelled through ontology relationships rather than ad-hoc filtering. Never duplicate a type for security. Review every new link, type, or property for whether it preserves the protections around restricted data.
