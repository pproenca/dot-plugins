---
name: swarm-forge-handoffs
description: The SwarmForge handoff protocol — how an agent inside a swarm queues work with swarm_handoff.sh, accepts it with ready_for_next.sh, completes it with done_with_current.sh, and asks a human for clarification. Use when writing role prompts, debugging stalled handoffs, or acting as a role in a swarm.
---

# SwarmForge handoffs

This is how agents inside a swarm pass work to each other. It matters in two situations:
you are writing or editing a `roles/<role>.prompt`, or a swarm has stalled and you need to
know what the helpers should have done.

Agents never touch tmux and never message each other directly. The `handoffd` daemon owns
the tmux socket; it watches each agent's outbox, validates and copies files into recipient
inboxes, and sends only a generic wake-up. Everything else is files on disk.

The helpers are on every agent's `PATH` — the launcher copies the engine's scripts into
each worktree at `swarmforge/scripts/` and prepends it.

## Sending

Write a draft file containing only headers, then queue it:

```bash
swarm_handoff.sh <draft-file>
```

Two message types, and no others.

**`git_handoff`** — points the recipient at committed state. Commit first.

```text
type: git_handoff
to: <role>[,<role>...]
priority: NN
task: <short-stable-task-name>
commit: <10-character-commit-abbrev>
```

The commit abbreviation must be exactly 10 hex characters. `swarm_handoff.sh` checks that
it resolves to a single commit and canonicalizes it before queuing.

**`note`** — one short freeform line, max 80 characters.

```text
type: note
to: <role>[,<role>...]
priority: NN
message: <one line>
```

Send a `note` only when the user, the role prompt, or the constitution explicitly directed
one. When blocked by ambiguity or a contradiction, ask for clarification instead — do not
improvise a `note`.

`task:` must reuse the name already on the board card. Do not invent a new one; the board
tracks cards by that name.

The helper generates the delivered payload. Agents do not write long bodies, branch names,
queue filenames, SHAs beyond the abbrev, or tmux commands.

## Receiving

```bash
ready_for_next.sh
```

Run it when woken, and after a restart. It dispatches to the task or batch helper
configured for the role and prints one of:

- `NO_TASK` — nothing queued. Stop waiting for work.
- `TASK: <path>` — treat the printed `TASK_NAME` and `PAYLOAD` as the task.
- `BATCH: <path>` — process the printed `BATCH_ITEM` entries in the order given.

A wake-up arriving mid-work can be ignored; `done_with_current.sh` checks for the next item
after completing the current one.

## Completing

```bash
done_with_current.sh
```

Stamps completion, moves the work to `completed/`, and immediately checks for the next task
or batch.

## Asking a human

```bash
pack_dashboard_request.sh clarify <question-file>
```

The question surfaces in the cockpit's Attention panel, and the operator's answer is
injected into the asking agent's pane. This is the sanctioned way to block on a human —
better than a `note` to another agent, which cannot answer.

## Runtime state

Per worktree, under `.swarmforge/handoffs/`:

```text
outbox/tmp   sent/   failed/   inbox/{new,in_process,completed}   pending_approval/
```

Never hand-edit, stage, or commit any of it. Drafts must be written into the helper's
designated temp location and queued through `swarm_handoff.sh` — writing directly into
`inbox/` bypasses validation and the board.

`failed/` is the first place to look when a handoff vanishes: it holds drafts that failed
validation, usually a malformed commit abbrev or an unknown recipient role.

The full protocol — filename format, header lifecycle, and who owns each field — is in
[references/handoff-protocol.md](references/handoff-protocol.md).
