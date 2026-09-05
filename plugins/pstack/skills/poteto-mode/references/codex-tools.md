# Codex collaboration contract

Use the tools and permissions exposed in the current turn. Their descriptions govern parameters, availability, context inheritance, and side effects.

## Delegate by outcome

Use collaboration agents for concrete independent work that can run alongside useful local work. A brief names the outcome, relevant paths, write ownership, constraints, and acceptance evidence. Give workers only the skill references their assignment needs; do not make each worker restart the parent workflow.

Launch independent work up to the available concurrency limit, counting the parent and active descendants. Run larger panels in waves. Keep coupled edits with one owner. Read-only workers can share a checkout; concurrent repository writers need separate worktrees and branches. Artifact-only workers can use distinct output directories. A branch name alone does not isolate files. Shared browsers, servers, and other mutable resources need one owner or separate instances too.

Continue local work while agents run. Use current message and follow-up tools to steer them, preserving accepted constraints. Wait when the next step needs their results. Inspect their artifacts before integrating. Reuse an agent for related work when its context remains useful; start fresh for independent review or substantially different scope.

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

Naming a skill does not load its body in Codex. Resolve and read a routed `SKILL.md` when that workflow applies. Reuse already loaded guidance and read only the supporting references needed for the current decision.
