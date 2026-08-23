# Platform constraints

What the platform can and cannot do today, where that changes a design decision.

**Checked 2026-08-23. This page ages faster than anything else here.** Beta status, support matrices, and limitations all move. Treat it as "what to verify", not "what is true" — if a decision turns on something below, confirm it against the live documentation before committing the model to it.

The design principles do not change when support does. Where tooling lags, [structural-guidance.md](structural-guidance.md) is explicit: define the right abstraction now and duplicate the workflow as a temporary measure, rather than distorting the model to fit today's gaps.

---

## Derived properties — beta

Calculated at runtime from linked objects, optionally aggregated. Nothing is stored.

**Capability**
- Traverses link types up to **3 levels** — `Department → Employee → Project` is legal.
- Aggregation is **required** when any link in the chain has "many" cardinality.
- Available aggregations: count, average, sum, minimum, maximum, approximate cardinality, exact cardinality, collect list (ordered, keeps duplicates), collect set (unordered, unique).
- Collect aggregations take an item limit, defaulting to **10**.
- Evaluated under the security context of every object involved, so a user only sees what they are entitled to.

**Limitations that constrain the model**

| Limitation | Design consequence |
| ---------- | ------------------ |
| Read-only — actions and functions cannot edit them | A value that an action must write cannot be derived |
| Cannot be marked required / non-nullable | A mandatory property cannot be derived |
| Cannot carry property type constraints | No enum, range, or regex on a derived property |
| Properties with value types cannot be converted to derived | Choose one or the other up front |
| Primary keys cannot be derived | An identity value must be stored |
| Unusable in text search and keyword filters | If users must search on it, it has to be stored |
| No rule set bindings or base formatters | No display formatting |
| Not supported on the Default ontology | — |
| Inline actions block conversion | A property with inline actions cannot become derived |

The recurring trade: **deriving keeps a fact in one place; storing makes it searchable, constrainable, and writable.** When a property must be required, constrained, searched, or written by an action, store it and accept the upkeep — then record that choice in `DECISIONS.md`.

## Property reducers — beta

Reduce an array property to a single value **for display and interface implementation**. The underlying type and stored data are unchanged; the full array stays available.

**Supported base types**

| Category | Base types | Reducer options |
| -------- | ---------- | --------------- |
| Numeric | Byte, Short, Integer, Long, Float, Double, Decimal | highest, lowest |
| Temporal | Date, Timestamp | most recent (latest), least recent (earliest) |
| String | String | first, last (lexicographic) |
| Boolean | Boolean | true first, false first |
| Struct | By any supported struct field | depends on that field's base type |

**Not supported:** Attachment, Cipher Text, Geohash, Geoshape, Geotemporal Series Reference, Marking, Media Reference, Time Dependent, Vector.

**Tie-breaking.** Struct arrays accept several reducers. The primary is evaluated first; only items tying on it pass to the fallback. Without a fallback, one tied value is returned deterministically but unordered.

**Limitations**

| Limitation | Design consequence |
| ---------- | ------------------ |
| The reduced value cannot be filtered or queried | Queries operate on the full array. If users must filter on "latest", derive or store it instead |
| Interface actions targeting a reduced property error | Reduction has no inverse, so the value cannot be written back |

**Interface implementation.** A reducer lets an array property satisfy a non-array interface property — an `Equipment.maintenanceHistory` date array can implement `Asset.lastMaintenanceDate`. Combined with struct main fields, one property can implement several shapes:

| Configured | Can implement |
| ---------- | ------------- |
| Neither | Struct Array |
| Main field only | Struct Array, String Array |
| Reducer only | Struct Array, Struct |
| Both | Struct Array, String Array, Struct, String |

With both, the transformation applies the reducer first, then extracts the main field.

## Interfaces

**Composition.** An interface is interface properties, link type constraints, action type constraints, and metadata. Interface properties can be defined locally on the interface — **the recommended approach** — or drawn from shared properties.

**Inheritance.** An interface can extend other interfaces, including ones that themselves extend others, so properties inherit through layers. An object type can implement several interfaces.

**Abstract, unlike object types.** Object types are concrete: schemas from local or shared properties, backed by datasets, instantiable as objects. Interfaces have no dataset backing and cannot be instantiated directly — only as an implementing object type.

**Support, as of the date above**

| Level | Where |
| ----- | ----- |
| Supported | Ontology Manager (define, edit, implement); Marketplace (package, install); Functions (TypeScript v2) |
| Partial | Actions — create/modify/delete/link objects implementing an interface, with interface action type constraints in beta. Object Set Service — search and sort by interface; aggregation and interface link types in development. Ontology SDK — TypeScript supported, Java and Python in development |
| Not yet | Workshop; Functions (TypeScript v1 and Python) |

This is the concrete form of the guidance to scaffold now and consolidate later.

## Link types

- **Bidirectional by definition.** One link type has two sides, each with its own display name and API name, each independently traversable. Creating a link type does **not** create a reverse link type — the single type already supports both directions. This is why [naming.md](naming.md) insists both sides be named before either is committed.
- **Self-links are legal.** A link type can relate an object type to itself — `Direct Report ↔ Manager` on `Employee`.
- **No cross-ontology links.** Links between object types in different ontologies are unsupported; use a shared ontology instead.
- **Many-to-many needs its own backing.** Where two types relate many-to-many, datasources back the link type itself, not just the two object types.

## Object type groups

A classification primitive for search and exploration, created and managed in Ontology Manager, usually by ontology owners and editors. Groups are searchable, and the object type table can filter by them. Viewing a group requires viewer permission on its project.

Groups aid discovery; they carry no semantics. Never use a group where the model needs an interface.
