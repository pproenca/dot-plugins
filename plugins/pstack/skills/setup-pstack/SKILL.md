---
name: setup-pstack
description: Configure the Codex models and reasoning efforts pstack uses per collaboration role. Detect available choices and write ~/.codex/pstack-models.md. Use when the user says /setup-pstack, configure pstack models, or change pstack's model choices.
---

# Setup pstack

Write `~/.codex/pstack-models.md`, the configuration file pstack skills read before spawning collaboration agents. Missing roles inherit each skill's default. This file is not a Codex instruction file and does not alter global `AGENTS.md` guidance.

## Steps

### 1. Detect available models

Read the model names and supported reasoning efforts exposed by the current collaboration tools. That is the source of truth for this session. Never save a model or effort that the tool does not list. The aliases `inherit-parent` and `auto` are always valid and both mean to omit model and reasoning overrides.

### 2. Load current state

If `~/.codex/pstack-models.md` exists, read it and treat its values as current. Otherwise start from the defaults in step 5.

### 3. Map and confirm

Show every role with its current value. Mark unavailable models or reasoning efforts as needing a choice. Use `request_user_input` when available. Otherwise ask one concise question with the valid options.

A single role uses `<model>@<reasoning-effort>`. A panel role uses a comma-separated list. One collaboration agent runs per panel entry. `arena cross-judge pool` is a list from which Arena chooses a model different from the candidate models when possible.

### 4. Validate

Every saved model and effort must appear in the current collaboration tool metadata. `inherit-parent` and `auto` always pass. Ask again if any other value is unavailable.

### 5. Write the configuration

Overwrite `~/.codex/pstack-models.md` so repeated setup converges to one file. Use this shape:

```markdown
# pstack model configuration

Delete a line to use the skill default. `inherit-parent` and `auto` omit model and reasoning overrides.

feature, refactoring: gpt-5.6-luna@high
bug-fix: gpt-5.6-sol@max
perf-issue: gpt-5.6-sol@max
hillclimb: gpt-5.6-sol@max
judgment and prose: gpt-5.6-sol@xhigh
hardest tasks: gpt-5.6-sol@max
how explorer: gpt-5.6-luna@high
how explainer: gpt-5.6-terra@xhigh
how critics: gpt-5.6-sol@max, gpt-5.6-terra@xhigh, gpt-5.6-luna@high, gpt-5.5@xhigh
why investigators: gpt-5.6-luna@high
why synthesizer: gpt-5.6-sol@xhigh
reflect tooling: gpt-5.6-terra@high
reflect judgment, divergent, synthesizer: gpt-5.6-sol@xhigh
arena runners: gpt-5.6-sol@max, gpt-5.6-terra@xhigh, gpt-5.6-luna@high, gpt-5.5@xhigh
arena cross-judge pool: gpt-5.6-sol@max, gpt-5.6-terra@xhigh, gpt-5.6-luna@high, gpt-5.5@xhigh
swarm workers: gpt-5.6-luna@high
architect runners: gpt-5.6-sol@max, gpt-5.6-terra@xhigh, gpt-5.6-luna@high, gpt-5.5@xhigh
interrogate reviewers: gpt-5.6-sol@max, gpt-5.6-terra@xhigh, gpt-5.6-luna@high, gpt-5.5@xhigh
```

If any example default is unavailable, replace it with a detected equivalent before writing. Do not save a knowingly invalid default.

### 6. Confirm

Tell the user which path was written and which roles inherit the parent. Pstack reads the file on each invocation, so no session restart is required.

### 7. Offer a verification skill

Check whether the repository has a way to drive the real product for proof, either a `verify-*` skill or an existing browser, PTY, CLI, or HTTP control tool. If not, offer once to run **create-verification-skill**. On yes, invoke that skill. On no, move on.
