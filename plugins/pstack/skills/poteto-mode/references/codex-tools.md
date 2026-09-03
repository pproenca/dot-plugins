# Codex tool contract

Read this reference before a pstack workflow uses a plan or collaboration tool in Codex. The tool schemas and developer instructions exposed in the current turn are the source of truth. A tool can be disabled, omitted for the current mode, or exposed under a namespace.

## Plan with the tools that exist

- If `update_plan` is available and the session is not in Plan mode, use it for the workflow phases.
- If `update_plan` is absent, keep the same phase list in a normal progress update and continue. Do not invent a plan tool call.
- In Plan mode, follow the active Plan mode instructions. `update_plan` does not enter Plan mode and Codex rejects it there.
- Use `request_user_input` only when the current mode exposes it and the decision needs the user. Otherwise ask one concise question or proceed with a reasonable reversible choice.

## Use Codex collaboration v2 directly

Call collaboration tools directly with the namespace shown in the current turn. Do not call them inside `functions.exec`, through a shell command, or through a guessed namespace.

The Codex v2 workflow is:

1. Call `spawn_agent` with a unique lowercase `task_name` and a self-contained `message`.
2. Set `fork_turns` to `"none"`, `"all"`, or a positive integer string. The default is `"all"`.
3. Omit `model` and `reasoning_effort` unless the visible schema exposes them and pstack has a validated override. A full-history fork cannot use model or reasoning overrides, so set `fork_turns` to `"none"` or a positive integer when an override is required.
4. Use `send_message` to queue context without starting a turn. Use `followup_task` to give an idle agent more work or queue the next task for a running agent.
5. Use `list_agents` for current status. Use `wait_agent` only when it is available and the next local step needs an agent result. In v2, `wait_agent` takes an optional timeout and no target list. It returns a mailbox summary, while agent messages and final results arrive separately.
6. Use `interrupt_agent` to stop the current turn. The agent remains available afterward. Codex v2 has no `close_agent` or `resume_agent` operation.

Spawn independent tasks together, then do non-overlapping local work. Do not poll agents that are still working. Every agent shares the parent filesystem and current working directory. Read-only workers can share the checkout. Give writing workers disjoint paths or separate worktrees, and pass each worktree path in the task message.

## Handle unavailable collaboration

Use collaboration only when `spawn_agent` is exposed and the active instructions authorize delegation. A pstack skill that explicitly requires agents supplies workflow intent, but it does not override a developer instruction that disables delegation.

If collaboration is unavailable, continue locally when one agent can still satisfy the request. If independence or parallel coverage is part of the success predicate, mark that gate `INCONCLUSIVE` or `BLOCKED` and name the missing capability. Never claim a multi-agent review that did not run.

On another host, use that host's visible equivalents for spawning, messaging, waiting, and status. Keep the same ownership and verification rules. Do not send Codex-specific fields to a different host.
