---
name: swarm
description: "Fan out N parallel workers, drain them, and return one report. Use when $pstack:swarm, 'swarm this', or parallel coverage, races, gauntlets, and exploration."
---

# Swarm

Fan out N parallel workers. They may cover separate slices, race the same brief, or mix both. The parent waits, aggregates, and returns one report.

Before delegating, read the [Codex collaboration contract](../poteto-mode/references/codex-tools.md). This workflow requires independent collaboration agents. If the current turn does not expose or authorize delegation, report `BLOCKED` because parallel coverage is this skill's core behavior.

## Start

Keep one visible entry per phase throughout the run. Use the current mode's planning capability when available. Otherwise maintain the same phases in progress updates.

1. Frame
2. Fan out
3. Aggregate
4. Report

## Phase A: Frame

1. State the done predicate and the artifact or report the swarm must return.
2. Choose the shape. Partition into slices, race N workers on identical briefs, or mix both. For a race or mixed shape, declare `first pass`, `rank all`, or `best-of` before spawning.
3. Set N from the user or derive it from the shape. N is total workers, not the current concurrency limit. Run only as many at once as the visible collaboration instructions allow.
4. Pick the worker model from `swarm workers` in `~/.codex/pstack-models.md` when present. Otherwise inherit the parent model. For a model race, name each arm's available model up front.
5. Give each worker its own writable output. Repository writers get separate worktrees and branches. Artifact-only workers get unique directories such as `/tmp/swarm-<slug>/worker-<n>/`.

## Phase B: Fan out

Start the first wave up to the current collaboration limit with unique task names and self-contained briefs. As workers finish, refill the available slots until all N have started. Use the shared checkout for read-only slices. Give every repository writer its own worktree and branch. Continue non-overlapping local work. Check worker status only when needed, and wait only when aggregation cannot proceed without a result.

When a worker must start from a non-default branch, create its isolated worktree from that exact branch or commit.

Every brief stands alone. Include the goal, scope, exact slice or race arm, how to verify, and what to report. Reports use `PASS`, `ISSUES`, or `BLOCKED` with evidence.

If a worker drops out, proceed with N-1 and note it.

## Phase C: Aggregate

Read each worker's final result delivered by collaboration. For coverage, every required slice needs a result. For a race, apply the selection rule declared up front. Use first pass, rank all, or best-of. Do not paste raw worker dumps.

Keep a compact result table, one-line evidenced issues, and explicit gaps or dropouts.

## Phase D: Report

Return one consolidated in-chat report with the table, issue one-liners, gaps or dropouts, and the race rule when used.
