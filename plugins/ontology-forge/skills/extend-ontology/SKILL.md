---
name: extend-ontology
description: "Use when /extend-ontology, 'extend the ontology', 'add X to the model', or fitting a new requirement into an ontology that already exists. Finds where the requirement belongs, and prefers extending through new linked types and interfaces over modifying established core types, so applications built on those types keep working."
metadata:
  disable-model-invocation: "true"
---

# Extend the ontology

A model already exists and a new requirement has arrived. The job is to fit it in without breaking what is built on top.

The governing principle is **open for extension, closed for modification**. Established types stay stable; new requirements extend around them. Adding a property to a core type is a modification. Adding a linked type that carries the new concept is an extension. Prefer the second, and reach for the first only when the property genuinely belongs to the core entity and always has.

Read [principles.md](../ontology-forge/references/principles.md) and [structural-guidance.md](../ontology-forge/references/structural-guidance.md) first.

## Start

Open a todolist with one entry per phase.

1. Read
2. Locate
3. Choose the shape
4. Blast radius
5. Write

## Phase 1: Read

Read the existing ontology before proposing anything: `ontology/object-types/`, `link-types/`, `interfaces/`, `action-types/`, and both `DECISIONS.md` and `GLOSSARY.md`.

`DECISIONS.md` matters most. It records why the model is shaped as it is — including compromises that look like mistakes until you read the reason. Do not undo a decision without knowing what it was for.

On a large ontology, dispatch subagents to read subsets of the types in parallel and report back the ones relevant to the requirement.

## Phase 2: Locate

Understand the requirement in domain terms, then find where it already lives.

- Does an existing type already represent this concept under a different name? Check the glossary. Adding a second type for a concept that exists is how Department Silos start.
- Which existing types does the requirement touch?
- Is this a new entity, a new fact about an existing entity, a new relationship, or a new operation?

If the requirement is genuinely a new distinct entity, it becomes a new object type and this is straightforward. The interesting cases are the rest.

## Phase 3: Choose the shape

For a new fact about an existing entity, in order of preference:

**A new linked object type.** The new concept gets its own type, linked to the core type. Nothing existing changes. Use this whenever the fact has its own lifecycle, its own timestamps, or belongs to one team's workflow rather than to the entity itself.

**A new interface, implemented by the existing type.** Use when several types need the same capability. The interface is new; the types gain an implementation without their own definitions being reshaped.

**A new property on the existing type.** Only when the fact is intrinsic to the entity, applies to essentially every instance, and would have been there from the start had anyone thought of it. A property that is null for most objects is not intrinsic — it is a linked type wearing a disguise.

Two shapes to refuse:

- **Widening a type to cover a second entity.** If the requirement is "this type should also represent X", it is a new type plus an interface, not a wider type. This is the God Object forming.
- **Copying a type to make a variant.** `WorkOrderV2`, `AssetForBilling`, a duplicate created for security reasons — all of these drift from the original and never reconverge. Extend the one type.

Apply the rule of three: if this is the third time a similar extension has been made, stop and refactor the shared shape into an interface instead of extending a third time.

## Phase 4: Blast radius

Before writing, work out what the change touches:

- Which action types read or write the affected properties?
- Which links point at the affected types?
- Which interfaces does the type implement, and does the change still satisfy them?
- Would anything already built on this type break?

Anything that would break existing consumers is a breaking change. Say so explicitly and let the user decide — do not absorb it silently.

## Phase 5: Write

Write the new and changed YAML under `ontology/`, following [spec-format.md](../ontology-forge/references/spec-format.md).

Append to `ontology/DECISIONS.md`: what was added, which shape was chosen, which shapes were rejected and why. The rejected options are the valuable part — they stop the next person reopening a settled question.

If the extension needs source data, continue with [map-sources](../map-sources/SKILL.md).

## Finish

Report what changed, what was deliberately left alone, and any breaking change the user needs to rule on. If the requirement could not be fitted without modifying a core type, say that plainly rather than quietly reshaping it.
