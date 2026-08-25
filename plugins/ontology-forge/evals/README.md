# Evals

A scored suite for `ontology-forge`, in the layout `claude plugin eval` consumes:
one directory per case, holding `prompt.md` and `graders/*.md`.

## Status

**`claude plugin eval` is gated behind early access and was not runnable on the
account that authored this suite:**

```
$ claude plugin eval .
`plugin eval` is currently in early access
```

So these cases are **authored but unexecuted**. Nothing here has a measured score.
When early access is enabled, run:

```bash
claude plugin eval ontology-forge --ablation with-without --runs 3
```

`--ablation with-without` adds a no-plugin baseline arm and reports the delta —
that is what shows whether the plugin earns its always-on cost rather than merely
sounding good — eight skill descriptions, roughly 700 tokens by a characters-over-four
estimate. Graders marked `with-only` (the `tool_used: Skill` ones) are
plugin-fired indicators rather than part of the score.

Five cases need a fixture staged into the working directory first. Each ships a
`scaffold.sh`; wire them to `scaffold_script` in a `case.yaml` and pass `--scaffold`,
or use the manual runner below.

## Running manually, today

`./run-manual.sh <case>` builds a temp workspace, stages the fixture, and prints the
prompt plus its grading criteria. Drive Claude in that directory, then score the
response by hand against the graders.

```bash
./run-manual.sh audit-finds-planted
./run-manual.sh --list
```

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

## Scoring the audit case

`fixtures/poisoned/ANSWER-KEY.md` lists all 24 planted defects with the rule IDs that
should fire. It sits outside `ontology/` so a skill reading the model cannot see it,
and `scaffold.sh` does not copy it.

Recall is *distinct planted defects found ÷ 24*. But the more informative number is
**precision** — anything reported that is not on the answer key is fabricated, and
the fixture contains nothing else wrong.
