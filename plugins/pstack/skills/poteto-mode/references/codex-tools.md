# Codex collaboration contract

Use the tools and permissions exposed in the current turn. Their descriptions govern parameters, availability, context inheritance, and side effects.

## Delegate by outcome

Give workers a bounded outcome, relevant paths and revision, write ownership, acceptance evidence, and constraints that could invalidate the result. Include phase exclusions directly in the brief. Supply only the skill references their assignment needs; workers should not restart the parent workflow.

For bounded assignments, prefer a self-contained brief with `fork_turns: "none"`. Inherit selected turns or full history when the assignment needs that context. Follow the live tool schema.

Choose workers by independent outcomes, not by available slots. The concurrency limit is a ceiling; run larger justified panels in waves. Keep coupled edits with one owner and start dependent writers from the completed prerequisite revision. Read-only workers can share a checkout; concurrent repository writers need separate worktrees and branches. Artifact-only workers can use distinct output directories. A branch name alone does not isolate files. Shared browsers, servers, and other mutable resources need one owner or separate instances too.

## Keep agent work in durable locations

Use the user's checkout for local work. When isolation is needed, use the host's managed worktree location or the repository's established convention. Otherwise create a sibling worktree at `<repository-parent>/<repository-name>-worktrees/<task-slug>/`. Resolve and pass the absolute working directory to every worker, and require its commands to use that directory.

Keep source edits, prototypes, candidate implementations, reports, and verification evidence in the assigned checkout or a durable project output directory. Artifact-only workers can use `<project-root>/artifacts/<task-slug>/worker-<n>/`, following the project's conventions for generated files. Do not use `/tmp`, `/private/tmp`, `$TMPDIR`, or another operating-system temporary directory as an agent workspace or the only copy of its deliverables. Disposable tool caches and test scratch files may remain temporary. A user-requested temporary experiment is an explicit exception.

If a durable destination needs additional permission, request it instead of substituting a temporary workspace. If existing work is already in a temporary worktree, coordinate with its owner and preserve its changes before moving it with Git; never move a directory underneath an active worker.

## Coordinate ongoing work

Continue local work while agents run. Use current message and follow-up tools to steer them, preserving accepted constraints. When a result becomes a dependency, use completion notifications or a bounded wait; do not repeatedly list agents or poll report files. Check progress when there is evidence of a stall or a decision needs it. Inspect completed artifacts before integrating. Reuse an agent for related work when its context remains useful; start fresh for independent review or substantially different scope.

Give reviewers a distinct risk or the requested comparison rubric. Reuse them to check fixes against their findings and the changed diff. Add review for uncovered risks, unresolved disagreements, or an explicit requirement. Preserve independent review without repeating generic passes over settled questions.

When delegation is unavailable, ordinary work proceeds locally. Workflows whose purpose is independent candidates or review must report the missing independence instead of claiming it occurred. They may still prepare the brief, evidence, or a clearly labeled local assessment.

## Choose models and reasoning

Read relevant roles from `~/.codex/pstack-models.md` if it exists. Missing roles, `inherit-parent`, `auto`, and unavailable values omit both overrides. Preserve the user's model choices. Validate explicit model and effort values against the current collaboration metadata before each dispatch; another host's accepted values are not evidence here.

Inherit the parent settings by default, including when the parent uses GPT-6 Astra. When the user requests tuning, or a configured role calls for it, use these starting heuristics within the advertised choices:

| Work | Effort to consider |
|---|---|
| Bounded lookup, extraction, or mechanical edit with a clear check | `low` |
| Routine implementation or investigation with several constraints | `medium` |
| Ambiguous design, difficult diagnosis, or consequential correctness review | `high` |
| Hard unresolved work after a lower-effort attempt, or an explicit user preference | Supported levels above `high` |

These are workload heuristics, not measured performance claims. Keep a deliberate cheaper-model role for simple work. Higher effort does not require more agents, more output, or broader tests. Compare representative outcomes, latency, and usage before promoting a new default. Do not assume every model supports every effort; in particular, do not use `none` or `minimal` for Astra.

With the current `spawn_agent` interface, explicit model or reasoning overrides require `fork_turns: "none"` or a supported numeric history count and a self-contained brief. Full-history forks inherit parent settings. Follow the live schema if it changes. A skill cannot change the active parent's model or reasoning through prose; child overrides and user-selected parent settings are separate controls.

Report the models that actually ran when diversity matters. Independent workers on one model provide same-model review. Different effort levels do not establish model diversity. Validate findings by evidence and impact, not vote count.

## Use Codex task capabilities

Use collaboration agents for subtasks within the current request. Create a separate user-facing Codex task only when the user explicitly asks for one. Use task history and status tools for a requested handoff or pickup, and bounded waits when following an existing task.

Use the current planning capability when it helps track dependencies. Otherwise give concise progress updates. Create a goal only on an explicit goal request. Scheduling a later continuation is distinct from working autonomously during the current turn.

## Schedule follow-ups

For requested recurring work, monitoring, or later follow-ups, create or update a matching thread heartbeat with the available automation tool. Follow its schema and the requested cadence. Stay quiet while nothing meaningful changes unless the user asks for periodic updates. Notify on a meaningful result, failure, or required action and stop the automation at its finish condition.

If scheduling or a required persistent webhook capability is absent, state the gap. Do not claim future wakeups or substitute independent tasks for a persistent bot without the user's agreement.

## Load routed skills

Read routed skills when their workflow applies. Reuse unchanged guidance already available in context; re-read when it changed, is unavailable, or a newly relevant section is needed. Apply the same rule to plans and model-role configuration instead of reloading them for every dispatch.
