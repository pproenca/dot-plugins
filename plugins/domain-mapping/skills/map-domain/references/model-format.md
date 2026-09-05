# Portable model format and commands

The v1 format is a normalized JSON document with explicit references. It can be projected into PostgreSQL or a property graph later. v0.1 does not install a database, run experiments, crawl remote sources, or translate an existing corpus automatically.

Run the helper with Python 3.10+ using its actual absolute path:

```text
python /PLUGIN_ROOT/scripts/domain_map.py init /PROJECT/domain-map/model.json --system Example --description "Booking cancellation, specified roles and settings"
python /PLUGIN_ROOT/scripts/domain_map.py audit /PROJECT/domain-map/model.json
python /PLUGIN_ROOT/scripts/domain_map.py frontier /PROJECT/domain-map/model.json
python /PLUGIN_ROOT/scripts/domain_map.py report /PROJECT/domain-map/model.json
python /PLUGIN_ROOT/scripts/domain_map.py checkpoint /PROJECT/domain-map/model.json
```

`/PLUGIN_ROOT` and `/PROJECT` stand for resolved absolute paths, not environment variables. `report` prints Markdown to stdout by default. `report --output PATH` atomically creates a new report, or replaces it only with `--replace`; it refuses to overwrite the canonical model, evidence, or plugin source. `audit` is read-only. Exit codes: 0 means the requested operation succeeded, 1 means an audit/frontier has outstanding work, 2 means malformed input or an operational error. A frontier with work returns 1 deliberately.

## Root and scope

Required root keys: `schema_version`, `scope`, `concepts`, `relations`, `claims`, `evidence`, `inventory`, `scenarios`, `runs`, `reviews`. `schema_version` is 1. Every collection is an array and each record has a globally unique nonblank `id`.

Scope fields are nonblank `id`, `revision`, `system`, `system_version`, `perspective`, and `description`, plus string arrays `conditions` and `exclusions`. Perspective is `observed` or `intended`. Initialization leaves `system_version` as `unresolved`, which must be investigated. Scope conditions explicitly name relevant roles, regions, configuration, history, clock, and external-system assumptions. Split models when their applicability envelopes differ. An empty list is not proof all variants were inspected.

## Records

| Collection | Required fields beyond id |
| --- | --- |
| concepts | `kind`, `name`, `context` as strings. Kinds and mandatory question aspects come from `scripts/obligations.json`. |
| relations | `source`, `target` concept IDs; `type`; `claim_ids`. An empty supporting list leaves the relation unresolved. |
| claims | `concept`, `aspect`, `statement`, `perspective`, `status`, `evidence_ids`, `depends_on`. Dependencies reference claims. |
| evidence | `kind`, `path`, `sha256`, `lineage`, `source`, `locator`, `captured_at`. Captured files are relative to the model directory. |
| inventory | `kind`, `description`, `disposition`, `concept_ids`, `evidence_ids`, `rationale`. |
| scenarios | `name`, `claim_ids`, `given`, `when`, `then`, `oracle_evidence_ids`. Given/when/then are precise nonblank prose strings. |
| runs | `scenario_id`, `result`, `basis`, `evidence_ids`, `recorded_at`. |
| reviews | `kind`, `result`, `basis`, `evidence_ids`, `recorded_at`. |

Relation types: `initiates`, `handles`, `produces`, `triggers`, `informs`, `governs`, `transitions`, `references`, `belongs_to`, `crosses`, `terminates`, `follows`. These encode the intended meaning of the claim; the checker checks references, not the business truth or every source/target type pairing. `follows` is chronological; `belongs_to` is not automatically a foreign key or transaction.

Claim perspective: `observed`, `intended`, or `proposed`. Claim status: `hypothesis`, `supported`, `contradicted`, or `not_applicable`. A proposed claim cannot close an observed/intended obligation. Every supported or N/A claim needs evidence. A N/A statement explains why the aspect is inapplicable. Keep alternatives and domain-specific aspects; required topics are only the default floor. Do not delete contrary evidence to make a claim supported.

Evidence kinds: `source`, `observation`, `documentation`, `data`, `verification`, `review`. `source` identifies the original system/version or source URL; `locator` points to the relevant original section, source range, or observation; `lineage` names the originating source family. Reusing an originating schema through generated docs does not create a new lineage. `captured_at` and recorded timestamps must be ISO 8601 with an explicit timezone. Hashes are lowercase SHA-256 hex.

Evidence paths use relative forward-slash segments beneath the model directory. Parent traversal, absolute paths, backslashes, and escaping symlinks are rejected. Copy appropriately redacted authorized captures into that directory; an external URL alone cannot be revalidated by this offline checker. It detects local capture drift, not remote source changes.

Inventory disposition is `mapped`, `unresolved`, or `excluded`. Mapped entries need concept references and current evidence. Excluded entries need evidence and rationale; exclusions remain separately counted. They are not verified behavior.

Scenario oracles must cite evidence. Shared lineage with supporting claims is conservatively flagged for review. A distinct lineage is not proof of independence. Preserve independent raw expected outcomes and examiner judgment.

Results are `passed`, `failed`, or `blocked`. Reviews use `walkthrough`, `blind_inventory`, or `challenge`. Verification records need `verification` evidence; review records need `review` evidence. Keep actual execution/review artifacts with environment, participants, adapter revision, fixtures, expected/observed results, and limitations. A stamp does not execute or authenticate a check.

## Recording actual results

After an actual run/review has finished and its captured artifact has been registered in `evidence`, record it:

```text
python /PLUGIN_ROOT/scripts/domain_map.py record-run MODEL --id run-001 --scenario scenario-001 --result passed --evidence-id evidence-run-001
python /PLUGIN_ROOT/scripts/domain_map.py record-review MODEL --id review-001 --kind challenge --result failed --evidence-id evidence-review-001
```

Use unique IDs; these commands append and atomically replace the model under an exclusive writer lock. They do not edit other records. Interrupted writes leave the original model intact. A stale lock is an explicit blocker: inspect whether its owning operation is still active before removing it manually. Workers should send proposals to the curator instead of concurrently editing the canonical document.

The lock coordinates plugin writers only. Direct editors must pause while a write command runs. The final content comparison detects earlier outside edits but is not an atomic compare-and-swap against non-cooperating writers. Keep checkpoints/version control and one curator. A future-dated result beyond five minutes of clock skew blocks audit rather than masking later failures; tests can supply a fixed audit clock.

`basis` is computed from the scope, model contracts, obligation definitions, supporting evidence metadata, and the plugin manifest, Python scripts, and skill Markdown contents. It excludes run/review history and their unreferenced artifacts. Contract or method edits invalidate all recorded results conservatively, including wording changes to the skills. Array record ordering does not change the basis. Freshness additionally checks actual captured bytes and transitive dependencies. Local snapshots and external execution environments are different; the latter still require explicit reobservation.

New artifacts are written and flushed to a temporary file, then published with an atomic no-overwrite hard link. Filesystems without hard-link support fail safely; use a supported local filesystem. Replacements preserve existing permission bits. This protects against interrupted process writes, not every power-loss or storage-device failure. Saved reports acquire the model lock before reading the model; they are snapshots and must be regenerated after later changes.

`checkpoint` creates an immutable content-addressed copy under `checkpoints/`; repeated identical calls are harmless. Keep historical evidence files in version control or an appropriate artifact store. A model checkpoint contains references, not a backup of their files.

## Lessons and reports

`lesson` appends a proposal into `lessons.jsonl` under the same writer lock. It stores the current basis, time, failure, proposal, and evidence references. It does not modify plugin instructions or promote a lesson into truth. See the improve-mapping skill for promotion and rollback.

Audit output includes issues, a deterministic frontier, separate counts, and `recorded_checks_satisfied`. No overall completeness percentage is emitted. Reports are projections; regenerate them after accepted changes. Unfinished source inspection, expert review, and portable implementation remain explicit responsibilities beyond the record checker.
