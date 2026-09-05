---
name: arena
description: "Run competing design or implementation candidates, select a base, and integrate their useful parts."
---

# Arena

Fan out N parallel attempts at the same task. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the synthesized result.

Before delegating, read the [Codex collaboration contract](../poteto-mode/references/codex-tools.md). This workflow requires independent collaboration agents. If the current turn does not expose or authorize delegation, report `BLOCKED` because independent candidates are this skill's core behavior.

## Start

Keep one visible entry per phase throughout the run. Use the current mode's planning capability when available. Otherwise maintain the same phases in progress updates.

1. Frame
2. Fan out
3. Cross-judge
4. Pick
5. Graft
6. Verify

## Phase A: Frame

The N candidates will receive the same prompt, so the prompt is the contract. Get it right before spawning anything.

1. State the artifact each candidate is producing.
2. Derive the rubric. State what success looks like for *this* task, then turn it into 3-6 concrete gradeable criteria. Concrete: `Adds a --dry-run flag that skips writes`. Vague: `code is correct`. The rubric is the picker's tool in Phase D; candidates only see the task.
3. Pick the runners. Read `arena runners` from `~/.codex/pstack-models.md` when present. Otherwise use available models from different families or capability tiers, and inherit the parent when no valid override exists. Spawn more when the arena covers multiple design directions. Use the same model N times when the work is generation-bound rather than judgment-sensitive.
4. Assign output paths using the durable locations in the Codex collaboration contract. Repository candidates get separate Git worktrees; standalone artifacts get project output directories such as `<project-root>/artifacts/arena-<slug>/candidate-<n>/`. Candidates must not share a writable location.

## Phase B: Fan out

Start independent candidates with unique task names, using waves within the available concurrency limit. Give each agent the task, the shared grounding path, its own output path, and instructions to produce both the artifact and a short rationale. Continue non-overlapping local work. Check worker status only when needed, and wait only when the next phase requires a result.

The rationale is mandatory. Without it, the parent cannot tell whether a candidate's structure is principled or accidental, which makes Phase E grafting unreliable. Each rationale names the alternatives the candidate considered and what it rejected.

If a candidate fails to produce output, note the dropout and continue with the remaining candidates. With fewer than two completed candidates, report the comparison as incomplete; do not claim independent selection.

## Phase C: Cross-judge

After all Phase B candidates complete, choose one model from the `arena cross-judge pool` in `~/.codex/pstack-models.md` when present. Otherwise use a valid model different from the candidate models when possible, or inherit the parent. Spawn one judge subagent on that model. It sees the rubric and candidates by path label, scores each criterion, and recommends a base with rationale. It runs in parallel with the parent's reading in Phase D, not with the candidates. Spawning while candidates still write makes the judge see partial output and report false dropouts.

## Phase D: Pick a base

Read every candidate end to end before picking. Skimming N candidates surfaces only the candidate whose surface looks most familiar.

Score each candidate against the rubric criterion by criterion, not on holistic feel. Compare against the cross-judge. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base on which candidate a future maintainer can extend most easily without breaking invariants. Prefer the cleaner boundary or smaller surface area when two feel tied, per the Laziness Protocol.

Record the pick and the reason in a short synthesis note alongside the base artifact, including the cross-judge's verdict.

## Phase E: Graft

Walk each losing candidate once more and identify what is worth porting into the base. The signal is usually one or two things per candidate, not most of it.

Fold each graft in by hand, per the **redesign-from-first-principles** principle skill. Don't paste mechanically. The result has to remain coherent under one mental model.

Record what was grafted, from which candidate, and what was rejected and why. The rejection notes are the highest-signal part of the record. Future readers learn from what you considered and dropped, not just what you kept.

When N candidates converge on the same shape, that is a strong agreement signal. Note the convergence in the record and ship the consensus shape. No graft is needed. When N candidates wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

The synthesized artifact has to hold up under the same scrutiny as any other output, per the **prove-it-works** principle skill. The arena does not earn you a pass.

If verification surfaces a problem the arena did not catch, either Phase A was wrong (re-frame and re-run) or one candidate caught it and you missed the graft (go back to Phase E). Don't paper over.

## Outputs

One synthesized artifact. One short synthesis note alongside, naming the base, the grafts (with source candidate), the rejections, the dropouts if any, and the verification result.
