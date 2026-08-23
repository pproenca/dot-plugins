---
name: audit-ontology
description: "Use when /audit-ontology, 'audit the ontology', 'review this object model', 'check for anti-patterns', or before promoting a model to production. Fans out parallel reviewers across the anti-pattern catalog and structural guidance, verifies each finding against the actual files, and reports ranked violations with the evidence and the fix."
metadata:
  disable-model-invocation: "true"
---

# Audit the ontology

Review an existing model against the anti-pattern catalog and the structural guidance. The output is a ranked findings report, every finding backed by evidence from the files.

Read [anti-patterns.md](../ontology-forge/references/anti-patterns.md), [structural-guidance.md](../ontology-forge/references/structural-guidance.md), and [naming.md](../ontology-forge/references/naming.md) before dispatching.

## Start

Open a todolist with one entry per phase.

1. Inventory
2. Fan out
3. Verify
4. Rank
5. Report

## Phase 1: Inventory

Locate the model. Default to `ontology/`; ask if the user's model lives elsewhere or is described in another format.

Build an index before reviewing: every object type with its property count and null-tolerant property count, every link type with cardinality and backing, every interface with its implementors, every action type with its target and the properties it modifies. Read `DECISIONS.md` — a documented tradeoff is not a finding, and reporting one as a violation wastes the user's attention.

If there is no model on disk, ask the user to point at one. Do not audit an ontology from a verbal description.

## Phase 2: Fan out

Dispatch one subagent per lane, in parallel, in a single message. Each gets the index, the paths, and the relevant reference file. Each returns structured findings: anti-pattern name, location, evidence quoted from the file, severity, and proposed fix.

| Lane | Hunts for | Method |
| ---- | --------- | ------ |
| **Duplication** | System Silos, Department Silos, rule-of-three violations | Compare property sets across all object types. Flag heavy overlap, source-system or department words in type names, and types sharing a primary-key semantic. |
| **Type shape** | Kitchen Sink, God Object, Time Machine | Per type: technical columns with no business meaning, sparse or conditional properties, a `type` property that switches other properties' meaning, version or year tokens in names, property count far above sibling types. |
| **Behaviour** | Golden Hammer, Action Sprawl | Per action type: does a human decide anything? Does the name read `Set X`? How many actions target one type? Is logic placed in the layer the placement table prescribes? |
| **Naming** | Misnomer, missing descriptions | Every element name against the naming table and the generic-name blocklist. Every element for a description that states meaning and valid values. Both directions of every link for readability. |
| **Structure** | Normalization, link modelling, interfaces, security | The same fact stored twice; manually maintained counts; links that are foreign keys in disguise; relationship metadata that wants an object-backed link; shared shape that should be an interface; types duplicated for security. |

Tell each subagent to quote the file and line it is reading from, and to report nothing it cannot evidence. A plausible-sounding finding with no file behind it is worse than a missed one.

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

## Fixing

Do not apply fixes during the audit. When the user wants them applied, work through the findings in severity order with [extend-ontology](../extend-ontology/SKILL.md), which will check blast radius before changing an established type.
