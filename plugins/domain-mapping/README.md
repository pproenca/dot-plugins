# Domain mapping

A Codex plugin in the dot-plugins repository for collaborative EventStorming, recursive domain investigation, and continuously checked behavioral specifications.

The plugin keeps business stories and unresolved disagreements alongside a structured model. It derives missing questions, checks evidence integrity, reopens stale dependencies, and records conformance results against a versioned contract. It uses Python 3.10+ with no third-party dependencies. It does not install a database or contact any external system.

## Use it

After enabling the plugin, start a new task with one of these requests:

- “Use map-domain to map this business process. Start with the narrative and an independent discovery inventory.”
- “Use map-domain to audit this existing model, reopen stale claims, and explain the next experiments.”
- “Use improve-mapping to reproduce this missed condition and evaluate a correction to the method.”

Start with one complete process that crosses a responsibility boundary. Expand after a walkthrough and an independent implementation exercise show that the specification communicates the required behavior.

The [map-domain skill](skills/map-domain/SKILL.md) owns the workflow. Its [model format](skills/map-domain/references/model-format.md) documents the helper commands and data model. [Principles](skills/map-domain/references/principles.md) preserve key definitions and cite Brandolini's original guidance. The [improvement skill](skills/improve-mapping/SKILL.md) defines regression-based changes and rollback.

## What is automatic

- Mandatory question generation per concept kind, plus explicit custom claims.
- Validation of types, identifiers, references, local evidence paths and hashes.
- Reopening of stale claims and their dependencies.
- Invalidation of recorded runs and reviews after contract changes.
- Separate inventory, obligation, and recorded-scenario counts.
- Deterministic Markdown reports and immutable model checkpoints.

## What requires investigation

The checker cannot prove that a paragraph states the right rule, that all behavior was discovered, or that a recorded test actually happened. Agents and practitioners must perform source investigation, UI/API experiments, domain walkthroughs, counterexample review, and independent conformance work. Different evidence IDs or agent opinions do not establish independent evidence.

No background daemon, self-updating hook, or scheduled task is installed. Safe recovery is invoked on each workflow resume/change through recomputation, evidence reinspection, and revalidation. Reusable method changes require a reproduced failure, evaluated candidate, preserved baseline, and recorded promotion. The workflow never heals by weakening completion criteria.

## Storage and history

Use one project-owned model per system-version/condition envelope. Keep raw stories, redacted captures, checkpoints, lessons, and proposal files beside it. Keep the installed plugin independent of project evidence. Version control provides review history; checkpoints preserve accepted model snapshots.

Graph storage is the next architecture decision. Evaluate traversal queries, relationship constraints, concurrent curation, provenance, and dependency invalidation before deciding whether PostgreSQL/AGE or another graph store should own the canonical model or hold a projection. The current JSON helper is the starting implementation; it does not settle that decision. Preserve portable export and independently executable behavioral contracts whichever storage model is selected.

Development lives in `plugins/domain-mapping/` in the dot-plugins repository. Its portable manifest, Codex manifest, and client catalog entries follow the repository's shared release version.

## Test

```text
python -m unittest discover -s tests -v
python scripts/domain_map.py --help
```

[Forward-evaluation cases](evals/cases.json) exercise instruction-level pitfalls beyond script correctness. Give their prompts to an independent evaluator without the expected criteria, then inspect the actual response. These cases are not automatically executed by the helper. See [VALIDATION.md](VALIDATION.md) for verification performed on this version.

The catalog icon is rendered from `assets/icon.svg`. Regenerate it from this plugin directory with `rsvg-convert --width 256 --height 256 --output assets/icon.png assets/icon.svg`.
