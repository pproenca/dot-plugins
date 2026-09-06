---
name: how
description: "Explain subsystem behavior, runtime flow, and code ownership. Use for code walkthroughs or architecture questions."
---

# How

Trace the code to explain how a subsystem works. Use Explain mode for walkthroughs and Critique mode when the user asks for architectural problems or improvements.

## Trace the question

Identify the requested behavior and relevant revision. Resolve routine ambiguity from the available context and state an assumption when it changes the answer. Find an entry point and follow its data, state transitions, and callers through the owning modules. Read the implementation; names alone are not evidence.

Start locally with a bounded trace. Delegate an independent slice when parallel exploration can save time or improve confidence while you trace another part. Multiple files or services alone do not require a panel. Use a broader team when there are distinct unresolved questions that warrant it; do not repeat the same trace in the parent and every worker.

## Delegate useful exploration

Read the [Codex collaboration contract](../poteto-mode/references/codex-tools.md) before dispatch. Use the configured `how explorer` role when valid. A worker gets a read-only assignment with the question, revision, entry points, known evidence, exclusions, and the gap it should resolve. Use the [explorer brief](references/explorer-prompt.md), loading only references that change the assignment.

Ask for the relevant flow, ownership, source locations, and unresolved gaps. Reuse the findings and verify consequential claims against the source. Give a follow-up to the same worker when its context is useful. Stop exploration when the requested behavior is explained or the remaining uncertainty is precise.

## Explain

Synthesize in the lead's existing context. A separate explainer is useful only when its work can run alongside another necessary task; use the configured `how explainer` role in that case. The [explanation guidance](references/explainer-prompt.md) is available when the audience or structure needs it.

Lead with what the subsystem does, then explain the path from trigger to result and the concepts needed to understand it. Cite the owning files and important boundaries. Include gotchas that affect use or maintenance, and distinguish observed behavior from inference. A narrow question needs a short answer; a broad onboarding explanation may need a flow diagram and a map of components.

## Critique

Establish the behavior before judging the design. Reuse the trace and evidence for review instead of asking reviewers to rediscover the subsystem.

For an ordinary critique, use one independent reviewer with the [critique rubric](references/critique-rubric.md) and [reviewer brief](references/critic-prompt.md). Select a valid profile from `how critics`. Add reviewers for uncovered consequential risks, unresolved disagreement, or an explicit request for a broader panel or model diversity. Give each an independent question and source scope. A configured list supplies profiles; its length does not require that many reviewers on every task.

Reviewers are read-only and must connect each actionable issue to a concrete consequence. Check findings against the source, reject unsupported concerns, and reuse reviewers for their findings and subsequent changes. Use the models advertised by the host and report the ones that actually ran when diversity matters. Same-model review provides independence, not model diversity.

Present your judgment with reasons: changes worth making now, tradeoffs needing a decision, and consequential limitations. If independent review is unavailable, provide a local assessment and mark independent critique `INCONCLUSIVE`.
