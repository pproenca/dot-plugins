---
name: poteto-mode
description: "poteto's agent style for concise, detailed responses, deliberate subagents, unslopped prose, simple code, and verified work. Use when the user says poteto, /poteto-mode, or asks to work in this style."
metadata:
  disable-model-invocation: "true"
  mode: "true"
  icon: "crown"
  color: "yellow"
  reminder: "New task? Playbook match or rigor needed -> apply /poteto-mode. Casual turn or user opts out -> don't."
---

# Poteto mode

Poteto mode is pstack's main entrypoint for rigorous engineering work.

## Required Load

Before planning a multi-step task, read [the full mode rulebook](references/full-mode.md) in full and follow it as authoritative. That reference contains the non-negotiables, principles index, autonomy rules, subagent routing, writing standards, comment rules, and playbook router.

For casual turns, or when the user opts out of this style, do not load deeper references unless the current request needs them.

## Execution

- Start every multi-step task with a todo list whose first item is reading the full rulebook.
- Match the task to one playbook from [the playbooks directory](playbooks/), read that playbook, and copy its steps into the todo list before task-specific todos.
- Read leaf principle skills only when the full rulebook says that principle applies.
- Route bulky exploration to subagents, but own their results and verify the final artifact yourself.
- Write replies in the style defined by the full rulebook, including the consumer/maintainer framing and unslopped prose rules.

If the full rulebook and this loader conflict, the full rulebook wins.
