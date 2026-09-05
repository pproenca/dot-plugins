# pstack

i'm [poteto](https://x.com/poteto). i'm not a president or ceo, but i've worked with millions of lines of code at Meta, Netflix, and Cursor. i'm also on the react core team where i help build and maintain react compiler.

there's a growing sense that ai writes too much slop code. i agree. i don't want to ship like a team of twenty slop artists. throughput without quality is not a goal i aspire to. if you want to go fast, go deep first. 

**pstack is my answer.** these are the same skills i use every day to ship high quality code at Cursor, ported to Codex tools and skill discovery. the goal is not to maximize loc. pstack helps you write less, but higher quality code.

**pstack gives you fearless parallelism.** when you can go deep on one agent and trust it to write good, verifiable code, you can truly parallelize with confidence. start multiple agents up with `poteto-mode` and trust that they'll apply rigorous engineering principles to their work.

**codex lets pstack split work across collaboration agents.** pstack reads the tools exposed in each turn, uses Codex collaboration v2 directly, and falls back to local work when delegation is unavailable. configure validated model overrides for your host, or inherit the parent model everywhere.

fork it. improve it. make it yours. PRs are welcome! 

## install

```bash
codex plugin add pstack@dot-plugins
```

## get started

start with poteto mode. model setup is optional:

1. use [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) for substantial engineering work.
2. run [`$pstack:setup-pstack`](./skills/setup-pstack/SKILL.md) when you want model or reasoning overrides. otherwise workers inherit your settings.

new here? the [pstack guide](./docs/guide/README.md) walks you through a first real task, from setup and prompting through verification and overnight runs.

that's it. the other skills are situational; the mode skill uses them as needed. [`$pstack:setup-pstack`](./skills/setup-pstack/SKILL.md) reads the models and reasoning efforts the current Codex host supports and writes the role mapping.

## usage

use [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) at the start of a task. it reads your request, picks from a set of playbooks, and runs the other skills as the steps need them.

### just use [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md)

this skill is the main shortcut. i use it whenever i need the agent to do rigorous engineering work. it comes with twenty-two playbooks:

```
$pstack:poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even when idle. repro
first, then fix and verify.
```

```
$pstack:poteto-mode i'm going to bed. land the stack even if ci flakes. i want everything merged by
morning.
```

<details>
<summary>the twenty-two playbooks</summary>

| playbook | for |
|---|---|
| [investigation](./skills/poteto-mode/playbooks/investigation.md) | a read-only question. how does x work, why was y built this way, are we sure. |
| [bug fix](./skills/poteto-mode/playbooks/bug-fix.md) | reproduce a defect, root-cause it, and fix with runtime evidence. |
| [perf](./skills/poteto-mode/playbooks/perf-issue.md) | trace a measured slowness and improve it against a baseline. |
| [hillclimb](./skills/poteto-mode/playbooks/hillclimb.md) | sustained, scientific improvement of one metric against a target, looping hypotheses with before/after measurement and one commit per accepted win. |
| [runtime forensics](./skills/poteto-mode/playbooks/runtime-forensics.md) | diagnose a live symptom (leak, idle-cpu spin, glitch) from instrumentation. |
| [trace forensics](./skills/poteto-mode/playbooks/trace-forensics.md) | diagnose a captured profiling artifact (cpuprofile, trace, spindump, heap snapshot). |
| [feature](./skills/poteto-mode/playbooks/feature.md) | new or changed behavior, built from a named data shape. |
| [refactoring](./skills/poteto-mode/playbooks/refactoring.md) | a behavior-preserving change to structure or shape. |
| [prototype](./skills/poteto-mode/playbooks/prototype.md) | a throwaway sketch to make a design or behavioral decision cheaply, or to settle an empirical fork by observing it. |
| [visual parity](./skills/poteto-mode/playbooks/visual-parity.md) | pixel-exact ui equivalence between two implementations. |
| [authoring a skill](./skills/poteto-mode/playbooks/authoring-a-skill.md) | writing or editing a SKILL.md. |
| [eval](./skills/poteto-mode/playbooks/eval.md) | test how a skill or prompt change affects agent behavior, blinded. |
| [babysit](./skills/poteto-mode/playbooks/babysit.md) | drive a pr or a stack to merge-ready: conflicts, review threads, ci. |
| [shipping](./skills/poteto-mode/playbooks/shipping.md) | independently verify a green stack, then land the contiguous verified run bottom-up with gh or optional Origin. |
| [autonomous run](./skills/poteto-mode/playbooks/autonomous-run.md) | drive a long task to completion without stopping. |
| [orchestrate](./skills/poteto-mode/playbooks/orchestrate.md) | a standing project handed to one coordinator chat: multi-day, many stacked prs, fleets of subagents. |
| [autopilot-full](./skills/poteto-mode/playbooks/autopilot-full.md) | run independent prs to merged with one owner per pr and root verification of each merge-ready head. |
| [autopilot-stack](./skills/poteto-mode/playbooks/autopilot-stack.md) | build and verify one linear graphite stack for the operator to review and land. |
| [session pickup](./skills/poteto-mode/playbooks/session-pickup.md) | resume or take over a prior agent's in-flight work. |
| [pause safely](./skills/poteto-mode/playbooks/pause-safely.md) | suspend in-flight work cleanly so it can be resumed later. |
| [multi-phase plan](./skills/poteto-mode/playbooks/multi-phase-plan.md) | work that spans phases or stacked PRs. |
| [worktree cleanup](./skills/poteto-mode/playbooks/worktree-cleanup.md) | reclaim disk by pruning merged or abandoned worktrees and stale ios simulators, safety-gated. |

</details>



when invoked it:

1. handles small, clear changes directly and selects a [playbook](./skills/poteto-mode/playbooks/) for substantial work.
2. reads supporting guidance only for the current decision.
3. delegates independent work when it helps, within available concurrency.
4. verifies the requested outcome and reports the evidence.

the full rules and playbooks live in [`skills/poteto-mode/SKILL.md`](./skills/poteto-mode/SKILL.md).

[`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) describes nontrivial engineering work directly, which makes it eligible for Codex's automatic skill selection without an explicit skill mention. explicit invocation remains the deterministic path. opt out any time by saying so.

for long runs, pair [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) with a Codex thread heartbeat automation and a checkable finish condition.

## skills

[`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) runs most of these for you when a step needs them (`how`, `why`, `architect`, `arena`, `swarm`, `interrogate`, `unslop`, `no-comments`, `technical-writing`, `tdd`, and the principles). the table below is for when you want one directly:

```
$pstack:how do we cancel runs? do we have an n+1 when we look up every run to cancel?
```

```
$pstack:interrogate review this pr.
```

<details>
<summary>all skills</summary>

| skill | use it when |
|---|---|
| [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) | default entry point for any non-trivial task. |
| [`$pstack:how`](./skills/how/SKILL.md) | you want a walkthrough of how a subsystem works. |
| [`$pstack:why`](./skills/why/SKILL.md) | you want to know why something was built this way. discovers available MCPs at run time and queries each evidence category in parallel (source control, issue tracker, long-form docs, real-time chat, infra observability, error tracking, analytics warehouse). |
| [`$pstack:recall`](./skills/recall/SKILL.md) | you're starting or resuming work and want your recent context on a topic rebuilt from your own chat history and the shared record, handed back as a tight current-state brief. |
| [`$pstack:blast-radius`](./skills/blast-radius/SKILL.md) | you have a small-looking change and want to know what else it could break, with the one fact it's safe because of proven by running code, not asserted. |
| [`$pstack:architect`](./skills/architect/SKILL.md) | a consequential interface or ownership choice needs competing designs, with caller usage settled first. |
| [`$pstack:arena`](./skills/arena/SKILL.md) | you want N parallel attempts at the same thing, then to grab the best parts of each. |
| [`$pstack:swarm`](./skills/swarm/SKILL.md) | you want N parallel workers across different slices or races, then one aggregated report. |
| [`$pstack:interrogate`](./skills/interrogate/SKILL.md) | you have a diff and want several different models to try to break it, including a strict code-quality lens. |
| [`$pstack:automate-me`](./skills/automate-me/SKILL.md) | you want your own `-mode` skill, drafted from how you've actually worked. |
| [`$pstack:make-bot-ui`](./skills/make-bot-ui/SKILL.md) | you want a page that wakes one persistent bot task. requires webhook support; the skill explains missing capabilities before offering a substitute. |
| [`$pstack:setup-pstack`](./skills/setup-pstack/SKILL.md) | you want to pick which models pstack uses per role. detects your models and writes a config rule. |
| [`$pstack:reflect`](./skills/reflect/SKILL.md) | a long task landed and you want the recipe captured as a skill edit. |
| [`$pstack:teach`](./skills/teach/SKILL.md) | you want to actually understand a change or subsystem, not just have it summarized. runs how + why and weaves one plain explanation, built up diagram by diagram. |
| [`$pstack:tdd`](./skills/tdd/SKILL.md) | you're fixing a bug and there's a cheap local test path. write the failing test first, then the fix. |
| [`$pstack:no-comments`](./skills/no-comments/SKILL.md) | strip comments before review; spawns Comment Sicko, fixes accepted findings, offers encodings for claimed constraints. |
| [`$pstack:typescript-best-practices`](./skills/typescript-best-practices/SKILL.md) | you're reading or editing typescript. grounds the type-system-discipline principle in syntax. |
| [`$pstack:figure-it-out`](./skills/figure-it-out/SKILL.md) | no bundled playbook fits. designs a rigorous, auditable playbook for the task. |
| [`$pstack:show-me-your-work`](./skills/show-me-your-work/SKILL.md) | you want a reviewable decision trail. logs decisions to a tsv you can commit. |
| [`$pstack:create-verification-skill`](./skills/create-verification-skill/SKILL.md) | your project has no scripted way to prove app behavior. generates a project-local verify skill with a feature map, for any language or platform. |
| [`$pstack:maintain-verification-skill`](./skills/maintain-verification-skill/SKILL.md) | your verify skill's feature map has drifted from the app. source wave + one live pass, at most one PR of proven corrections. |
| [`$pstack:unslop`](./skills/unslop/SKILL.md) | you're cleaning up writing. removes AI tells. |
| [`$pstack:bro`](./skills/bro/SKILL.md) | you want the last message restated in plain human language, no jargon. |
| [`$pstack:technical-writing`](./skills/technical-writing/SKILL.md) | layered doc standard (Diátaxis + Google developer style + STE + Global English) for docs, RFCs, readmes, PR descriptions, commit messages. |

</details>



### examples

mostly i type [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) at the start of a task and let it route to a playbook. the other skills fire as the steps need them. a few i reach for directly.


<details>
<summary>all the examples</summary>

```
bug fix:           $pstack:poteto-mode this pr has a subtle bug where the scroll drifts every 750ms even
                   when idle. repro first, then fix and verify.
perf:              $pstack:poteto-mode a big list takes a second or two to load even though we virtualize.
                   run a cpu trace and tell me why.
feature:           $pstack:poteto-mode build a small feature behind a feature flag. verify it really works.
prototype:         $pstack:poteto-mode build two prototypes of the markdown renderer so we can compare.
                   spawn an agent for each.
multi-phase:       $pstack:poteto-mode open source these skills as a plugin. nothing internal leaks, work
                   in a temp dir, show me the dependency graph first.
overnight run:     $pstack:poteto-mode i'm going to bed. land the stack even if ci flakes. i want
                   everything merged by morning.
babysit:           $pstack:poteto-mode check on pr 123. anything outstanding?
visual parity:     $pstack:poteto-mode the row spacing is too tall when this flag is on. the second image
                   is correct. repro and fix until it matches.
figure it out:     $pstack:poteto-mode i'm stepping away. migrate every caller from the synchronous store
                   to the new async one, keeping behavior identical. i want to trust it was done
                   right when i'm back.
how:               $pstack:how do we cancel runs? do we have an n+1 when we look up every run to cancel?
why:               $pstack:why is this feature flag not on yet?
architect:         design this instrumentation to be high signal with no false positives. $pstack:architect
                   this first.
arena:             $pstack:arena take my prompt to the arena verbatim. i want to compare their proposals
                   with yours.
swarm:             $pstack:swarm check every package under packages/ against its check.sh. one worker per
                   package. one report.
interrogate:       $pstack:interrogate review this pr.
tdd:               $pstack:tdd implement
unslop:            can we unslop and tighten the new changes?
reflect:           $pstack:reflect that took too long. capture what we learned so the next run doesn't
                   repeat it.
show-me-your-work: $pstack:show-me-your-work keep a decision trail i can review when i'm back.
automate-me:       $pstack:automate-me
```

</details>

## collaboration subagents

pstack gives each worker a bounded outcome, file ownership, and only the references it needs. routed skills such as `how`, `why`, `arena`, `swarm`, and `interrogate` define specialized worker prompts.

the [Codex collaboration contract](./skills/poteto-mode/references/codex-tools.md) is the shared rule for capability discovery, model overrides, shared working directories, status, waiting, and interruption.

pstack also preserves [Comment Sicko](./com.cursor/agents/comment-sicko.md). [`$pstack:no-comments`](./skills/no-comments/SKILL.md) loads those rules into a fresh read-only collaboration agent.

## principles

twenty-one short skills, one principle each. the optional [principles index](./skills/poteto-mode/references/full-mode.md) points to them by decision. load the relevant principle when it helps.

<details>
<summary>all twenty-one principles</summary>

| principle | group | rule |
|---|---|---|
| [laziness-protocol](./skills/principle-laziness-protocol/SKILL.md) | core | Bias toward deletion and the smallest change that solves the problem. |
| [foundational-thinking](./skills/principle-foundational-thinking/SKILL.md) | core | Apply before writing logic: choosing core types and data structures, sequencing scaffold-vs-feature work, asking what concurrent actors share. Get the data structures right so downstream code becomes obvious. |
| [redesign-from-first-principles](./skills/principle-redesign-from-first-principles/SKILL.md) | core | Redesign as if the requirement had been a foundational assumption from day one, instead of bolting it on. |
| [subtract-before-you-add](./skills/principle-subtract-before-you-add/SKILL.md) | core | Remove dead weight, redundant validators, and stub references first, then build on the simpler base. |
| [minimize-reader-load](./skills/principle-minimize-reader-load/SKILL.md) | core | Count layers between question and answer, and hidden state in the reader's head; collapse one-caller wrappers and shrink mutable scope. |
| [outcome-oriented-execution](./skills/principle-outcome-oriented-execution/SKILL.md) | core | Apply during planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture; don't preserve smooth intermediate states with throwaway compatibility code. |
| [experience-first](./skills/principle-experience-first/SKILL.md) | core | Choose user delight over implementation convenience; ship fewer polished features over more rough ones. |
| [exhaust-the-design-space](./skills/principle-exhaust-the-design-space/SKILL.md) | core | Build 2-3 competing prototypes and compare side by side before committing. |
| [build-the-lever](./skills/principle-build-the-lever/SKILL.md) | core | Automate repeated work or complex checks when a reusable tool improves consistency and reviewability. Reuse existing tools first. |
| [model-the-domain](./skills/principle-model-the-domain/SKILL.md) | architecture | Encode the domain in a structure instead of scattered conditionals. |
| [boundary-discipline](./skills/principle-boundary-discipline/SKILL.md) | architecture | Concentrate guards at system boundaries (CLI, config, network, external APIs); trust internal types and keep business logic in pure functions. |
| [type-system-discipline](./skills/principle-type-system-discipline/SKILL.md) | architecture | Make illegal states unrepresentable, brand semantic primitives, parse external data at boundaries, refuse to lie to the compiler, exhaust variants, derive from authoritative schemas. |
| [make-operations-idempotent](./skills/principle-make-operations-idempotent/SKILL.md) | architecture | Converge to the same end state regardless of partial prior runs. |
| [migrate-callers-then-delete-legacy-apis](./skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md) | architecture | Migrate callers and delete the old API in the same wave instead of preserving compatibility layers. |
| [separate-before-serializing-shared-state](./skills/principle-separate-before-serializing-shared-state/SKILL.md) | architecture | Eliminate the sharing first; serialize structurally only when one shared writer is a real invariant. |
| [prove-it-works](./skills/principle-prove-it-works/SKILL.md) | verification | Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.'. |
| [fix-root-causes](./skills/principle-fix-root-causes/SKILL.md) | verification | Trace each symptom to its root cause and fix it there; reproduce first, ask why until you reach it, resist nil-check guards that silence crashes. |
| [sequence-verifiable-units](./skills/principle-sequence-verifiable-units/SKILL.md) | verification | Apply to multi-step work (sweeps, migrations, runs of similar edits) and to how you stack commits and PRs. Break work into small units that each end in a verifiable state, check each before the next, and order delivery so the sequence proves itself to a reviewer. |
| [guard-the-context-window](./skills/principle-guard-the-context-window/SKILL.md) | delegation | Route bulk to subagents; keep summaries in the main thread, not raw payloads. |
| [never-block-on-the-human](./skills/principle-never-block-on-the-human/SKILL.md) | delegation | Proceed, present the result, let the human course-correct after the fact; reserve confirmation for irreversible actions. |
| [encode-lessons-in-structure](./skills/principle-encode-lessons-in-structure/SKILL.md) | meta | Encode the rule as a lint, metadata flag, runtime check, or script instead of more text. |

</details>

## companion capabilities

a few workflows use Codex capabilities outside this plugin:

- Codex ships **skill-creator** for authoring skills.
- Browser control and computer use drive web and native products when installed.
- **control-cli** drives CLIs and TUIs when installed.

When a control skill is unavailable, [`$pstack:create-verification-skill`](./skills/create-verification-skill/SKILL.md) builds a repository-local one.

## why are there no planning skills?

codex has a plan mode that works with pstack. but personally, i don't believe in planning. the best spec is code. if you do want a plan, [`$pstack:poteto-mode`](./skills/poteto-mode/SKILL.md) covers it, but it is not the default.

## make it yours

`poteto-mode` is my style. you may not want exactly that.

type [`$pstack:automate-me`](./skills/automate-me/SKILL.md). it mines your recent transcripts, drafts a `<your-name>-mode` skill from how you've actually worked, and routes through pstack underneath. you keep pstack as the base and end up with your own routing skill alongside `poteto-mode`.

models are configurable too. type [`$pstack:setup-pstack`](./skills/setup-pstack/SKILL.md). it detects the models and reasoning efforts exposed to collaboration agents and writes `~/.codex/pstack-models.md`. every routed skill reads it and inherits the parent when a role is absent or stale.

## automations

pstack also ships a dormant [benny automation pack](./com.cursor/automations/benny/). benny triages slack issue reports, then reproduces and fixes confirmed bugs with real ui evidence. its files are not registered as slash skills.

the preserved pack is Cursor-specific source material. Codex recurring work uses thread heartbeat or cron automations. Port the pack's prompts into those automations when you need Benny on Codex; do not treat the Cursor files as active Codex configuration.

## Codex adaptation

The [upstream comparison and Astra tuning notes](./docs/codex-adaptation.md) record what is preserved, what changed, and how to validate future edits. Pstack inherits the parent model by default. The [collaboration contract](./skills/poteto-mode/references/codex-tools.md#choose-models-and-reasoning) gives workload-based effort guidance without changing your active task settings.

## evaluate changes

The [quality suite](./evals/README.md) compares frozen instruction variants on the same model and reasoning level. It provides isolated coding tasks, held-out behavior checks, and a review rubric based on the original engineering standards. Use the [Eval playbook](./skills/poteto-mode/playbooks/eval.md) to run, diagnose, and retest changes before promoting them.

## license

MIT
