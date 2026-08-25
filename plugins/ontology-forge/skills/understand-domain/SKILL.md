---
name: understand-domain
description: "Stage 01 of ontology design. Use when /understand-domain, 'understand the domain', starting an ontology from scratch, or when a model is being proposed before anyone has established what the domain actually contains. Interviews the user as a domain expert, separates entities from events from decisions, and produces a domain brief plus glossary that stage 02 designs against."
---

# Understand the domain

Stage 01 of three. Build a picture of the real world before any object type exists. The output is a domain brief and a glossary — no YAML, no object types, no source schemas.

Read [../ontology-forge/references/principles.md](../ontology-forge/references/principles.md) and [../ontology-forge/references/interviewing.md](../ontology-forge/references/interviewing.md) first.

This stage is an interview. **One question per message, never a second question mark** — the whole of the rule and how to sequence questions is in [interviewing.md](../ontology-forge/references/interviewing.md). A batch of questions returns one answer and three silences, and the silences become assumptions.

## Start

Read `ontology/STATUS.md` first. It carries the position, the open questions, and the
thin-evidence decisions from earlier stages — the format is in
[status-format.md](../ontology-forge/references/status-format.md). If it does not exist,
reconstruct it from what is on disk using the derivation table there. Starting without it
means re-asking questions the user has already answered.

Open a todolist with one entry per phase.

1. Scope
2. Elicit
3. Separate
4. Pressure-test
5. Write the brief

## Phase 1: Scope

Establish what is in and what is out before elicitation, or the interview never terminates.

Three things need settling. Ask them in this order, one message each, reading each answer before choosing the next question:

1. **What decisions or workflows should this ontology support?** Ask for two or three concretely. Vague scope is the single most expensive thing to discover late.
2. **Who does that work, and what do they call themselves?** Their words are the naming source for stage 02.
3. **What is explicitly out of scope for now?** Ask this last — it is only answerable once the user has said what is in.

Search the repository before asking any of them. A question whose answer is already in a README spends the user's attention for nothing.

If the user answers in terms of systems ("we need to model Salesforce"), redirect once: ask what the people using Salesforce are actually doing. Model the work, not the tool. That redirect is itself one question — do not append it to another.

## Phase 2: Elicit

Interview the user as the domain expert. Ask in their language, never in ontology vocabulary — do not say "object type" in this phase.

Six themes need covering. This is a queue to work down, not a list to send:

| Theme | What to draw out |
| ----- | ---------------- |
| **Things** | The nouns people talk about all day; what a new joiner must learn in week one |
| **Happenings** | Events that occur; whatever has a timestamp in the way people describe it |
| **Decisions** | Where a human decides something and records it, and who is allowed to |
| **Navigation** | What someone looks up, and how they get to it. "I have a work order, and I need to know…" — the rest of that sentence is a link |
| **Rules** | What must always be true; which combinations are impossible |
| **Pain** | Where the current setup fails them; what is duplicated, stale, or reconciled by hand |

One theme per message, and within a theme, one question. A theme usually takes several turns — that is the expected cost, not a sign of going slowly.

Do not treat the order as fixed. When an answer opens a thread, follow it before returning to the queue; the user's own emphasis is better evidence than the sequence in this table.

Follow up on anything vague, one question at a time. When the user uses a word twice with different meanings, stop and spend a turn pulling it apart — that is a God Object being born, and it is far cheaper to separate now than in stage 02.

Use `AskUserQuestion` when the user faces a genuine either/or about their own domain, with one question in the call. Use plain prose for open elicitation, where offering options would put words in their mouth.

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

Before writing the brief, check the picture holds. Do this analysis yourself first — most of it needs no input from the user:

- Walk each named workflow through the entities and relationships. Where you cannot get from A to B, a link is missing.
- For each entity, establish what distinguishes one instance from another. No answer means it is an attribute, not an entity.
- For each entity, check whether two of them are the same real-world thing under different names.
- Count the shortcuts. Every "we'll figure that out later" gets recorded, not dropped.

Where a gap genuinely needs the user, take it back to them one question at a time. Resist the pull to close the phase by sending a list of everything still open — that is the batching failure at its most tempting, because the gaps are now known and enumerable. Ask the one that changes the model most; the rest often resolve in the answer.

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

Write `ontology/STATUS.md` before saying anything to the user — the shape and its rules are in
[status-format.md](../ontology-forge/references/status-format.md). Stage 01 is where the open
questions list is born, so it matters most here:

- Mark stage 01 `done`, naming what it produced.
- Every term two teams disagreed on, every gap that needs a stakeholder, and everything the
  user deferred goes under **Open questions**, with what each one blocks.
- Anything answered by one person's recollection rather than a source goes under **Thin
  evidence**, with what would settle it.
- Set **Next** to `/ontology-forge:design-ontology`.

Then report what was written and what is still unresolved, and offer stage 02 — hand back to
[forge](../forge/SKILL.md) if that is what invoked this stage, otherwise ask whether to run
`ontology-forge:design-ontology` now.

Do not create object types in this stage, even when the shape looks obvious. Committing to a type here is how a domain brief silently becomes a source-schema transcription.

Write the brief and the glossary as files under the model directory. Do not publish them as an
artifact or render them as a page — the user reviews these in a diff alongside the model.
