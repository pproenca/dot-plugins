# Anti-pattern catalog

Eight named failure modes. Each entry gives what causes it, how to spot it, a worked example, what it costs, and how to fix it. [audit-ontology](../../audit-ontology/SKILL.md) runs this catalog; [detection-rules.md](detection-rules.md) turns the indicators into mechanical checks.

Distilled from [Ontology anti-patterns](https://www.palantir.com/docs/foundry/ontology/ontology-anti-patterns/).

## At a glance

| Anti-pattern | Shape | Fix |
| ------------ | ----- | --- |
| System Silos | A separate object type per source system | Merge upstream in a pipeline; one unified type |
| The Kitchen Sink | Technical columns carried in as properties | Curate deliberately; leave ETL metadata behind |
| Department Silos | Each department owns its own copy of a shared entity | One shared type; properties and links for local needs |
| The God Object | One type standing in for several entities | Distinct types; interfaces for what they truly share |
| The Golden Hammer | One tool used for every job | Match mechanism to job |
| Action Sprawl | Many single-property actions | Actions shaped around business operations |
| The Time Machine | History modelled as separate objects or types | One object per entity; history in a linked type |
| The Misnomer | Vague or generic names | Specific, self-documenting names |

---

## 1. System Silos

A separate object type for the same real-world entity per source system, modelling the plumbing instead of the entity.

**Causes.** Different teams own different source systems and build independently. Uncertainty about how to merge across sources. A wish to keep every system-specific field rather than decide what is essential.

**Example.** Employee data lives in an HR system, a badge access system, and a project management tool. Instead of one `Employee`, the ontology gets `HrSystemEmployee`, `BadgeSystemEmployee`, and `ProjectManagementEmployee`.

| Problem | Impact |
| ------- | ------ |
| Fragmented view of reality | Users navigate three object types to understand one person |
| Duplicated effort | Actions, links, and applications built three times for one concept |
| Inconsistent data | The same employee carries conflicting values with no source of truth |
| Complex maintenance | Every business-logic change is replicated per system-specific type |

**Fix.** One object type for the entity, backed by a dataset that merges the sources.

1. Find the primary key that identifies the entity across systems.
2. Build a transform joining all sources.
3. Set explicit precedence for conflicting values — HR is authoritative for job title, say.
4. Back the single object type with the merged dataset.

---

## 2. The Kitchen Sink

Object types carrying columns from source systems that have no business meaning — technical artifacts cluttering the model.

**Causes.** "Just in case" retention. No clarity on which fields are meaningful. Direct mapping without curation. Fear of losing data by excluding a column.

**Example.** A `Customer` built from a CRM keeps `customerId`, `customerName`, and `email` — correctly — alongside `_crm_extracted_at`, `_crm_received_at`, `_crm_batched_at`, `_crm_sequence`, `_crm_table_version`, `_crm_internal_record_id`, and `last_etl_update_timestamp`.

| Problem | Impact |
| ------- | ------ |
| Confusion | Irrelevant technical fields sit beside business data |
| Performance degradation | Extra properties inflate scale, compute, and index size, slowing search |
| Obscured insights | Business properties are buried among system metadata |

**Fix.** Curate. Decide per column using this split:

| Include | Exclude |
| ------- | ------- |
| Business identifiers — customer ID, order number | Pipeline metadata |
| Human-readable attributes — name, description | Internal system IDs with no business meaning |
| Dates relevant to business process | Timestamps that only matter to data engineering |
| Status fields needed for filtering or actions | Audit columns for pipeline debugging |

The governing question for each column: *would someone ever need to see, search, or filter by this?* Keep technical metadata in the backing dataset for debugging without exposing it. Hide borderline properties that must exist but are rarely needed. Record why each property exists and who uses it.

---

## 3. Department Silos

Each department builds its own version of a shared entity, so the ontology mirrors the org chart instead of the business.

**Causes.** Departments working without cross-functional coordination. Each team believing its view of the customer is unique. No central design authority. Teams wanting control over "their" data.

**Example.** Sales creates `SalesCustomer`, support creates `SupportCustomer`, finance creates `BillingCustomer`, marketing creates `MarketingContact`. All four are the same person.

| Problem | Impact |
| ------- | ------ |
| No single source of truth | Departments hold conflicting information about one customer |
| Impossible cross-functional workflows | "Show me every interaction with this customer" cannot be answered |
| Duplicated development | Each department rebuilds the same actions, links, and applications |
| Governance nightmare | Quality problems multiply; a fix in one type does not propagate |

**Fix.** One shared `Customer`, with department-specific attributes as properties (`salesStatus`, `supportTier`, `billingAccountId`) and links out to department-owned objects (sales opportunities, support tickets, invoices).

1. Identify entities that cross departmental boundaries.
2. Convene a cross-functional group to define the shared type.
3. Capture department-specific attributes as properties on the shared object.
4. Link the shared object to department-specific objects.
5. Give departments different *views* through object views or curated applications — not different types.
6. Use restricted views where only one team may see certain properties.

---

## 4. The God Object

One object type overloaded to represent several distinct entities.

**Causes.** Over-abstraction on superficial similarity — "they are all assets". A wish to minimise type count. No clear entity definitions before building. Scope creep as use cases pile onto an existing type.

**Indicators.**
- Many properties frequently null.
- A property's meaning changes based on another property's value, such as `type` or `category`.
- Viewing an object prompts "what kind of *[Object]* is this?"
- Business rules need extensive conditional logic keyed on the object's "type".

**Example.** An `Asset` type meant to cover "anything valuable" ends up holding physical equipment, software licences, real estate, financial instruments, and employees as "human assets". It carries 150+ properties, mostly null for any given object, and `value`, `location`, and `status` mean something different for each kind.

| Problem | Impact |
| ------- | ------ |
| Semantic confusion | Nobody can say what an `Asset` actually represents |
| Sparse data | Most properties are null for most objects |
| Impossible validation | Rules differ per entity type, so none can be enforced |
| Poor search | Searching assets returns a mix of unrelated things |
| Action complexity | Actions must branch across wildly different entities |

**Fix.** Distinct types for distinct entities — `Equipment`, `Vehicle`, `SoftwareLicense`, `Property`, `FinancialInstrument` — with an interface such as `DepreciableAsset` (`purchaseDate`, `purchaseValue`, `depreciationSchedule`) for what they genuinely share.

1. List the distinct entities currently crammed into the type.
2. Create a separate type for each.
3. Identify the genuinely shared properties and behaviours.
4. Model those as interfaces.
5. Migrate existing objects to the new types.

---

## 5. The Golden Hammer

Leaning on one tool for every problem — actions doing batch work, pipelines reacting to events, functions computing what could have been pre-computed.

**Causes.** Familiarity with one tool. Wanting to give users "control" over when computation happens. Unfamiliarity with the rest of the platform. Thinking exclusively in one layer.

**Examples.**
- *Action overuse.* Regional sales totals for a dashboard computed by a `Calculate Regional Sales Totals` action users trigger by hand, instead of a pipeline aggregating them.
- *Pipeline overuse.* An alert object is created by a pipeline; assigning it to the on-call engineer and notifying them is bolted into more pipeline logic instead of an automation reacting to the new object.
- *Function overuse.* `fullName = firstName + lastName` implemented as a function-backed column — runtime overhead and a code repository to maintain — where a pipeline concat would do.

| Problem | Impact |
| ------- | ------ |
| Scalability limits | Each tool has different execution ceilings; the wrong one hits them early |
| Unnecessary complexity | Logic in the wrong layer means more moving parts |
| User burden | People click buttons the platform could have handled |
| Performance issues | Action- or function-time computation is slower than pre-computed results; scheduled pipelines are too slow for event-driven work |
| Difficult debugging | Failures in the wrong layer are harder to diagnose |

**Fix.** Match tool to job:

| Tool | Best for | Not ideal for |
| ---- | -------- | ------------- |
| Action types | Human decisions, user-initiated edits to a few objects, input-driven changes applying immediately | Batch calculation, scheduled updates, event reactions with no human |
| Pipelines (batch) | Batch processing, aggregation, cleansing, enrichment, pre-computing derived values | Real-time reaction to single-object change; anything needing human input |
| Pipelines (streaming) | Continuous low-latency processing where results must stay current | Infrequent updates; human input; reacting to ontology-level events |
| Automations | Event-driven reaction to ontology change — object created, property updated — orchestrating actions or notifications without a user | Heavy data processing, complex multi-dataset joins, human judgment |
| Functions | Complex real-time computation across objects, validation, values depending on live ontology state | Simple derivations computable in a pipeline; batch processing at scale |
| Schedules | Recurring builds, time- or event-based refresh orchestration | Reacting to individual object changes in real time |

Five questions that place logic correctly:

1. Before an action — *does this need human judgment or input?* If not, it belongs in a pipeline or automation.
2. Before pipeline logic — *is this a data transformation, or an operational workflow?* Cleansing, aggregation, enrichment are pipeline work; assigning work, notifying, and reacting to individual changes are automation work.
3. Before a function — *can this be pre-computed upstream?* If it depends only on source columns and needs no live ontology traversal, compute it in the pipeline.
4. Before a polling pipeline — *can an automation react to this event directly?* Automations respond in near-real-time without scheduled-build overhead.
5. Before defaulting to batch — *does this need to be continuously current?* If consumers need low latency, use streaming.

---

## 6. Action Sprawl

Many narrow action types each touching one property, instead of actions representing business operations.

**Causes.** Thinking of actions as column updates. Building incrementally without considering overall experience. Not knowing actions can bundle changes. Mimicking CRUD from traditional application development.

**Indicators.**
- More than 10 action types on a single object type.
- Several actions always performed in sequence.
- Names reading `Set [Property]` or `Update [Property]`.
- Users complaining about how many steps a task takes.

**Example.** An `Employee` type accumulates `Update Employee First Name`, `Update Employee Last Name`, `Update Employee Email`, `Update Employee Phone`, `Update Employee Department`, `Update Employee Manager`, and twenty more.

| Problem | Impact |
| ------- | ------ |
| Overwhelming experience | A long cluttered list; users cannot find the right action |
| Fragmented workflows | One business task needs several submissions |
| No business representation | Actions map to database updates, not real processes |
| Fragmented audit trails | History scatters across many small actions, obscuring what happened and why |

**Fix.** Bundle related changes into actions named for the operation:

- `Update Employee Contact Information` — firstName, lastName, email, phone.
- `Transfer Employee to New Department` — newDepartment, newManager, newLocation, effectiveDate.
- `Onboard New Employee` — every field a new hire needs, triggering badge and equipment workflows downstream.

Map the real processes first, group the property changes each one implies, use parameters for optional fields, name after the business operation, and enforce constraints with action rules and validation.

---

## 7. The Time Machine

Historical versions modelled as separate objects or types instead of proper temporal strategy.

**Causes.** Wanting a complete history of every change. Misunderstanding temporal modelling. Applying file-versioning habits (v1, v2, v3) to objects. Not knowing about time series properties or linked history patterns.

**Indicators.**
- One object type holds several objects representing the same entity at different times.
- Properties like `version`, `revision`, or `isCurrent` exist to tell copies apart.
- Object counts grow with the number of *changes* rather than the number of *entities*.
- Users are unsure which object to reference or link to.

**Example.** `Contract v1`, `Contract v2`, `Contract v3` as separate objects — or worse, `Contract2023`, `Contract2024`, `Contract2025` as separate object types. Each version is a full copy, and links to vendors and departments are duplicated across all of them.

| Problem | Impact |
| ------- | ------ |
| Object count explosion | Every change creates an object, inflating the ontology with redundancy |
| Ambiguous current state | Hard to tell which version is authoritative |
| Ambiguous links | Which version should a vendor link to? |
| Complex reporting | Cross-period reporting needs error-prone filtering and deduplication |

**Fix.** One `Contract` per contract holding current state (`currentValue`, `currentStatus`, `effectiveDate`), linked to a `ContractAmendment` type capturing `amendmentDate`, `previousValue`, `newValue`, `changeReason`. Use time series properties for values that change frequently, and edits history or the backing dataset for full audit trails.

---

## 8. The Misnomer

Vague, generic, or misleading names that fail to communicate meaning.

**Causes.** Shorthand that makes sense to the author alone. Names carried straight from source columns without translation. Brevity preferred over clarity. No naming conventions or governance. Assuming context makes meaning obvious.

**Indicators.**
- Users repeatedly ask "what does this property mean?"
- A name could reasonably refer to several concepts.
- Single generic words as property names — `value`, `type`, `status`, `date`, `name` — with no qualification.
- Link types labelled "related to" without saying how.

**Example.** An object type `Item` (product? line item? inventory item?). A property `value` (monetary? quantity? score? rating?). A property `type` (of what, with which valid values?). A property `date` (created? modified? due? effective?). A link `Item → Related Item` (parent-child? substitute? accessory?).

| Problem | Impact |
| ------- | ------ |
| Misinterpretation | Users cannot understand the ontology unaided, so analysis and decisions go wrong |
| Steep learning curve | New team members spend real time decoding vague names |
| Documentation dependency | Docs become essential rather than supplementary, and go stale |
| Cross-team confusion | Teams read the same vague name differently and use it inconsistently |

**Fix.** Specific, self-documenting names.

| Instead of | Use |
| ---------- | --- |
| Object type `Item` | `Product`, `SalesOrderLineItem`, `WarehouseInventoryRecord` |
| Property `value` | `monetaryValue`, `quantityOnHand`, `riskScore` |
| Property `type` | `productCategory`, `serviceTier` |
| Property `date` | `orderPlacedDate`, `contractEffectiveDate` |
| Link `Item → Related Item` | `Product → PurchasingCustomer`, `Employee → Supervisor`, `Equipment → ManufacturingFacility` |

Agree conventions before building and enforce them in review; add descriptions stating meaning and valid values; validate names with the people who will use them daily.

---

## Closing note

These failures are common but avoidable, and design is iterative. Start from clear entity definitions, involve stakeholders early, and refine as you learn. When something feels wrong, come back to this catalog and check whether an anti-pattern is forming — course-correcting early is far cheaper than after applications depend on the shape.
