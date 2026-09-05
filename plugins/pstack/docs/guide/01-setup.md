# Set up pstack

In this page you install the plugin, pick which models pstack uses, and run your first task. Setup is one command plus a short conversation.

## Install the plugin

In a terminal with the `dot-plugins` marketplace configured, run:

```text
codex plugin add pstack@dot-plugins
```

Codex confirms the plugin is installed. Start a new task after installation so it loads the skills.

## Pick your models

Run:

```text
$pstack:setup-pstack
```

[`$pstack:setup-pstack`](../../skills/setup-pstack/SKILL.md) detects the models and reasoning efforts exposed to collaboration agents, applies requested role choices, preserving the others. It writes `~/.codex/pstack-models.md`, which routed pstack skills read before delegating. If Codex hides model overrides, setup uses `inherit-parent` instead of guessing model names.

You only override what you care about. A role with no line inherits the parent model. To remove an override later, delete that role's line, or run `$pstack:setup-pstack` again.

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `$pstack:swarm` worker unless a race names a model for each arm.

## Tune reasoning when needed

Inherited settings work without a role file. For intentional overrides, start with low effort for bounded lookups or mechanical edits, medium for routine implementation, and high for unresolved design or correctness questions. Use higher supported levels when the task warrants them, then compare results and cost on representative work. These are starting heuristics, not benchmark results.

Setup validates each model and effort against the current host. It cannot change the active parent's reasoning level. See the [collaboration contract](../../skills/poteto-mode/references/codex-tools.md#choose-models-and-reasoning) for the full rules.

Pstack reads the model file on each invocation, so role changes do not require a restart.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
$pstack:poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the plan or progress updates for the requested behavior, consequential choices, and verification. The agent adapts the Feature playbook to this task without loading unrelated principles or copying every phase.

From here you can type normal follow-ups. `$pstack:poteto-mode` is sticky. It stays on for the conversation until you opt out by saying so.

Next: [Route work through `$pstack:poteto-mode`](./02-poteto-mode.md).
