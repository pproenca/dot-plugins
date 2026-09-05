### Eval

Evaluate a prompt or skill change against the quality of the work it produces. Preserve the original pstack's engineering standards while reducing instructions that add no value.

For an improvement request, deliver a change-and-retest decision with before/after outcome evidence. A baseline score alone leaves that loop unfinished. Keep a useful change or reject an ineffective one; do not manufacture a winning result.

## Frame and freeze

Freeze each plugin by explicit revision or immutable copy and record its content hash. Confirm the hashes match the intended arms before scheduling. Choose representative tasks and write the acceptance criteria before running either variant. Keep correctness, scope, and honest verification as hard gates. Assess domain modeling, interface quality, root-cause fixes, and simplicity from the artifacts. Loading more skills or writing less code is not itself a quality score.

For an instruction comparison, hold the model, reasoning effort, tools, starting files, task prompt, and delegation policy constant within each pair. Vary one factor at a time. Use separate pairs for another model or effort. Repeat close results before treating a difference as reliable. Define the run limit and promotion rule before spending a long session on the experiment.

Use a Codex-compatible control when comparing Codex instructions. An unmodified plugin from another host can fail on missing capabilities. Record the upstream source and adapter changes so compatibility failures do not masquerade as quality regressions.

## Run blind

- Give each agent a fresh project directory and only its instruction variant. Keep the rubric, held-out checks, arm labels, and other outputs outside its workspace.
- Use an organic task prompt without mentioning the experiment or requesting skill citations. Ordinary project files and tests keep their normal names.
- Use fresh agents without inherited conversation history. Select identical validated model and effort settings for a pair under the [Codex collaboration contract](../references/codex-tools.md). Schedule runs within available slots.
- Preserve user and repository constraints. Generated artifacts stay outside the plugin. Use explicit isolated worktrees for repository writers or separate directories for standalone fixtures.
- Freeze the output when a run finishes. Do not feed hidden failures back into that arm and then call the repair a fresh passing run.

## Check and review

Run coordinator-owned behavior checks against the finished artifacts. First prove that the checks reject a broken seed and accept an independent correct implementation. Include unaffected behavior and meaningful edge cases. Do not test literal source strings, mandated headings, or whether a named skill was cited.

Have one independent judge review both anonymous outputs on one scale, with the same rubric and no model or variant labels. Use a distinct validated judge model when available and useful. Independent same-model review remains useful but is not cross-model evidence. Read the artifacts yourself and resolve disagreements against concrete behavior and code; agreement is not proof.

Read only the exact run transcript or history the host exposes for these agents. Codex user-task tools do not necessarily expose collaboration-agent history. If traces, tool counts, tokens, or timing are unavailable, record that limitation. Infer neither instruction loading nor execution from the final answer alone.

## Iterate and decide

1. Compare each pair against the frozen quality gates. A correctness regression cannot be averaged away by a faster run elsewhere.
2. Diagnose a concrete regression and change only the responsible instruction, trigger, or capability adaptation. Do not respond by adding a general mandatory workflow.
3. Rerun affected tasks from fresh starting states, then use a transfer task that did not drive the fix. Preserve previous failures in the report.
4. Promote only when quality evidence supports the change. Prefer less instruction and overhead when quality is preserved. Otherwise revise or revert the relevant change. A small suite supports a bounded conclusion, not universal parity.

For pstack changes, use the bundled [quality suite](../../../evals/README.md) for pagination, lease-queue, and inventory-reservation tasks and the reusable prepare/verify commands. Add cases from real failures. Keep this workflow conditional on skill evaluation or a meaningful regression concern; it does not run before every edit.

**Reply:** control and variant, tasks, model and effort settings, acceptance results, blind review, observed regressions, iteration evidence, promotion decision, and coverage limits.
