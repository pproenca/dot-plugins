---
name: forge
description: "The entry point for ontology work. Use when /forge, 'start an ontology', 'continue the ontology', 'resume the model', 'where were we', 'what is the next step', or whenever the user wants the ontology workflow driven for them rather than having to name a stage themselves. Reads ontology/STATUS.md, reports where the work stands, runs the next stage, and returns to a checkpoint when it finishes."
---

# Forge

Drive the ontology workflow. The user should never have to know which stage comes next or
what it is called — read the position, show it, run the next step, come back and ask.

```
   01 understand-domain ──► 02 design-ontology ──► 03 map-sources ──► 04 write-contracts
        │                        │                     │                    │
        │                        └──► extend-ontology ─┘                    │
        │                        │                                          │
        └────────────────────────┴──────────────────────────────────────────┴──► audit-ontology
```

Every stage ends at a checkpoint here. Never run two stages back to back without showing the
user what the first one produced — stage 02 committing to types the user would have corrected
is the expensive failure, and it is only catchable at the boundary.

## Phase 1: Orient

Find the model directory. Default `ontology/`; if the user has one elsewhere, use theirs and
record the path in STATUS.md.

Read `ontology/STATUS.md`. It is the position of record — the format and its rules are in
[../ontology-forge/references/status-format.md](../ontology-forge/references/status-format.md).

If it does not exist, reconstruct the position from what is on disk using the derivation table
in that reference, write the file, and say it was reconstructed. Do not ask the user where they
are when the files can answer it.

Then read what the reconstruction depends on — `DOMAIN-BRIEF.md`, `DECISIONS.md`, the object
type filenames. Enough to describe the position accurately, not the whole model.

## Phase 2: Show the board

Report the position before doing anything with it. Three things, briefly:

- Each stage and its state, with what it produced.
- Open questions and thin-evidence decisions carried forward, counted and named.
- Anything in the domain brief not yet modelled.

Keep it to what fits on a screen. This is orientation, not a report — the detail is in the
files, and the user can open them.

## Phase 3: Offer the move

Use `AskUserQuestion` with concrete options drawn from the actual position. Put the natural
next step first. Options are real work, never "continue" — name the stage and what it will do.

| Position | Offer first | Also offer |
| -------- | ----------- | ---------- |
| Nothing on disk | Stage 01, understand the domain | Design directly, flagged as skipping 01 |
| 01 done | Stage 02, design the object model | Revisit an open question first |
| 02 in progress | Resume 02 at its phase | Audit what exists so far |
| 02 done | Stage 03, map source data | Audit before mapping |
| 03 done | Stage 04, write the data contracts | Audit before contracting |
| 04 done for one direction | The other direction — inbound or outbound | Audit the whole model |
| 04 done | Audit the whole model | Extend it with a new requirement |
| Open questions blocking a type | Resolve the question | Proceed and record it as thin evidence |

When the user arrives with a specific request — a new requirement, "audit this" — skip the menu
and go straight to the stage that serves it. The menu is for when the next move is genuinely the
user's call, not a toll booth on a clear instruction.

## Phase 4: Run the stage

Invoke the stage with the Skill tool. Do not paraphrase a stage's method into this
conversation — the stage skills carry the actual procedure and its guardrails:

| Stage | Skill |
| ----- | ----- |
| 01 Understand the domain | `ontology-forge:understand-domain` |
| 02 Design the ontology | `ontology-forge:design-ontology` |
| 03 Map source data and logic | `ontology-forge:map-sources` |
| 04 Write the ODCS data contracts | `ontology-forge:write-contracts` |
| Add a requirement to an existing model | `ontology-forge:extend-ontology` |
| Review for anti-patterns | `ontology-forge:audit-ontology` |

Pass along what the stage needs to start where the user is: the model directory, the open
questions relevant to it, and any constraint the user just stated.

## Phase 5: Checkpoint

When the stage returns, before offering anything further:

1. **Verify it wrote files.** Every stage's output is files under the model directory. If the
   stage produced its result only in the response, write the files now.
2. **Update STATUS.md.** New stage states, new open questions, resolved ones checked off, thin
   evidence added, `Next` pointing at a real command.
3. **Report what changed**, including what the stage could not settle.
4. **Return to Phase 3.** The board has moved; offer the next move against the new position.

Stop the loop when the user says so, or when the next move needs an answer only a stakeholder
outside the conversation can give. Say which it is.

## Non-negotiables

**Output is files, never an Artifact.** Everything this workflow produces goes to the model
directory as files: the brief, the glossary, the YAML, DECISIONS.md, STATUS.md, AUDIT.md. Do
not publish an artifact, and do not render any of it as a web page — not the domain brief, not
the audit, not a summary of the model, however much it reads like a finished deliverable. The
user works on these files in their repository and reviews them in a diff. A published page is a
copy that immediately goes stale and cannot be reviewed.

**One question per message.** Every stage that talks to the user asks one thing at a time and
never emits a second question mark. That applies to this skill too. See
[interviewing.md](../ontology-forge/references/interviewing.md).

**The stage order is not negotiable without saying so.** The user may skip stage 01. Record it
as `skipped` in STATUS.md with the risk stated, and never silently treat it as done.

**These files are a design specification.** Ontology Manager is the system of record. Never
imply that writing YAML here changes a live ontology.
