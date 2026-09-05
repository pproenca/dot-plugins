### Multi-phase or multi-PR plan

**You own the plan, not the code. The plan is a checklist an owner runs box by box and the operator audits from the evidence.** For work that spans phases or stacked PRs. The plan is the deliverable. Do not implement.

1. When the change is one or two files with an obvious approach, skip the plan. Say so and stop.
2. Settle open questions by prototype before you write. For a question about layout, timing, behavior, or whether an API works, run `playbooks/prototype.md`. Keep the branch, the SHA, and the screenshots for Appendix A. Ask one concise question only for a product or preference call that no run can settle.
3. Explore with collaboration subagents and an explicit available model when model diversity matters. Each returns file pointers, conventions, test commands, and entry points. Do not inline source dumps.
4. Copy the skeleton below into the plan file and fill every placeholder. Unless the operator names a path, write the file under `${CODEX_HOME:-$HOME/.codex}/plans/`, outside the repository. Keep every heading and sub-block in the order shown. One section per PR. One PR is one change with its own evidence. Name the execution playbook in **How to read this**. Pick between `playbooks/autopilot-full.md` and `playbooks/autopilot-stack.md` per the rule at the end of `playbooks/autopilot-stack.md`. A standing program takes `playbooks/orchestrate.md`.
5. Apply the **technical-writing** skill, then **unslop**. The body is one Diátaxis mode, how-to. Appendices hold explanation and reference. Two rules apply verbatim. "i dont want any abstract metaphors" and "write like hemingway". Each heading states the task or finding. No long dashes. No mid-sentence colons.
6. Resolve `scripts/check-plan.mjs` relative to this skill and run `node <check-plan.mjs> <plan.md>`. Fix every line it prints. The script enforces the skeleton, the verification rule in every verification block, and the punctuation rules.
7. Hand back the plan path and script output, then stop. Execution starts on the operator's explicit go under the execution playbook the plan names.

**Verification.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. That sentence is the verification rule. Every verification block opens with it. The live block is mandatory. Ten isolated lanes at the PR head drive the real product through its control skill. Each lane is one box with a concrete scenario, saved evidence, and a pass predicate. Use the configured `swarm workers` model when available. Otherwise use an available fast model and inherit the parent when no override is valid. One lane is the **Regression lane against trunk.** It runs the same load-bearing scenario on trunk and head. If trunk does not have the feature, the lane records that fact and gates the behavior the diff adds plus the end state the user waits for instead of inventing a trunk result. The perf gate is dual-sided: trunk and head must both produce the named metric. If trunk lacks the feature, also isolate the work the diff adds and set an absolute budget for that work plus the end-to-end state the user waits for; do not claim a ratio between unlike scenarios. The perf block names the metric, the interleaved probe, the trunk baseline measured first, and the rule with the number that fails. A PR that changes an interaction is review-gated. The operator reviews screenshots and a video before merge. A PR that changes no interaction writes `**Review gate.** None. <PR id> is not review-gated.` and has no boxes under it.

**Control skill.** Pick it by product. Browser and web UI work uses an available browser-control skill. CLIs and TUIs use **control-cli** when installed. Native apps use the available computer-use or simulator-driving skill. A PR that touches two products gets lanes on both. A product with no control skill is a risk in Appendix C, and its live block still names how each lane drives it.

````markdown
# <Program> plan

<Under ten lines. What changes, for whom, the rule the program enforces, and the PR ids in order.>

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `skills/poteto-mode/playbooks/<execution playbook>.md`. <Who merges, and which PR ids are the operator's items that stop at merge-ready.>

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on her explicit go.
- [ ] On her go, record this finish condition in the plan. Create a goal only if the operator explicitly requests one. "<The plan path, the PR ids in order, the verification rule, who merges, and the done condition.>"
- [ ] Resolve these paths at program start and record them in the plan. Re-read them at every tick.
  - [ ] `<active pstack skill root>/poteto-mode/playbooks/<execution playbook>.md`
  - [ ] `<active pstack skill root>/swarm/SKILL.md`
  - [ ] `<active control skill path>`
  - [ ] `<active pstack skill root>/poteto-mode/playbooks/opening-a-pr.md`
  - [ ] `<active pstack skill root>/<each other leaf skill the program uses>/SKILL.md`
- [ ] If recurring follow-ups are requested, create or update a thread heartbeat with the available automation tool. Follow the scheduling rules in the Codex collaboration contract and the operator's requested cadence.
- [ ] Use this tick prompt, preserving any explicit request for periodic status updates. "Re-read the execution playbook from its recorded active skill path and the finish condition in the plan or active goal. Audit the operation against both and fix drift in this tick. Probe active lanes and verify progress through their outputs. Replace a stuck lane when the evidence warrants it. Stay quiet while nothing meaningful changes. On meaningful progress, completion, failure, or required operator action, report the queue of PR, owner, state, and head SHA, new verdicts, merges, open gates, and blockers. Stop this automation when the finish condition is met."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Create one explicit worktree and branch per PR. Record each absolute path.
- [ ] Spawn one collaboration agent per PR. Pass its worktree path and require every command to use that working directory.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges, or base it on the parent branch when the execution playbook stacks.
  - [ ] <PR id> and <PR id> are independent and first. Both branch from `main`.
  - [ ] <PR id> after <PR id>.
- [ ] Hold the file boundaries. <PR id or class> touches only `<glob>`.
- [ ] Hold the review gate. <PR ids> change an interaction. They wait for the operator's review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Default to `gh`; if `command -v origin` succeeds and Origin can resolve the repository, use `origin pr` for every PR operation. Record any fallback to `gh`. Never require `gt`.
- [ ] Open the PR ready, never draft, with `origin pr create --status open --base <base-branch>` or `gh pr create --base <base-branch>` according to the resolved forge. A stack child targets its parent branch.
- [ ] Run the repository's lint and typecheck once before the PR-facing push. Push with hooks on.
- [ ] Remove dead compatibility paths and narrating comments before each commit. Run **no-comments** before review.
- [ ] Triage every automated review comment per `../references/bugbot-triage.md`.
- [ ] Rebase onto current trunk before babysit and again before the merge-ready report.

### Verdict and merge, for every PR

- [ ] At the merge-ready head SHA, run the swarm per `skills/swarm/SKILL.md`. One gates lane. The ten live lanes from the PR's **Verify, live** block. The perf lane from its **Verify, perf** block. One audit lane reads the diff and receipts and distrusts the PR body.
- [ ] Clean only when every lane is `PASS`. Findings go back to the owner. A new head gets a fresh swarm and verdict.
- [ ] <The merge or append rule from the execution playbook, with the patch-id rule from `playbooks/shipping.md`.>

### Boot recipe, for every live lane

Each live lane runs in its own explicit worktree at the PR head. Create and record those worktrees before spawning the lanes. Drive through the selected control skill.

- [ ] `git fetch origin <head-branch> && git checkout <head SHA>`.
- [ ] <Start the backend and product. Wait for ready.>
- [ ] <Deliver input only through the control skill. Name the read-only diagnostics.>
- [ ] Save screenshots under the durable project output directory, for example `<project-root>/artifacts/swarm-<pr-id>/worker-<n>/<slug>.png`, and return their absolute paths with the report.

## <Task as a verb phrase> (<PR id>)

**Depends on.** <PR id, or None.>

**Files.**

- [ ] Edit `<path>`.
- [ ] Create `<path>`.
- [ ] Delete `<path>`.

**Build.**

- [ ] <One change. Name the symbol and file.>

**You see.**

- [ ] <One observable result, with the exact log line or screen state.>

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] <Test file and the case it gains.> Run `<command>`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run <the same load-bearing scenario> at trunk and head. If trunk lacks the feature, record that and gate <the behavior the diff adds plus the end state the user waits for>. Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 2. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 3. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 4. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 5. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 6. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 7. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 8. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 9. <Scenario.> Save `<slug>.png`. Pass when <predicate>.
- [ ] Lane 10. <Scenario.> Save `<slug>.png`. Pass when <predicate>.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. <What is measured at both trunk and head. If trunk lacks the feature, also name the diff-added work and the end-to-end state the user waits for.>
- [ ] Probe. <The command or procedure, run at trunk and at the head, interleaved. Both sides must produce the metric.>
- [ ] Baseline. Record the trunk <value> first.
- [ ] Rule. <Head against trunk, with the number that fails. If the scenarios differ, add absolute budgets for the diff-added work and the user-visible end state instead of an invalid ratio.>

**Review gate.** The operator reviews before merge.

- [ ] Copy lane <n> screenshots into `<media path>/<pr-id>-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of the change. Save it as `<media path>/<pr-id>-review.mp4`.
- [ ] Post the screenshots and video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**

- [ ] Root's clean verdict at the exact head SHA.
- [ ] Automated-review triage done.
- [ ] Rebased onto current trunk after the verdict, patch-id unchanged.
- [ ] <The owner squash-merges its own PR, or the root appends the PR to the base-branch stack and the operator lands it bottom-up.>

## Close the program

- [ ] Every box above is checked with its evidence.
- [ ] Reply to the operator with the report the execution playbook names.

## Appendix A. Prototype evidence

<Each open question a prototype answered, with the branch, SHA, and artifact links. Each question that stays unproven.>

## Appendix B. Alternatives rejected

<Each approach weighed and why it lost.>

## Appendix C. Risks

<Each risk with the PR it lands in and what the owner watches.>

## Appendix D. Links and reading list

<Docs to read before editing. Which PRs get `skills/how/SKILL.md` and `skills/interrogate/SKILL.md`. The trail per `skills/show-me-your-work/SKILL.md`.>
````

**Reply:** the plan path, PR ids with dependencies and the review-gated set, what prototypes proved and what stays unproven, and the check script output.
