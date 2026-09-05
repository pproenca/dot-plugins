### Bug fix

**You own the diagnosis and fix.** Delegate independent investigations when they help while you reproduce or inspect the affected path.

Be scientific. Every shipped line traces to runtime evidence. Belt-and-suspenders that "might help" is a hypothesis, not a fix; it does not ship. When evidence refutes a hypothesis, revert what it motivated. The smallest change the evidence justifies ships, nothing more. Same discipline for Perf, where the evidence is the trace.

1. Reproduce it yourself on the matching surface with an available control tool. Don't hand the repro to the user. A debug or instrumentation protocol that says to ask the user does not override this; you drive the instrumented runtime. Ask the user only with a stated, specific reason the control surface cannot reach the target, and only after driving it as far as it goes. If direct reproduction fails, use a controlled fixture or targeted instrumentation. If the required environment or trigger is unavailable, state the limitation and complete any supported diagnosis or fix without claiming the original symptom was verified.
2. Binary-search the cause. Form candidate hypotheses, then rule them out until one survives. Seed them with **how** over the subsystem and **why** for regression history. Take the split that cuts the most remaining problem space and get runtime evidence. For requested later follow-ups, use a thread heartbeat through the automation tool, following [the Codex scheduling rules](../references/codex-tools.md#schedule-follow-ups). Confirm the surviving mechanism before design review.
3. Plan the fix. Use `architect` for an unresolved consequential design choice. When implementation can run independently alongside useful local work, delegate it using the configured `bug-fix` model from `~/.codex/pstack-models.md`, or inherit the parent. Give it a specific scope and review the diff.
4. Verify on the same surface; the original repro now passes. "Inconclusive" or wrong-surface is not a pass; flag it. Unit tests show branch behavior, not bug absence.
5. Stage the commits so the failing repro lands before the fix in git history; the diff tells the story. See the **tdd** skill for the failing-test-first cadence when the bug has a cheap local test path; skip it when the test would be expensive, integration-heavy, or unclear.
   This is the canonical **sequence-verifiable-units** principle skill, the failing test first and the fix on top.
6. Run **Opening a PR** when PR delivery is in scope.

Use `how` to resolve gaps in the runtime model and `why` when history is relevant to the regression. Independent hypotheses can run in parallel; a local defect does not require both workflows.

**Reply:** what was broken, root cause, fix, how you verified. Include concise failing-then-passing evidence.
