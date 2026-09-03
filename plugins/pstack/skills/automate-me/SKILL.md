---
name: automate-me
description: "Use when \"automate me\", \"create/update/refresh my -mode skill\", \"turn/capture my preferences or working style into a skill\", or wanting agents to follow how the user works. Drafts or revises a personal -mode skill via skill-creator and unslop, optionally pulling fresh evidence from recent transcripts."
metadata:
  disable-model-invocation: "true"
---

# Automate me

A guided flow for turning the user's working conventions into a skill agents will follow. The output is one `-mode` skill tailored to them (e.g. `jay-mode`, `priya-mode`).

This skill orchestrates three others: an inline mining pass, the built-in **skill-creator** skill, and **unslop**. It sequences them; it does not replace them.

Before spawning Codex history readers, read the [Codex tool contract](../poteto-mode/references/codex-tools.md). If `spawn_agent` is unavailable, mine the scoped history locally and note that cross-slice independence was unavailable.

## Flow

### 0. Check for an existing skill

Look recursively for `.agents/skills/**/*-mode/SKILL.md` and `~/.agents/skills/*-mode/SKILL.md` matching the user's handle. If one exists, confirm intent with `request_user_input` when available, unless the user already asked to update it:

- Update the existing skill (default for repeat runs)
- Start fresh (rare; ask why before doing it)

Update mode changes the rest of the flow:
- Step 1 mines only history since the skill was last edited (`git log -1 --format=%cI <path>`).
- Step 2 asks what's changed or missing, not what to capture from zero.
- Step 4 edits the existing file in place. Preserve sections the user hasn't contradicted; revise ones with new evidence; add new sections only for genuinely new rules.

### 1. Mine their history

List recent Codex tasks in the active workspace before fanning out. Use task tools to read only matching tasks. Never scan another workspace or unrelated local session logs.

Survey recent agent conversations within that scope for recurring patterns. Run multiple parallel subagents across slices of history (e.g. last 2-4 weeks, split into 3 slices so each has enough material). Each slice mining subagent reads transcripts from the workspace-scoped path the parent provides, looks for the signals below, and returns a short structured list of patterns it saw with evidence pointers. Default signals worth hunting:

- Response preferences (length, tone, format, "dumb it down" corrections)
- Delegation habits (subagents, models, specialized workflows, parallelism)
- Verification posture (what "done" means; unit tests vs live repro; reviewers)
- Code and prose discipline (style, principles cited, lint/format tools)
- Process conventions (worktrees, commits, PRs, review/merge tooling)
- Meta preferences (fixing skills mid-task, proposing new ones)

Cross-check across slices before elevating a signal. Patterns seen in 2+ slices are high-confidence; lone signals are weak and usually get dropped.

### 2. Ask the user directly

Mining misses intent that has not come up yet. Use `request_user_input` when available. Otherwise ask one concise question at a time.

Shape: one or two questions with two or three mutually exclusive options each. Start broad ("Which area matters most?"), then follow up on the selected area with specific options. Ask one free-form chat question afterward to catch anything the options missed.

Don't dump 20 questions. Two structured rounds plus one open question is usually enough.

### 3. Cluster findings

Group the combined signals into sections. Common ones (use only what applies):

- **Response style**: length, tone, format.
- **Autonomy**: how much to do without asking; MCP tool use.
- **Understand first**: which skills to reach for when scoping or investigating a change.
- **Subagents**: default, parallelism, model-to-task, specialized workflows.
- **Prose / code discipline**: principles, lint tools, style guides.
- **Review and verify**: repro posture, verification skills, live-testing tools.
- **Process**: git worktrees, commits, PRs, review/merge tooling.
- **Skills**: skill-authoring habits, fix-the-skill-first, proposing new skills.

The **poteto-mode** skill shows the shape. Read it for granularity. Don't copy its content; the user's rules are not the same as poteto-mode's.

### 4. Draft the skill

Use the built-in **skill-creator** skill to author the skill. Placement:

- Path: preserve an existing skill's scope. For a new repository skill, use `.agents/skills/<handle>-mode/SKILL.md`. For a personal skill, use `~/.agents/skills/<handle>-mode/SKILL.md`.
- Handle: the user's first name or chosen identifier.
- Frontmatter `description`: trigger on their name + `/<handle>-mode` + "work in their style", not on generic keywords like "write code" or "review PR".
- Frontmatter formatting: follow **skill-creator**'s YAML rules. Keep `description` as one YAML scalar; quote it or use `description: >-` with indented continuation lines when punctuation or wrapping requires it.
- Frontmatter `metadata.disable-model-invocation: "true"` by default. Mode skills are heavy and opinionated; they should only apply when the user explicitly invokes them (by name or slash command), not auto-trigger on description matching. Opt out only if the user explicitly wants their mode to apply on every turn. Agent Plugins closes the frontmatter field set, so client-specific keys go under `metadata` as strings; a client that reads only the top-level key will not honor it.

### 5. Iterate on prose

Apply the **unslop** skill and **skill-creator**'s writing guidelines to every line. Both apply to any agent-read prose, not just skills.

Show the draft to the user and take feedback. Expect multiple iterations. Cut ruthlessly; a mode skill is not a manual.

### 6. Land it

Work in a worktree off main. Commit and open a PR so the user can review it. Don't push to main directly.

## Guardrails

- **Don't overfit to one conversation.** A preference stated once and contradicted another time is noise. Require multiple instances before codifying it.
- **Don't be clever.** Restating other skills' contents, inventing metaphors, or writing "poetic" prose for an agent reader is cost without benefit. Keep it operational.
- **Reference, don't inline.** Other skills the user relies on should appear as path references, not pasted excerpts. Same for any principle docs they maintain elsewhere.
- **Keep sections minimal.** Only add a section if the user has a specific, non-default rule there. "Communicate clearly" is not a section. "Short paragraphs. Tables when comparing options. Bullets only when items are genuinely parallel." is.
- **Name conventions generic.** Use "the user" or "the human" in imperatives, not the author's first name. Others may read or adopt the skill.
- **Don't force symmetry.** If a user has no process rules worth writing down, skip the Process section entirely. Sparse is fine; bloated is not.

## Evaluation

A `-mode` skill is subjective output. A skill-creator benchmark loop is not useful here. Vibe-check with the user: does it read like them? Did it miss anything? Then ship.

Run a description-optimization loop only if the skill's trigger accuracy turns out to be a problem in practice.

## When not to use

- User wants a task-specific skill, not working conventions: use **skill-creator** alone, with no mining pass.
- User wants to capture one narrow workflow (e.g. "how I write commit messages"): that's a regular skill, not a mode skill.

## Reference files

- The **poteto-mode** skill: example of the output shape.
- The **unslop** skill: prose discipline for every line.
- The built-in **skill-creator** skill: skill authoring process and writing guidelines.
