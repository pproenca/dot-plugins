# Anti-pattern catalog

Eight named failure modes, each with what it looks like, why it hurts, and the fix. This is the checklist [audit-ontology](../../audit-ontology/SKILL.md) runs against.

Source: [Ontology anti-patterns](https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns/).

---

## 1. System Silos

**Recognise:** separate object types for the same entity, split by which system it came from — `HrSystemEmployee`, `BadgeSystemEmployee`, `ProjectManagementEmployee`.

**Harm:** fragmented user perspective, duplicated development, conflicting data across types, and a maintenance burden every time business logic changes.

**Fix:** one object type for the real-world entity. Merge the systems upstream in a pipeline. Identify a cross-system primary key and build joining transforms with explicit precedence rules for conflicts.

**Audit signal:** two or more object types whose property sets overlap heavily and whose names contain a source-system word.

---

## 2. The Kitchen Sink

**Recognise:** object types carrying technical columns with no business relevance — ETL metadata, internal system IDs, debug timestamps, `_ingested_at`, `row_hash`.

**Harm:** users cannot find the fields that matter, performance degrades on properties nobody reads, and business insight is buried among system artifacts.

**Fix:** curate properties intentionally. For each one ask: *would someone ever need to see, search, or filter by this?* If not, it stays in the backing dataset.

**Audit signal:** properties whose names are snake_case system idioms, or which appear in no action, no workflow, and no view.

---

## 3. Department Silos

**Recognise:** each department builds its own version of a shared entity — `SalesCustomer`, `SupportCustomer`, `BillingCustomer`, `MarketingContact` all describing the same real customer.

**Harm:** no single source of truth, cross-departmental workflows become impossible, development is redundant, and governance multiplies.

**Fix:** shared object types serving several departments, with properties for department-specific attributes and link types for connections to department resources. Establish a cross-functional working group to agree the unified entity.

**Audit signal:** distinct types sharing a primary-key semantic; department names appearing in type names.

---

## 4. The God Object

**Recognise:** one object type standing in for several distinct entities. Many null properties. Property meaning that depends on conditional logic. Users asking "what kind of *[Object]* is this?"

**Harm:** semantic confusion, sparse null-heavy objects, validation that cannot be written because business rules conflict, poor search, and action types thick with conditionals.

**Fix:** distinct object types for distinct real-world entities. Where they genuinely share properties or behaviour, model that with an interface rather than fusing the types.

**Audit signal:** high null density; a `type` or `category` property that switches the meaning of other properties; property count far above sibling types.

---

## 5. The Golden Hammer

**Recognise:** one tool used for every job — action types running batch calculations, pipelines reacting to events, functions computing values that could have been pre-computed.

**Harm:** scalability limits hit early, unnecessary complexity, users made to trigger work that should be automatic, performance problems from running logic in the wrong layer, and hard debugging.

**Fix:** match the mechanism to the job — see the placement table in [structural-guidance.md](structural-guidance.md).

**Audit signal:** action types with no human decision in them; functions recomputing a value that never changes between writes.

---

## 6. Action Sprawl

**Recognise:** many narrow action types each touching one property — `UpdateEmployeeFirstName`, `UpdateEmployeeEmail`. More than ten actions on one object type. Names that read `Set [Property]`.

**Harm:** overwhelming UX, workflows fragmented across several submissions, actions that map to database updates rather than business processes, and audit trails scattered across many entries.

**Fix:** design actions around business operations. Bundle related changes into one action that represents a real process, name it after that process, and use optional parameters for the fields that vary.

**Audit signal:** action names beginning `set`, `update`, or `change` followed by a single property name; action-to-object-type ratio above ten.

---

## 7. The Time Machine

**Recognise:** history modelled as separate objects or types — `Contract v1` / `v2` / `v3`, or `Contract2023` / `Contract2024`.

**Harm:** object count explodes with redundant data on every change, current state becomes ambiguous, link targets are unclear, and reporting across periods is complex and error-prone.

**Fix:** one object per entity holding current state. Put historical change in a separate linked type — an amendment or revision object capturing timestamp and reason — or use edit history or time series properties.

**Audit signal:** version or year tokens in type or property names; near-duplicate types differing only by period.

---

## 8. The Misnomer

**Recognise:** vague, generic, or misleading names — `value`, `type`, `date`, `status`, `Item`, a link called `relatedItems`. Users repeatedly asking what something means.

**Harm:** data gets misinterpreted, new team members face a steep climb, everyone depends on out-of-band documentation, and teams use the same field inconsistently.

**Fix:** specific, self-documenting names. Qualify ambiguous properties — `monetaryValue`, `quantityOnHand`, `riskScore`. Name links so they explain the relationship. Add descriptions stating meaning and valid values. Validate names with the people who will use them.

**Audit signal:** any property or link matching the generic-name list in [naming.md](naming.md).
