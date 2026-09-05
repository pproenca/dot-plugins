# Principles and distinctions

## Preserve the EventStorming experience

Begin with meaningful events in business language and concrete stories. Let different people expose incompatible accounts before normalizing terms. Capture pivotal events, actors, systems, value created or lost, manual work, and hotspots. Narrate the story aloud or in a shared walkthrough; a practitioner challenges and a curator changes the model. Agents can prepare and challenge stories but do not acquire lived domain experience by receiving a persona prompt.

Zoom from Big Picture into Process Modelling, then into Software Design where behavioral precision needs it. Keep the scope provisional during discovery; completion statements identify a frozen version of that scope. Explore adjacent responsibilities when a story crosses the proposed boundary. Never hide a discovered dependency by redefining it out of scope.

Introduce rigor progressively. A database schema imposed during divergent discovery can erase the very contradictions the session is supposed to reveal. Preserve raw narratives and dissent even after producing normalized records.

## Terms that must not collapse

| Term | Meaning and important boundary |
| --- | --- |
| Command | An intention or request. It can succeed, fail, be rejected, or do nothing. An HTTP request is only one possible implementation. |
| Domain event | A meaningful fact expressed in past tense. A proposed event name does not prove an emitted message, stored event log, or event sourcing. |
| Policy | A response to an event, using decision information to choose commands. Record human discretion separately from automatic decisions. |
| Authorization rule | Whether an actor can act on a resource in given conditions. Keep it distinct from a reaction policy and from UI visibility. |
| Read model | Information supporting a decision, including calculations, populations, filters, freshness, and access. A GET operation is not a domain event. |
| Entity / value object | Identity through change versus a value defined by its meaning. A frontend class does not prove a database table. |
| Aggregate | A candidate consistency and decision boundary. Infer it from invariants and behavior, never from a pink system card or foreign key alone. |
| Bounded context | A boundary within which language and a model have consistent meaning. It does not prescribe a service, database, or deployment. |
| Claim / evidence | An interpretation versus the material supporting or challenging it. Integrity of evidence does not establish truth of the interpretation. |
| Observation / intention | What happened under recorded conditions versus what stakeholders want to happen. Keep implementation rules and intended policy distinguishable. |
| Invariant / precondition / outcome | What must remain true, what permits an action, and what follows it. Examples are evidence for these, not substitutes for their definitions. |
| Chronology / causality | Appearing later does not establish causation. An edge must identify its actual meaning. |
| Unknown / excluded / N/A | Unanswered, intentionally outside the declared scope, or demonstrably inapplicable. None means experimentally verified. |
| Consistency / completion | Immediate atomic behavior, eventual effects, and user-visible completion may differ. Model all applicable clocks and outcomes. |

Do not turn bug-compatible behavior into intended policy silently. Record the observed behavior and the decision about whether it belongs in a future contract separately.

## Portable meaning

Capture identity and equality, defaults, absence versus null, units, precision and rounding, time zones and business calendars, ordering, history, archive/delete/merge semantics, partial failure, and external contracts when they affect behavior. Read models include what a user must know to decide; manual conversations may need flexible ordering and explicit termination rather than a forced sequence.

Framework classes, routes, and storage models are evidence adapters. The domain specification should remain understandable if those disappear. A portable specification includes glossary, process narratives, decision tables, state machines, examples, and independent conformance scenarios. Passing one clean-room slice demonstrates portability of that slice only.

## Sources and attribution

These are paraphrased operational principles informed by the following original sources, read 2026-09-05. No endorsement or certification is implied. The recursive queue and integrity checker are this plugin's additions.

- [Brandolini, Introducing EventStorming](https://ziobrando.blogspot.com/2013/11/introducing-event-storming.html). Collaborative domain exploration and the warning against pursuing exhaustive detail during the workshop.
- [Avanscoperta, EventStorming](https://www.avanscoperta.it/en/eventstorming/). Big Picture, Process Modelling, and Software Design.
- [Brandolini, Collaborative Process Modelling](https://medium.com/@ziobrando/collaborative-process-modelling-with-eventstorming-17ed363650c0). Question policies with always/immediately, challenge scope, and preserve different modeling styles.
- [Extract Acceptance Tests](https://www.eventstorming.com/patterns/extract-acceptance-tests/). Make action/event examples and expected states unambiguous.
- [Conversational System](https://www.eventstorming.com/patterns/conversational-system/). Represent non-sequential activity and termination without infinitely unfolding loops.
- [Deliverable Obsession](https://www.eventstorming.com/patterns/deliverable-obsesssion/). Preserve collective learning while producing further artifacts when the task needs them.
