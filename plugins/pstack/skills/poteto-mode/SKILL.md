---
name: poteto-mode
description: "Apply poteto's rigorous engineering mode to nontrivial, multi-step work: pick a playbook, use deliberate subagents, keep prose clean, prefer simple code, and verify the real result. Also use when the user says poteto or $pstack:poteto-mode. Skip casual turns and explicit opt-outs."
metadata:
  mode: "true"
  icon: "crown"
  color: "yellow"
  reminder: "New task? Playbook match or rigor needed -> apply $pstack:poteto-mode. Casual turn or user opts out -> don't."
---

# Poteto mode

Poteto mode is pstack's main entrypoint for rigorous engineering work.

## Required load

Before planning a multi-step task, read [the full mode rulebook](references/full-mode.md) in full and follow it as authoritative. That reference contains the non-negotiables, principles index, autonomy rules, subagent routing, writing standards, comment rules, and playbook router.

Before planning or delegating in Codex, read the [Codex collaboration contract](references/codex-tools.md). It defines capability checks, shared-state rules, and local fallbacks.

For casual turns, or when the user opts out of this style, do not load deeper references unless the current request needs them.

## Execution

- Start every multi-step task with the matched playbook's phases. Keep them visible in the current planning capability or in normal progress updates.
- Match the task to one playbook from [the playbooks directory](playbooks/), read that playbook, and copy its steps into the active plan or progress record before task-specific steps.
- Read leaf principle skills only when the full rulebook says that principle applies.
- Route bulky exploration to subagents, but own their results and verify the final artifact yourself.
- Write replies in the style defined by the full rulebook, including the consumer/maintainer framing and unslopped prose rules.

If the full rulebook and this loader conflict, the full rulebook wins.
