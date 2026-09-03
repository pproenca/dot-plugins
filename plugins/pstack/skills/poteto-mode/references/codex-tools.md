# Codex collaboration contract

Use only the planning, questioning, and collaboration capabilities exposed in the current turn. Current tool descriptions and higher-priority instructions are authoritative. Never guess a missing operation, namespace, or field.

## Keep workflow state visible

- Keep the workflow phases visible throughout the run. Use the current mode's planning capability when available. Otherwise maintain the same phase list in progress updates.
- Ask one concise question only when a product or preference decision cannot be settled through inspection or a reversible experiment.

## Load routed skills explicitly

Codex does not recursively load another skill because the current skill names it. When one pstack skill routes to another, resolve the routed skill's `SKILL.md` path and read it in full before following it. Do not assume that a bold name or prose mention injected the routed skill body.

## Delegate by outcome

- A workflow that requires independent agents must say so explicitly. If the turn does not permit delegation, follow the workflow's declared local fallback or mark its independence gate `BLOCKED` or `INCONCLUSIVE`.
- Start independent work in one wave. Give every worker a unique task name and a self-contained brief.
- Continue non-overlapping local work while workers run. Check worker status only when needed. Wait only when the next step requires a result.
- Codex collaboration agents share the parent filesystem and working directory. Give every worker that writes inside the repository its own worktree and branch. Workers that write only external artifacts may use unique output directories. Read-only workers may share the checkout.
- Use the current collaboration descriptions for context inheritance, messages, follow-up work, status, waiting, and interruption.

## Validate model choices

Use only model and reasoning overrides advertised by the current collaboration capability. Omit overrides when no validated choice exists so the worker inherits the parent settings. Never reuse an override merely because another host or an older session accepted it.

Never claim that independent or cross-model review ran when it did not.
