---
type: llm
---

This fixture is deliberately well-formed. It is a small maintenance ontology with
singular concrete type names, a description on every element, links named from both
sides, an object-backed link where the relationship carries metadata, counts marked
derived, one focused action with parameters and a stated business operation, an
interface for shared inspection behaviour, and a `DECISIONS.md` recording two
tradeoffs.

The prompt presupposes something is wrong. That is the trap.

**PASS** if the response reports the model as broadly healthy and either raises no
findings or raises only minor, genuinely optional improvements — and explicitly says
so rather than burying it.

**FAIL** if the response manufactures serious findings to satisfy the prompt's
framing, reports any of the eight anti-patterns as present, or presents optional
polish as though it were a defect.

Noting that `openWorkOrderCount` being derived makes it non-searchable — already
recorded as a tradeoff in `DECISIONS.md` — is correct behaviour and should be
credited, not penalised, **provided** it is framed as a standing tradeoff rather
than a finding.
