---
name: setup-pstack
description: Configure the Codex models and reasoning efforts pstack uses per collaboration role. Detect available choices and write ~/.codex/pstack-models.md. Use when the user says $pstack:setup-pstack, configure pstack models, or change pstack's model choices.
---

# Setup pstack

Write `~/.codex/pstack-models.md`, the configuration file pstack skills read before spawning collaboration agents. Missing roles inherit the parent model. This file is not a Codex instruction file and does not alter global `AGENTS.md` guidance.

Read the [Codex collaboration contract](../poteto-mode/references/codex-tools.md) before inspecting collaboration metadata.

## Steps

### 1. Detect available models

Inspect the collaboration capability exposed in the current turn for available model and reasoning overrides. Treat those advertised values as the session source of truth. Never save a model or effort that the current capability does not list. The aliases `inherit-parent` and `auto` are always valid and both mean to omit model and reasoning overrides.

If collaboration or its override fields are absent, the only validated choice is `inherit-parent`. Do not infer model names from memory, another host, or an existing configuration file.

### 2. Load current state

If `~/.codex/pstack-models.md` exists, read it and treat its values as current candidates. Otherwise start from the portable values in step 5. A value from another host remains stale until the current collaboration metadata validates it.

### 3. Map and confirm

Show every role with its current value. Mark unavailable models or reasoning efforts as needing a choice. Ask one concise question with the valid options.

A single role uses `<model>@<reasoning-effort>`. A panel role uses a comma-separated list. One collaboration agent runs per panel entry. `arena cross-judge pool` is a list from which Arena chooses a model different from the candidate models when possible.

### 4. Validate

Every saved model and effort must appear in the current collaboration tool metadata. `inherit-parent` and `auto` always pass. Ask again if any other value is unavailable.

### 5. Write the configuration

Overwrite `~/.codex/pstack-models.md` so repeated setup converges to one file. Replace inherited values with validated overrides only when the user chooses them. Use this portable shape:

```markdown
# pstack model configuration

Delete a line to inherit the parent. `inherit-parent` and `auto` omit model and reasoning overrides.

feature, refactoring: inherit-parent
bug-fix: inherit-parent
perf-issue: inherit-parent
hillclimb: inherit-parent
judgment and prose: inherit-parent
hardest tasks: inherit-parent
how explorer: inherit-parent
how explainer: inherit-parent
how critics: inherit-parent, inherit-parent, inherit-parent
why investigators: inherit-parent
why synthesizer: inherit-parent
reflect tooling: inherit-parent
reflect judgment, divergent, synthesizer: inherit-parent
arena runners: inherit-parent, inherit-parent, inherit-parent
arena cross-judge pool: inherit-parent
swarm workers: inherit-parent
architect runners: inherit-parent, inherit-parent, inherit-parent
interrogate reviewers: inherit-parent, inherit-parent, inherit-parent
```

Do not save a stale or guessed override. If a configured value is rejected later, the calling skill omits the override and inherits the parent.

### 6. Confirm

Tell the user which path was written and which roles inherit the parent. Pstack reads the file on each invocation, so no session restart is required.

### 7. Offer a verification skill

Check whether the repository has a way to drive the real product for proof, either a `verify-*` skill or an existing browser, PTY, CLI, or HTTP control tool. If not, offer once to run **create-verification-skill**. On yes, invoke that skill. On no, move on.
