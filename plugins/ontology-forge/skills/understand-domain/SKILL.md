---
name: understand-domain
description: "Stage 01 of ontology design. Use when /understand-domain, 'understand the domain', starting an ontology from scratch, or when a model is being proposed before anyone has established what the domain actually contains. Interviews the user as a domain expert, separates entities from events from decisions, and produces a domain brief plus glossary that stage 02 designs against."
metadata:
  disable-model-invocation: "true"
---

# Understand the domain

Stage 01 of three. Build a picture of the real world before any object type exists. The output is a domain brief and a glossary — no YAML, no object types, no source schemas.

Read [../ontology-forge/references/principles.md](../ontology-forge/references/principles.md) first.

## Start

Open a todolist with one entry per phase.

1. Scope
2. Elicit
3. Separate
4. Pressure-test
5. Write the brief

## Phase 1: Scope

Establish what is in and what is out before elicitation, or the interview never terminates.

Ask the user:
- What decisions or workflows should this ontology support? Name two or three concretely.
- Who are the people doing that work, and what do they call themselves?
- What is explicitly out of scope for now?

If the user answers in terms of systems ("we need to model Salesforce"), redirect once: ask what the people using Salesforce are actually doing. Model the work, not the tool.

## Phase 2: Elicit

Interview the user as the domain expert. Ask in their language, never in ontology vocabulary — do not say "object type" in this phase.

Work through these, one theme at a time:

- **Things.** What are the nouns people in this domain talk about all day? What does a new joiner have to learn the meaning of in week one?
- **Happenings.** What events occur? What has a timestamp attached to it in the way people describe it?
- **Decisions.** Where does a human decide something and record the decision? Who is allowed to?
- **Questions.** What does someone need to look up, and how do they navigate to it? "I have a work order, and I need to know…" — the rest of that sentence is a link.
- **Rules.** What must always be true? What combinations are impossible?
- **Pain.** Where does the current setup fail them? What is duplicated, out of date, or manually reconciled today?

Ask follow-ups on anything vague. When the user uses a word twice with different meanings, stop and pull it apart — that is a God Object being born.

Use `AskUserQuestion` when the user faces a genuine either/or about their own domain. Use plain questions for open elicitation.

## Phase 3: Separate

Sort what you heard into four buckets. This is the analytical work of the stage.

| Bucket | Test | Becomes, later |
| ------ | ---- | -------------- |
| **Entity** | Has identity and persists. You can point at it next month and it is the same one. | Object type |
| **Event** | Happened at a time. Does not change afterward. | Object type, usually linked to an entity |
| **Attribute** | Only ever describes something else. No independent existence. | Property |
| **Relationship** | Connects two things and answers a navigation question. | Link type |

Two separations matter most:

**Identity from observation.** A vessel is an entity. Its position at 14:32 is an observation. Fusing them gives you a vessel type that changes shape every ping.

**The same word used by two teams.** Write both meanings down separately. Resolve it now, with both teams in the room if possible. This is the Department Silos anti-pattern, and it is far cheaper to fix here than after two teams have built on it.

## Phase 4: Pressure-test

Before writing the brief, check the picture holds:

- Walk each named workflow through the entities and relationships. Where you cannot get from A to B, a link is missing.
- For each entity, ask what distinguishes one instance from another. No answer means it is an attribute, not an entity.
- For each entity, ask whether two of them are the same real-world thing under different names.
- Count the shortcuts. Every "we'll figure that out later" gets recorded, not dropped.

## Phase 5: Write the brief

Write two files. Directory defaults to `ontology/`; use the user's if they have one.

**`ontology/GLOSSARY.md`** — every domain term, defined in the user's language, with any conflicting usages flagged and how they were resolved. This is the artifact you validate names against in stage 02.

**`ontology/DOMAIN-BRIEF.md`** — structured as:

```markdown
# Domain brief

## Scope
Workflows and decisions this ontology serves. What is out of scope.

## Actors
Who does the work, what they are responsible for.

## Entities
One section each: what it is, what makes one distinguishable from another,
its lifecycle, who owns it.

## Events
What happens, to what, and when.

## Relationships
Plain-English statements: "a work order is carried out on exactly one asset";
"a technician is assigned to many work orders over time".

## Rules and invariants
What must always be true.

## Open questions
Unresolved conflicts, terms two teams disagree on, gaps needing a stakeholder.
```

## Finish

State plainly what is still unresolved, then offer stage 02: `/ontology-forge:design-ontology`.

Do not create object types in this stage, even when the shape looks obvious. Committing to a type here is how a domain brief silently becomes a source-schema transcription.
