### Autonomous run

**You own the exit condition. Define done, then drive to it without stopping.** For "going to bed", "run until done", or recurring work until X.

1. State the exit condition as a checkable predicate before the first iteration (tests green, repro fixed, all N PRs merged, pixel-diff zero). A vague goal stalls; a predicate lets you stop.
2. Pick the wake mechanism. An event such as CI, a merge, or a ref advancing gets a watcher. For requested recurring work or later follow-ups, use a thread heartbeat through the automation tool, following [the Codex scheduling rules](../references/codex-tools.md#schedule-follow-ups). Size the interval to when the result is worth re-checking.
3. Each iteration makes the smallest change the evidence justifies, verifies it against the predicate, commits if it advanced, discards changes that didn't help. Belt-and-suspenders that "might help" gets reverted, not left to ride.
   Sequence the work via the **sequence-verifiable-units** principle skill, verifying each unit before the next instead of batching checks at the end.
4. Fix discoveries that block the requested outcome or invalidate its evidence, using the relevant poteto-mode workflow. Record unrelated bugs, tooling improvements, or drift briefly and continue the requested work. Reversibility alone does not bring a side project into scope. Resolve routine prerequisites autonomously; preserve user approval boundaries for external or irreversible actions.
5. Checkpoint consequential progress and handoffs with the revision, changed behavior, acceptance evidence, and remaining work. Reuse the existing task record; use **show-me-your-work** when a durable review trail is needed. Do not copy unchanged status into every model turn.
6. Stop when the predicate is met. A plateau is not a stop, so keep going and pivot your approach to push past it. Surface a genuine dead end rather than spinning, and never relax the predicate to declare victory.

**Reply:** the exit condition, iterations run, what landed, what was discarded, final predicate state.
