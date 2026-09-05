# Verification, repair, and completion

## What the helper can establish

`audit` validates model structure, mandatory question coverage, local evidence hashes, dependency freshness, inventory accounting, scenario coverage, current recorded results, and review records. It does not execute UI/API scenarios, inspect remote deployments, prove predicates exhaustive, or authenticate the person who wrote a record. Its positive result is named `recorded_checks_satisfied` deliberately.

Validate semantic claims separately. A paragraph can exist and still omit a rule. A source hash can match and still describe an obsolete deployment. A falsely reported run can pass record-integrity checks. Record the limitation rather than describing any of these as a theorem about the domain.

## Required review responsibilities

- **Walkthrough:** actual participants narrate concrete examples, challenge definitions, verify their decision information, and resolve business meaning. Record who participated and where domain expertise was unavailable.
- **Blind inventory:** independently discover and reconcile business processes, human work, entry points, jobs, integrations, settings, and historical concepts. Record inspected sources, omissions, and access limits.
- **Challenge:** attempt counterexamples, mismatched assumptions across contexts, invalid states, and missing conditions. Inspect expected results independently of the model author.

Current passed review records are necessary bookkeeping gates; they cannot manufacture those activities. Do not create a passed review because an agent agrees with the map. Portability additionally requires an independent implementer using the specification without original implementation access and an independent conformance exercise. v0.1 does not have an automated portability gate.

## Scenario rigor

Describe initial conditions, actions, and exact expected state or observations. Include rejection/no-op results, boundaries, permissions, temporal effects, retries, and concurrency when relevant. Record invariant and decision-table references. Separate intended contract from observed compatibility behavior.

Deriving a model and its entire oracle from the same source proves transcription. The checker conservatively flags overlapping evidence lineages. Different lineages are only a candidate for independence; reviewers must inspect actual provenance. Hold out independently captured examples and deliberately alter behavior to confirm important tests turn red. A different agent reading the same source is not independent evidence.

Use finite input partitions and explicit bounds for generated sequences. Exhaustive checking of a finite state model establishes properties of that abstraction, not of all real executions. Record untested interactions. Avoid “100%” without the exact denominator, scope/version, method, exclusions, and unresolved obligations.

## Invalidation and safe recovery

On each accepted change and resume, run audit. Changed or missing captured files reopen claims and transitive dependents. A changed specification or obligation matrix invalidates recorded runs/reviews through the basis fingerprint. Current evidence integrity is still checked even if the stored basis matches. Any new runtime/remote discovery must first be captured; the helper has no remote watcher.

Repair is conservative and repeatable:

1. Preserve the current model with `checkpoint` and inspect the root failure.
2. Rebuild the report/frontier from source with `report`; those are disposable projections.
3. If source evidence changed, reinspect it and retain the previous capture/history. Amend claims only after assessing the semantic difference.
4. Reconcile conflicting proposals and regenerate affected scenarios. Rerun actual checks before recording replacement results.
5. When a tool is unavailable or an outcome remains ambiguous, leave the question open with the next required action.

Never heal by deleting a failing scenario, shrinking the inventory, changing an expected hash without reinspection, accepting a stale pass, relabeling an unknown N/A, or weakening the checker. Installed plugin files are not project memory.

## Completion vocabulary

Report mapped and excluded inventory separately. Report supported mandatory obligations separately from current passing scenarios. Unknown and contradicted claims prevent closure. Empty models cannot pass. Extra domain-specific aspects also remain subject to evidence and scenario review.

Treat full specification as a reviewed claim within a declared scope, and verification as current evidence under tested conditions. Periodic independent discovery can reopen both. Record exceptions honestly rather than converting the dashboard to one overall percentage.
