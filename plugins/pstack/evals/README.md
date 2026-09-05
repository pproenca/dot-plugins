# Pstack quality checks

This suite checks whether prompt changes preserve useful engineering behavior. It complements the marketplace validators, which check packaging rather than agent quality. It does not run on every coding task.

## Paired protocol

Freeze both plugin trees by explicit revision or immutable copy, and freeze this suite before a run. Check the preparation receipts before scheduling: instruction hashes must differ for an instruction comparison, while case hashes match. Identical instruction hashes mean repeated runs of one variant, regardless of their labels. Use fresh workspaces for each arm. Hold the candidate model, reasoning effort, tool access, task prompt, and delegation policy constant within each pair. Run a separate pair to study another reasoning level. Repeat pairs before treating a small difference as a reliable result.

Set the run budget before dispatch. Two selected cases, two instruction versions, two efforts, and two repetitions require 16 candidate runs, plus review. Record blocked or interrupted runs separately; they are neither quality failures nor passing replacements. This is a coordinator-run workflow with a preparation and verification CLI, not an unattended benchmark service.

A control should be a known Codex-compatible version. An unmodified Cursor plugin can require unavailable tools; that measures host compatibility as well as instruction quality. Record the original upstream revision and any adapter changes. Keep the original pstack's caller-first design, domain ownership, root-cause fixes, and direct verification as the quality standard.

Prepare a task using a frozen plugin copy:

```sh
python3 evals/run.py prepare event-feed /tmp/cedar-feed --plugin /path/to/frozen/pstack
```

Give the returned prompt to a fresh agent with no conversation history. Do not tell it the arm, hypothesis, rubric, or another agent's existence. The prepared project has the seed, public contract, smoke checks, and supplied plugin. It excludes this suite's held-out checks and reports. Ordinary project tests are allowed; hiding experimental labels does not mean banning the word `test` from a coding task.

The bundled prompts require direct execution without delegation. This holds execution conditions constant and measures implementation quality. It does not establish the quality of nested orchestration, external delivery, or automatic skill discovery. Test those separately with their actual capabilities before changing their defaults.

After the agent finishes, freeze its output and run the coordinator-owned checks:

```sh
python3 evals/run.py verify event-feed /tmp/cedar-feed
python3 evals/run.py verify lease-queue /tmp/maple-dispatch
```

Also run the queue's separate review probes:

```sh
PYTHONPATH=/tmp/maple-dispatch python3 -B evals/lease-queue/review_checks.py
```

These probes cover valid deeply nested payloads and finite time arguments whose float sum overflows. They were added after the first blind review. Keep their results separate when reproducing that experiment; include them in the gate for future runs. New checks must enforce the public contract, not introduce an undisclosed requirement.

These commands execute candidate Python code in a subprocess with a timeout. Use them only in the isolated local workspaces prepared for the run. They are not an OS security sandbox. Keep the acceptance checks outside the candidate workspace until it finishes.

## Cases

| Case | What it exercises |
|---|---|
| Event feed | Repair pagination at the filter and cursor boundary, stable ordering, timestamp ties, changing page sizes, and full traversal in both directions. |
| Lease queue | Model deduplication, lease expiry, retries, completion, stale tokens, boundary validation, and payload ownership behind four operations. |
| Inventory holds | Preserve stock across atomic reservations, capture, release, expiry, permanent replay keys, and detached snapshots. Authored independently as a transfer case. |

The seed smoke tests intentionally pass while the tasks remain unfinished. The held-out checks must reject each unfinished seed. Validate the checks against an independent correct implementation too. Checks inspect behavior, never literal source strings, prescribed class names, or skill citations.

## Frozen review rubric

Correctness is a hard gate: all held-out checks and the unchanged smoke checks must pass. Preserve the public contract and stated scope. Do not average away a failure because another case is good.

Have one reviewer inspect both anonymous outputs in each pair on the same scale. Hide plugin versions, model, effort, and the hypothesis. Rate each criterion from 0 to 2 with a concrete code or execution reference:

- Domain and boundary design: state and ordering rules have a clear owner; callers do not coordinate internal stages; mutable data does not leak.
- Simplicity: the change removes the cause or implements the domain without unsupported guards, redundant wrappers, or speculative systems. Line count alone is not a quality measure.
- Verification: focused checks exercise relevant failures and transitions; claimed passing commands have evidence. Inspect transcripts only when the host exposes them for these runs. Otherwise mark execution claims unverified and use coordinator-run results.
- Completion and scope: the requested behavior is delivered, unrelated files stay unchanged, and limitations are reported honestly.

A candidate is not promoted if it adds a correctness failure, a serious scope or honesty failure, or a material design regression. A quality tie with less overhead is promising, but timing, token counts, and tool counts need measured data. Missing traces or cost telemetry are unavailable, not zero.

## The loop

1. Freeze the task, rubric, plugin arms, and model/effort settings.
2. Run the pair, then check outputs and judge them blind.
3. Identify the actual failure mechanism. Fix the narrow instruction or capability gap responsible; do not add generic mandatory ceremony.
4. Rerun affected pairs on fresh workspaces and add a transfer task before promoting a fix. Never continue a failed arm with the hidden answer and count that as a fresh pass.
5. Record the settings, artifacts, verdict, unresolved coverage, and promotion decision. Keep large generated workspaces and transcripts outside the plugin.

For a workflow that includes review and repair, preserve the initial output and grade the final workflow output separately. A reviewer may derive findings from public requirements and code; keep coordinator-owned checks hidden. Report improvement across these stages honestly, including the extra review work. A repaired output is not a new independent candidate run.

The suite is a small regression set, not proof of universal parity. Expand it from real failures and important workflows, not a target count of tests.

See the [first comparison report](2026-09-05-comparison.md) for results, setup errors, and remaining coverage.
The [completed improvement loop](2026-09-05-improvement.md) records a rejected prompt addition, successful review-driven repairs, and a fresh check of the resulting workflow.
