---
name: reflect
description: "Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect."
metadata:
  disable-model-invocation: "true"
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Before spawning Codex reviewers, read the [Codex tool contract](../poteto-mode/references/codex-tools.md). If `spawn_agent` is unavailable, report `BLOCKED`. Independent reviewers are part of this skill's evidence, not optional ceremony.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

Use the current Codex task history when the task tools expose it. If the environment provides an exact local transcript path for this task, use only that file. Never scan another workspace or glob across the Codex home directory.

```bash
ls -t <agent-transcripts>/*.jsonl <agent-transcripts>/*/*.jsonl <agent-transcripts>/*/subagents/*.jsonl 2>/dev/null | head -10
```

Three transcript layouts: legacy flat (`<id>.jsonl`), current nested (`<id>/<id>.jsonl`), and subagent (`<parent>/subagents/<child>.jsonl`).

For each candidate, read the first JSONL line and check that `message.content[0].text` contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

Spawn three collaboration reviewers together with explicit valid models when configured. Their prompts forbid file writes. They may use available connectors for cited context lookups. The parent applies accepted edits.

| Lens | `model` | Prompt template |
|---|---|---|
| Judgment | your configured reflect-judgment model, or inherit parent | `references/judgment-reviewer.md` |
| Tooling | your configured reflect-tooling model, or inherit parent | `references/tooling-reviewer.md` |
| Divergent | your configured reflect-judgment model, or inherit parent | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Collect each reviewer's final response from the collaboration mailbox.

### 3. Synthesize

Spawn one collaboration synthesizer using the configured `reflect judgment, divergent, synthesizer` model when valid. Its prompt forbids writes but allows available connectors for citation checks. Use `references/synthesizer.md` verbatim with reviewer outputs inserted where marked. It returns Accepted, Rejected, and Backlog lists.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically. Those are tracker submissions, not skill edits. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit: hand it to **skill-creator** and run its draft, validate, and iterate loop.
- `tune description: <skill path>`: hand it to **skill-creator** and test realistic trigger prompts.
- `new skill via skill-creator: <kebab-name>`: hand creation to **skill-creator**. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
