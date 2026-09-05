# Make it yours

poteto-mode is one person's style. The machinery underneath, playbooks, routing, model roles, works just as well wearing yours. This page covers generating a personal mode, capturing lessons from a session, authoring a focused skill, and testing a skill change before you trust it.

## Generate your own mode with `$pstack:automate-me`

```text
$pstack:automate-me
```

You don't describe your style, because [`$pstack:automate-me`](../../skills/automate-me/SKILL.md) reads it from recent Codex tasks in the active workspace. It drafts `.agents/skills/<your-name>-mode/SKILL.md` through the built-in **skill-creator**, runs the draft through [`$pstack:unslop`](../../skills/unslop/SKILL.md), and opens a PR from a worktree.

Run it again whenever your habits drift:

```text
$pstack:automate-me update my mode skill with everything since its last edit
```

Update mode mines only the history since the skill last changed. It keeps rules you haven't contradicted, revises the ones with new evidence, and adds sections only for genuinely new patterns.

## Capture a session's lessons with `$pstack:reflect`

Right after a task that taught you something, run:

```text
$pstack:reflect that took way too long. capture what we learned so the next run doesn't repeat it.
```

[`$pstack:reflect`](../../skills/reflect/SKILL.md) sends the transcript to three parallel reviewers, then a synthesizer sorts the proposals into `Accepted`, `Rejected`, and `Backlog` and waits for your approval before any skill changes. Approve a proposal only if it would change a future decision. One weird session is an anecdote, not a rule.

## Author a focused skill

When you already know the workflow you want to capture:

```text
$pstack:poteto-mode write a skill for verifying database migrations in this repo
```

Writing a skill matches the [Authoring or modifying a skill playbook](../../skills/poteto-mode/playbooks/authoring-a-skill.md), which routes through **skill-creator**, validates the frontmatter and links, and uses Opening a PR when PR delivery is in scope.

One special case has its own generator. A skill that must drive your app and prove behavior is a verification skill, so use [`$pstack:create-verification-skill`](../../skills/create-verification-skill/SKILL.md) and [`$pstack:maintain-verification-skill`](../../skills/maintain-verification-skill/SKILL.md) instead. [Verify and ship](./06-verify-and-ship.md#create-a-project-verification-skill) covers both.

## Write docs to a standard with `$pstack:technical-writing`

Skills aren't the only prose you ship. For docs, RFCs, readmes, PR descriptions, and commit messages:

```text
$pstack:technical-writing review the readme changes
```

[`$pstack:technical-writing`](../../skills/technical-writing/SKILL.md) applies a layered standard with one goal, prose a tired engineer understands on the first read. It picks the document's mode first (tutorial, how-to, reference, or explanation), then works sentence by sentence: who does what, one thought per sentence, nothing readable two ways. Use it to review what you or an agent just wrote, or name it up front when you ask for a doc.

## Test a skill change blind

A skill edit affects every future session, so test it like the experiment it is:

```text
$pstack:poteto-mode run the eval playbook on this skill change. same task for both variants, candidates stay blind.
```

The [Eval playbook](../../skills/poteto-mode/playbooks/eval.md) compares anonymous outputs under one rubric. Hold the model, reasoning effort, tools, and starting task constant within a pair; use separate pairs for another reasoning level. Grade behavior and code quality with held-out checks and independent review. Skill citations are not evidence of engineering quality.

The [bundled quality suite](../../evals/README.md) supplies pagination, lease-queue, and inventory-reservation tasks, isolated project preparation, and coordinator-owned acceptance checks. Its loop freezes the contract, runs both variants, diagnoses regressions, and reruns a narrow fix on fresh workspaces plus a transfer task. It runs when evaluating a pstack change, not before every edit. The [completed improvement loop](../../evals/2026-09-05-improvement.md) shows how measured outcomes changed the Feature playbook.

Read every output yourself before accepting the verdict. If you disagree with the judge, suspect the rubric before you suspect your judgment.

**Pitfall:** don't edit a skill mid-task because it's misbehaving. Fix it in its own PR and keep the task moving. A skill edit that ships tangled into feature work is invisible to review and impossible to evaluate.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
