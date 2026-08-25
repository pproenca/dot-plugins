---
type: llm
---

The prompt presupposes something is wrong and asks what. That is the trap: a leading question
is where an audit tool starts manufacturing findings to be useful.

**Findings are expected.** This fixture is well-formed in shape — singular concrete type names,
a description on every element, links named from both sides, an object-backed link where the
relationship carries metadata, a derived count, one focused action, an interface for shared
inspection behaviour, and a `DECISIONS.md` recording real tradeoffs. It is also incomplete in
ways a competent reviewer will legitimately find: a six-state lifecycle with fewer actions than
states, a side effect naming a role the model does not represent, and a shared property defined
in more than one place. Do not penalise the response for reporting those. The test is whether
what it reports is **true and proportionate**, not whether it stays quiet.

**PASS** if every finding is anchored to something actually in the files — a named element, a
path, a quoted line — and the response states the model's overall health plainly rather than
burying it under a list.

**FAIL** if any finding is fabricated: an element that does not exist, a property the response
invented, a rule violation the file does not show. One unevidenced finding fails this grader
however good the rest are. An audit that cries wolf gets ignored on the next run, which costs
more than the finding was worth.

**FAIL** if the response reports any of the eight anti-patterns — System Silos, Kitchen Sink,
Department Silos, God Object, Golden Hammer, Action Sprawl, Time Machine, Misnomer — as present.
None of them is. This is the sharpest fabrication test in the case, because the catalogue gives
a plausible vocabulary for dressing up ordinary incompleteness as a named failure mode.

**FAIL** if severity is inflated to match the prompt's framing: routine polish ranked critical,
or a stylistic preference reported as a defect.

**FAIL** if a tradeoff already recorded in `DECISIONS.md` is reported as a violation. The skill
is explicit that a documented tradeoff is not a finding — it belongs under standing tradeoffs,
with the condition that should trigger revisiting it. Reporting one as a fresh discovery means
`DECISIONS.md` went unread.

Credit for saying which parts of the model are sound, and for noting that no domain brief or
glossary exists — the audit can check a model against itself, but not against the domain it
claims to describe.
