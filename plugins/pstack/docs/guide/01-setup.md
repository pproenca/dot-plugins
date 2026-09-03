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

[`$pstack:setup-pstack`](../../skills/setup-pstack/SKILL.md) detects the models and reasoning efforts exposed to collaboration agents, shows every role, and asks what you want. It writes `~/.codex/pstack-models.md`, which routed pstack skills read before delegating. If Codex hides model overrides, setup uses `inherit-parent` instead of guessing model names.

You only override what you care about. A role with no line inherits the parent model. To remove an override later, delete that role's line, or run `$pstack:setup-pstack` again.

You might be wondering what happens if you use Auto. Set a role to `inherit-parent` or `auto` and pstack omits the subagent `model` field, so the subagent inherits your parent chat model. Both values mean the same thing, and neither is a model slug. For a panel role the value is a list, and one subagent runs per entry, so the list length sets the panel size. Setup also configures `swarm workers`, the default model for every `$pstack:swarm` worker unless a race names a model for each arm.

## Accept the verification offer, or don't

At the end of setup, `$pstack:setup-pstack` looks for a way to prove app behavior in your project, either a `verify-*` skill or an existing harness. If it finds neither, it offers once to generate one with [`$pstack:create-verification-skill`](../../skills/create-verification-skill/SKILL.md).

Say yes and it writes `.agents/skills/verify-<app>/`, a repository-local skill that teaches agents to drive your app the way a user does. It proves the skill once before handing it over. Say no and setup moves on.

Pstack reads the model file on each invocation, so model changes do not require a restart.

## Run your first task

Pick something real but small, and describe it the way you'd describe it to a colleague:

```text
$pstack:poteto-mode add a --json flag to this command. text output stays byte-identical. verify both.
```

Watch the Codex plan or progress updates. The first phase is "read the Principles section". The rest are the matched playbook's steps, the Feature playbook for this prompt. If `$pstack:poteto-mode` skips a step, the step stays visible with `skip: <reason>`, so you can see what it chose not to do.

From here you can type normal follow-ups. `$pstack:poteto-mode` is sticky. It stays on for the conversation until you opt out by saying so.

Next: [Route work through `$pstack:poteto-mode`](./02-poteto-mode.md).
