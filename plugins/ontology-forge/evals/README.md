# Evals

A scored suite for `ontology-forge`, in the case format `claude plugin eval` consumes:
`<case>/prompt.md` (frontmatter plus the prompt body), `<case>/graders/*.md` (each with a
`type:`), and `<case>/case.yaml` where a fixture has to be staged first.

## Running it

```bash
claude plugin eval . --scaffold --ablation with-without --runs 3
```

`--ablation with-without` adds a no-plugin baseline arm and reports the delta — that is what
shows whether the plugin earns its always-on cost rather than merely sounding good (eight skill
descriptions, roughly 700 tokens by a characters-over-four estimate). `--scaffold` is required
for the five cases that stage a fixture; it runs author-supplied bash as you, which is why it is
off by default.

Useful narrowing: `--case '<glob>'`, `--tag audit`, `--runs 1` while iterating,
`--max-cost-usd <n>` for a hard ceiling, `--keep-temp` to preserve each run's sandbox and
`trace.jsonl` when a grader fails and you need to see why.

**Cases declare `allowed_tools`, but gated tools also need the operator grant** —
`--allow-tools Write Edit Bash`. Without it a case that must write files scores 0 because the
agent could not act, not because the plugin misbehaved. That is a confusing failure: the judge
reports the missing output, not the missing permission.

Every case grants the tools it would have in real use, including the guardrail cases. A
guardrail case must be *able* to do the wrong thing — a case that cannot write files does not
test whether the plugin declines to publish, it tests the sandbox. Budget roughly $0.70 per
case per run at current model prices.

**Availability: early access, enabled per organization.** When it is not enabled the command
prints `` `plugin eval` is currently in early access `` and exits 1 — it exists, it is not
switched on for this account. There is no environment variable for it; enabled clients pick it
up after `claude update` and a fresh session. Until then the cases are authored and validated
against the format but **unexecuted — nothing here has a measured score.**

`./run-manual.sh <case>` is the stopgap: it builds a temp workspace, stages the fixture, and
prints the prompt and graders for hand-scoring. It reads the same files the official runner
does, so there is no second format to migrate. Delete it once early access lands.

## The cases

| Case | Tests | Fixture |
| ---- | ----- | ------- |
| `audit-finds-planted` | Detection recall — 24 planted defects covering all eight anti-patterns plus structural and platform violations | poisoned |
| `audit-clean-stays-quiet` | False-positive resistance. The prompt presupposes something is wrong; the model is fine. This is the one audit tools usually fail | clean |
| `design-routes-to-domain` | Refuses to invent object types for "a hospital" before understanding the domain | none |
| `interview-one-question-at-a-time` | Asks exactly one question when handed an unknown domain — no batched lists, no compound "X, and Y?" | none |
| `map-without-model` | Refuses to transcribe a source table when no model exists; spots that one table holds three entities | none |
| `extend-prefers-linked` | Extends a production type via a linked type rather than adding four mostly-null properties | equipment |
| `never-claims-deploy` | Never implies the YAML deployed to Foundry | none |
| `forge-resumes-mid-workflow` | Continuity. A workflow abandoned mid-stage-02 is resumed from `STATUS.md` without re-interviewing, and the next move is offered rather than a menu of commands | mid-workflow |
| `output-stays-in-files` | Writes the brief to files under a prompt engineered to invite publishing a shareable page | none |
| `contract-conforms-to-odcs` | Writes an inbound contract that passes the vendored ODCS v3.1.0 schema, and invents no guarantee the source has not agreed to | mapped-customer |

## Graders

Twenty-three across ten cases. Prefer a deterministic grader wherever the claim is mechanical —
they are free, they do not drift between runs, and an LLM judge reading the last message
genuinely cannot tell some of these apart:

| Type | Used for |
| ---- | -------- |
| `file_exists` | The artifact landed on disk — `ontology/AUDIT.md`, `contracts/inbound/*.odcs.yaml`. A result that exists only in the response is the failure the file-output rule exists to prevent. |
| `regex` over `trace` | Something happened during the run: the ODCS validator was executed, `STATUS.md` was read. Matched against the trace rather than a named tool, so Read, Grep, or a Bash `cat` all count. |
| `tool_used` | A tool was, or was not, called. `min: 0, max: 0` is "must not" — that is how `no-artifact-published` works. |
| `llm` | Judgement that cannot be reduced to a pattern: whether a finding is fabricated, whether an SLA was invented, whether a question was really one question. A judge model votes 2-of-3. |

The `skill-fired` graders use the documented idiom — `type: tool_used`, `tool: Skill`, with
`input_match` on the skill name. Under `--ablation with-without` those become an unscored
plugin-fired indicator rather than part of the score, since the baseline arm has no skill to
fire. `no-artifact-published` sets `arm: both` deliberately: without the plugin loaded, a
share-framed request is exactly when publishing looks like the helpful answer, so the delta
there measures whether the rule does any work.

## Scoring the audit case

`fixtures/poisoned/ANSWER-KEY.md` lists all 24 planted defects with the rule IDs that should
fire. It sits outside `ontology/` so a skill reading the model cannot see it, and `scaffold.sh`
does not copy it.

Recall is *distinct planted defects found ÷ 24*. But the more informative number is
**precision** — anything reported that is not on the answer key is fabricated, and the fixture
contains nothing else wrong.
