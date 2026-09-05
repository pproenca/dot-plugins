---
name: poteto-mode
description: "Engineering playbooks for implementation, investigation, refactoring, and verification. Use for substantial engineering work or when asked for poteto mode."
metadata:
  mode: "true"
  icon: "crown"
  color: "yellow"
---

# Poteto mode

Pstack favors simple designs, independent exploration where it helps, and evidence from the actual result. Complete the user's requested outcome, including running and fixing the relevant checks.

## Choose the useful workflow

For a small, well-understood change, inspect the affected source, make the change, and check it directly. For substantial work, read the matching playbook below and adapt its phases to the task. Keep consequential decisions and remaining work visible without copying a checklist verbatim.

| Task | Read |
|---|---|
| Understand or assess existing behavior | [Investigation](playbooks/investigation.md) |
| Reproduce and fix a defect | [Bug fix](playbooks/bug-fix.md) |
| Add behavior | [Feature](playbooks/feature.md) |
| Change structure while preserving behavior | [Refactoring](playbooks/refactoring.md) |
| Improve measured performance | [Perf issue](playbooks/perf-issue.md), or [Hillclimb](playbooks/hillclimb.md) for sustained experiments |
| Diagnose a live symptom or captured trace | [Runtime forensics](playbooks/runtime-forensics.md) or [Trace forensics](playbooks/trace-forensics.md) |
| Settle an empirical design question | [Prototype](playbooks/prototype.md) |
| Match an existing UI | [Visual parity](playbooks/visual-parity.md) |
| Write or evaluate skills | [Authoring a skill](playbooks/authoring-a-skill.md) or [Eval](playbooks/eval.md) |
| Prepare or maintain PRs | [Opening a PR](playbooks/opening-a-pr.md) or [Babysit](playbooks/babysit.md) |
| Land a verified stack | [Shipping](playbooks/shipping.md) |
| Run a long task or standing program | [Autonomous run](playbooks/autonomous-run.md) or [Orchestrate](playbooks/orchestrate.md) |
| Execute an authorized PR queue | [Autopilot-full](playbooks/autopilot-full.md) or [Autopilot-stack](playbooks/autopilot-stack.md) |
| Plan multiple phases or PRs | [Multi-phase plan](playbooks/multi-phase-plan.md) |
| Resume, pause, or reclaim worktrees | [Session pickup](playbooks/session-pickup.md), [Pause safely](playbooks/pause-safely.md), or [Worktree cleanup](playbooks/worktree-cleanup.md) |

If no playbook fits a substantial task, read [figure-it-out](../figure-it-out/SKILL.md). Stepping away does not itself require a larger workflow.

## Scale the work

- Read supporting skills only when their guidance changes a current decision. The [principles index](references/full-mode.md) provides targeted routes; it is optional reference material.
- Use [architect](../architect/SKILL.md) for consequential, unresolved interface or ownership choices. Crossing a function boundary alone does not warrant competing designs.
- Delegate concrete independent investigations, implementations, or reviews when they can save time or improve confidence alongside useful local work. Read the [Codex collaboration contract](references/codex-tools.md) before delegation or scheduling. Use [swarm](../swarm/SKILL.md) for coverage and [arena](../arena/SKILL.md) for competing candidates when those workflows fit.
- Run required repository checks and verify changed behavior on the relevant artifact. Add tests for a meaningful regression or uncovered contract. Broaden or repeat checks when failures, changes, or unresolved risks justify it.
- Read [interrogate](../interrogate/SKILL.md) when independent adversarial review is requested or a consequential design remains contested. Review findings against the source before acting on them.
- Report the outcome, consequential choices, verification, and remaining limitations in plain prose. Use [unslop](../unslop/SKILL.md) or [technical-writing](../technical-writing/SKILL.md) when an editorial pass is useful.

## Preserve the task boundary

The user's scope and current tool instructions govern the workflow. Playbooks do not add permission to publish, message others, deploy, merge, or change unrelated skills. A reference to Opening a PR applies when PR delivery is in scope. Follow repository conventions for branches, commits, and reviews.

Proceed with authorized work using reasonable assumptions. Ask only for missing input that materially changes the result and cannot be resolved by inspection or a reversible experiment. Prepare the concrete result before any necessary approval. Preserve explicit review checkpoints and evidence gates for consequential actions; do not add a checkpoint merely because a first implementation is ready.
