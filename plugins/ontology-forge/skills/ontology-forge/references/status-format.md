# STATUS.md — the continuity contract

`ontology/STATUS.md` is the one file that answers "where are we?" across sessions. Every
stage reads it on entry and rewrites it on exit. Without it each stage guesses its position
from which files happen to exist, and everything unresolved evaporates into chat scrollback.

It is committed alongside the model, like `DECISIONS.md`. A reviewer reading the repository
should be able to tell what is finished, what is assumed, and what is still open — without
having been in the room.

## Shape

```markdown
# Ontology status

**Stage:** 02 design-ontology — phase 5 of 7 (Actions)
**Directory:** ontology/
**Updated:** 2026-08-25

## Stages

| Stage | State | Produced |
| ----- | ----- | -------- |
| 01 understand-domain | done | DOMAIN-BRIEF.md, GLOSSARY.md (31 terms) |
| 02 design-ontology | in progress | 7 object types, 5 link types, 2 interfaces |
| 03 map-sources | not started | — |
| 04 write-contracts | not started | — |

## Open questions

Unresolved, and what each one blocks. Carried forward until answered or explicitly dropped.

- [ ] Does "account" mean the billing account or the login account? Two teams use it
      differently. Raised stage 01. Blocks the `Customer` / `Account` split.
- [x] Whether returns are in scope — resolved: out of scope for now.

## Thin evidence

Decisions made without a stakeholder confirming them. Each names what would settle it.

- `Shipment.status` valid values inferred from one sample export. Needs ops to confirm
  the full set before actions are built against it.

## Not yet modelled

Parts of the domain brief no type covers yet.

- Billing and invoicing — deferred, brief section 4.
- Warranty claims — deferred, brief section 6.

## Next

`/ontology-forge:map-sources`, or `/ontology-forge:forge` to be taken there.
```

## Rules

**States are `not started`, `in progress`, `done`, or `skipped`.** `skipped` records a stage
deliberately bypassed — a design done without a domain brief, say — and reads as a risk, not
an achievement. Never mark a stage `done` that ended early.

**Open questions carry forward.** A stage may add to the list and may resolve entries, but
never silently drops one. Resolving means checking the box and writing the answer inline, so
the history stays readable. Dropping one requires a line saying who decided and why.

**Thin evidence is not the same as an open question.** An open question has no answer yet. Thin
evidence has an answer nobody authoritative has confirmed. Both need to survive the session;
they need different fixes.

**Rewrite the whole file, do not append.** STATUS.md is current position, not a log. The
history belongs in git and the reasoning belongs in `DECISIONS.md`.

**Keep `Next` executable.** It names a command the user can paste, not a description of what
should happen next.

## When there is no STATUS.md

An ontology that predates this file, or one started by hand, still has a position. Derive it
from what is on disk, write the file, and say plainly that it was reconstructed:

| On disk | Stage reached |
| ------- | ------------- |
| Nothing, or an empty `ontology/` | Before 01 |
| `DOMAIN-BRIEF.md` and `GLOSSARY.md`, no `object-types/` | 01 done |
| `object-types/` populated, no `mappings/` | 02 done or in progress |
| `mappings/` populated, no `contracts/` | 03 done or in progress |
| `contracts/` populated | 04 done or in progress, per direction |

A reconstructed file has empty **Open questions** and **Thin evidence** sections. Say so —
those sections being empty means nobody recorded them, not that none exist.
