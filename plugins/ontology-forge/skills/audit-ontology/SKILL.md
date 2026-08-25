---
name: audit-ontology
description: "Use when /audit-ontology, 'audit the ontology', 'review this object model', 'check for anti-patterns', or before promoting a model to production. Fans out parallel reviewers across the anti-pattern catalog and structural guidance, verifies each finding against the actual files, and reports ranked violations with the evidence and the fix."
---

# Audit the ontology

Review an existing model against the anti-pattern catalog and the structural guidance. The output is a ranked findings report, every finding backed by evidence from the files.

Read [detection-rules.md](../ontology-forge/references/detection-rules.md) first — it turns every indicator below into a computable check. Then [anti-patterns.md](../ontology-forge/references/anti-patterns.md), [structural-guidance.md](../ontology-forge/references/structural-guidance.md), and [naming.md](../ontology-forge/references/naming.md) for what each hit means and how to fix it.

## Start

Read `ontology/STATUS.md` first. It carries the position, the open questions, and the
thin-evidence decisions from earlier stages — the format is in
[status-format.md](../ontology-forge/references/status-format.md). If it does not exist,
reconstruct it from what is on disk using the derivation table there. Starting without it
means re-asking questions the user has already answered.

Open a todolist with one entry per phase.

1. Inventory
2. Fan out
3. Verify
4. Rank
5. Report

## Phase 1: Inventory

Locate the model. Default to `ontology/`; ask if the user's model lives elsewhere or is described in another format.

Build an index before reviewing: every object type with its property count and null-tolerant property count, every link type with cardinality and backing, every interface with its implementors, every action type with its target and the properties it modifies. Read `DECISIONS.md` — a documented tradeoff is not a finding, and reporting one as a violation wastes the user's attention.

If `ontology/contracts/` exists, run `../write-contracts/scripts/validate_contract.py` over it and
carry the result into the report. A contract that no longer conforms to ODCS v3.1.0 is a finding
the lanes below cannot see, because they read the ontology YAML rather than the contracts.

If there is no model on disk, ask the user to point at one. Do not audit an ontology from a verbal description.

## Phase 2: Fan out

Dispatch one subagent per lane, in parallel, in a single message. Each gets the index, the paths, and the relevant reference file. Each returns structured findings: anti-pattern name, location, evidence quoted from the file, severity, and proposed fix.

**Below roughly 30 files, run the lanes inline instead.** Fan-out exists to keep a large model out of the main context; on a small one the subagent overhead buys nothing and reading every file directly is more accurate. Say which way you ran it and why, so the reader knows whether any file went unread.

| Lane | Hunts for | Rules |
| ---- | --------- | ----- |
| **Duplication** | System Silos, Department Silos, rule-of-three violations | `DUP-1` … `DUP-5` |
| **Type shape** | Kitchen Sink, God Object, Time Machine, undocumented elements | `SHAPE-1` … `SHAPE-9` |
| **Behaviour** | Golden Hammer, Action Sprawl, logic in the wrong layer | `ACT-1` … `ACT-7` |
| **Naming** | Misnomer, missing descriptions, inconsistent conventions | `NAME-1` … `NAME-7` |
| **Structure** | Normalization, link modelling, structs, interfaces, security | `STRUCT-1` … `STRUCT-10` |
| **Platform** | Specifications the platform cannot express — derived-property and reducer misuse, cross-ontology links | `PLAT-1` … `PLAT-9` |
| **Referential integrity** | Elements naming elements that do not exist | `REF-1` … `REF-7` |

Each lane runs its rules from [detection-rules.md](../ontology-forge/references/detection-rules.md) against the files, then reads every hit in context before reporting it. A rule firing is a reason to open the file, never a finding on its own — the thresholds are heuristics, and a model may violate one deliberately.

Tell each subagent to report, per finding: the rule ID that fired, the file and line, the computed value against the threshold, and the anti-pattern it suggests. Nothing gets reported that cannot be evidenced from a file. A plausible-sounding finding with no file behind it is worse than a missed one.

## Phase 3: Verify

Findings arrive over-inclusive. Check each one yourself against the actual file before it reaches the report:

- Does the evidence say what the finding claims?
- Is it already recorded as an accepted tradeoff in `DECISIONS.md`? Then it is not a finding — note it as a standing tradeoff instead.
- Is the same problem reported by several lanes? Merge into one finding.
- Would the proposed fix create a different anti-pattern? Splitting a God Object into types with no interface produces duplication instead.

Drop anything that does not survive. An audit that cries wolf gets ignored on the next run.

## Phase 4: Rank

| Severity | Meaning |
| -------- | ------- |
| **Critical** | Wrong semantics, or a shape that breaks as data grows. God Object, System Silos, one fact stored twice, types duplicated for security. |
| **Major** | Real cost to users or maintainers, no correctness failure. Action Sprawl, Kitchen Sink, Time Machine, Golden Hammer. |
| **Minor** | Clarity and consistency. Misnomers, missing descriptions, inconsistent date naming. |

Within a severity, order by how expensive the fix becomes if deferred. Renaming before applications are built on a type is cheap; afterwards it is a breaking change — so a naming finding on a new type outranks one on a type nothing consumes yet.

## Phase 5: Report

Write `ontology/AUDIT.md`, and summarize the critical findings in the response.

```markdown
# Ontology audit

**Reviewed:** N object types, N link types, N interfaces, N action types.

## Summary
Two or three sentences on the model's overall health.

## Critical
### [Anti-pattern] — [element]
**Rule:** SHAPE-1 (42 properties vs median 11)
**Where:** path/to/file.yaml
**Evidence:** what is in the file.
**Why it matters:** the consequence, in this model, not in general.
**Fix:** the specific change.

## Major
## Minor

## Standing tradeoffs
Accepted compromises found in DECISIONS.md, with the condition that should
trigger revisiting each.

## Not reviewed
What the audit could not see — source mappings absent, security not expressed
in the files, interfaces referenced but not defined.
```

Be direct about severity. Report a healthy model as healthy — inventing findings to look thorough trains the user to ignore the next audit. If the model is good, say so and list only what would make it better.

## Finish

Update `ontology/STATUS.md` — see [status-format.md](../ontology-forge/references/status-format.md):

- Record that an audit ran, when, and the count at each severity.
- Every critical and major finding goes under **Open questions** until it is fixed or accepted.
  A finding that lives only in `AUDIT.md` is one `git pull` away from being invisible.
- Set **Next** to `/ontology-forge:extend-ontology` when there are findings to apply.

Hand back to [forge](../forge/SKILL.md) if it invoked this stage.

## Fixing

Do not apply fixes during the audit. When the user wants them applied, work through the findings in severity order with [extend-ontology](../extend-ontology/SKILL.md), which will check blast radius before changing an established type.

## Where the report goes

`ontology/AUDIT.md`, as a file in the repository. Do not publish the audit as an artifact or
render it as a web page, however much a findings report invites it. The audit is reviewed in a
diff next to the model it describes, and it is stale the moment the model changes — a published
copy keeps asserting findings that have already been fixed.
