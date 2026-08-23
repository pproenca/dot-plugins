# Element vocabulary

The Foundry Ontology's own terms, so the model and the conversation use the same words.

Distilled from [Core concepts](https://www.palantir.com/docs/foundry/ontology/core-concepts) and [Types reference](https://www.palantir.com/docs/foundry/object-link-types/type-reference).

## What an ontology is

A categorization of the world — the digital twin of an organization, integrating its digital assets (datasets and models) into a coherent whole by mapping them to object types, properties, link types, and action types.

Foundry splits types two ways: **ontology types** model a real-world domain; **data types** represent data values, drawing on ideas from RDF, OWL, and XSD.

## Schema versus instance

The distinction matters constantly and is easy to blur:

- An **object type definition** is type-level information — display name, property names, property data types, description. This is what the files under `ontology/` specify.
- An **object instance** is the actual primary key and property values for one thing: an `Airplane` with `planeId = my_plane_id1` and `maximumOccupancy = 240`.

The same split applies to link types and links.

## The dataset analogy

Useful for orienting people who think in tables — and dangerous if taken as a design method, since designing from the dataset side is exactly the Domain-driven design failure:

| Datasets | Ontology |
| -------- | -------- |
| Dataset | Object type |
| Row | Object |
| Column | Property |
| Field | Property value |
| Join | Link type |

## Elements

| Element | Definition |
| ------- | ---------- |
| **Object type** | Schema definition of a real-world entity or event. `JFK` and `LHR` are objects of an `Airport` object type. A collection of instances is an **object set**. |
| **Property** | Schema definition of a characteristic of that entity or event. For `Airport`, `name` and `country`. A **property value** is that property on one object. |
| **Shared property** | A property usable across several object types, giving consistent modelling and centralized management of property metadata. |
| **Link type** | Schema definition of a relationship between two object types. A **link** is one instance of it. Bidirectional by definition — two sides, each with its own display and API name — so creating one link type does not create a reverse. May relate a type to itself; may not cross ontologies. |
| **Action type** | Schema definition of a set of changes to objects, property values, and links a user can make at once — including the side effects that fire on submission. Users change objects by applying actions. |
| **Interface** | An ontology type describing the shape of an object type and its capabilities, providing polymorphism so types sharing a shape are modelled and used consistently. Composed of interface properties, link type constraints, action type constraints, and metadata. Abstract: no backing dataset, never instantiated directly. |
| **Object type group** | A classification primitive helping people search and explore the ontology. Aids discovery only — it carries no semantics, so never use a group where the model needs an interface. |
| **Value type** | A semantic wrapper around a field type — metadata plus constraints — for type safety and expressiveness. Email addresses, URLs, UUIDs, enumerations. Unlike field types and base types, value types are created dynamically within a space. |
| **Function** | Code-based logic taking inputs and returning an output, natively integrated: it can take objects and object sets as input, read property values, and be used across action types and applications. |
| **Roles** | The central permissioning model, granting access to ontological resources at ontology or individual-resource level. |
| **Object View** | The central hub for one object — its key information, linked objects, metrics, analyses, dashboards, and applications. |

## Value type constraints

What a value type can enforce, and on which base types. Use these in the `constraints` block of a property in [spec-format.md](spec-format.md):

| Constraint | Meaning | Valid base types |
| ---------- | ------- | ---------------- |
| **Enum (one of)** | A static set of allowed values. For strings, optionally case-sensitive or case-insensitive | String, Boolean, Decimal, Double, Float, Integer, Short |
| **Range** | A minimum, a maximum, or both. For strings this constrains length; for arrays, size | Decimal, Double, Float, Integer, Short, Date, Timestamp, String, Array |
| **Regex** | A pattern the string must match; may optionally pass on a substring match | String |
| **RID** | Must be a valid resource identifier | String |
| **UUID** | Must be a valid UUID | String |
| **Uniqueness** | Every element of the array must be unique | Array |
| **Nested** | A constraint applied to each element — a regex over every string in an array, say | Array |
| **Element constraints** | A mapping from struct field identifier to a value type reference, constraining individual struct components | Struct |

Reaching for a constraint is usually better than describing the rule in prose: it is enforced at the schema level rather than depending on every writer to remember it.
