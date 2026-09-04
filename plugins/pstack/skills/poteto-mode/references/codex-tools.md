# Codex collaboration contract

Use only the planning, questioning, and collaboration capabilities exposed in the current turn. Current tool descriptions and higher-priority instructions are authoritative. Never guess a missing operation, namespace, or field.

## Keep workflow state visible

- Keep the workflow phases visible throughout the run. Use the current mode's planning capability when available. Otherwise maintain the same phase list in progress updates.
- Ask one concise question only when a product or preference decision cannot be settled through inspection or a reversible experiment.
- Create a goal only when the user explicitly requests a goal. An execution go does not imply that request. Otherwise keep the finish condition in the plan or progress updates.

## Schedule follow-ups

When the user requests recurring work, monitoring, or a later follow-up, use the available automation tool to create or update a thread heartbeat. Reuse a matching automation and follow its current schema. If scheduling is unavailable, report that limitation without claiming future wakeups.

Keep the heartbeat quiet while nothing meaningful changes, unless the user requests periodic status updates. Notify on meaningful progress, completion, failure, or required user action. Stop the automation when its finish condition is met.

## Load routed skills explicitly

Codex does not recursively load another skill because the current skill names it. When one pstack skill routes to another, resolve the routed skill's `SKILL.md` path and read it in full before following it. Do not assume that a bold name or prose mention injected the routed skill body.

## Delegate by outcome

- A workflow that requires independent agents must say so explicitly. If the turn does not permit delegation, follow the workflow's declared local fallback or mark its independence gate `BLOCKED` or `INCONCLUSIVE`.
- Start independent work in one wave. Give every worker a unique task name and a self-contained brief.
- Continue non-overlapping local work while workers run. Check worker status only when needed. Wait only when the next step requires a result.
- Codex collaboration agents share the parent filesystem and working directory. Give every worker that writes inside the repository its own worktree and branch. Workers that write only external artifacts may use unique output directories. Read-only workers may share the checkout.
- Use the current collaboration descriptions for context inheritance, messages, follow-up work, status, waiting, and interruption.
- Delegate only concrete, independent work that can run alongside useful local work. Scale worker counts and verification to the task. Do not add review waves or repeat passing checks without an unresolved concern.

## Validate model choices

Use only model and reasoning overrides advertised by the current collaboration capability. Omit overrides when no validated choice exists so the worker inherits the parent settings. Never reuse an override merely because another host or an older session accepted it.

When using `spawn_agent` with a model or reasoning override, set `fork_turns` to `"none"` or a supported numeric history count and provide a self-contained brief. Omitted `fork_turns` and `"all"` inherit the parent settings and cannot accompany overrides. Follow the current schema if these options change.

Report the models that actually ran. Independent reviewers using the same model are same-model review, with model diversity `INCONCLUSIVE`. Different reasoning efforts alone do not establish cross-model diversity.
