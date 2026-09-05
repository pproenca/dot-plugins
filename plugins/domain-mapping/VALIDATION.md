# Validation record

Version: 0.1.0. Date: 2026-09-05. Executed on macOS with Python 3; the runtime requires Python 3.10 or newer.

Relocated into dot-plugins on the same date and aligned with its 0.16.3 shared release version. The import adds the portable manifest and both catalog entries, and applies the repository's Ruff formatting and import rules. Validation in a staging copy of the destination repository passed 238 repository tests with 22 skipped, all 33 plugin tests, Ruff, and the Codex plugin validator. The repository suite now runs the plugin behavioral suite in CI. The repository suite also validates portable plugin conformance and catalog agreement. The native Codex CLI 0.153.0 loader also discovered both skills and resolved the included icon. The relocation operation was tested in isolated fixtures for successful installation and rollback after a forced reinstall failure. No graph database integration was added by the relocation.

## Automated verification

`python3 -m unittest discover -s tests -v` passed all 33 tests. Tests exercise actual model audits and CLI operations, including:

- Empty and malformed models cannot produce vacuous success; duplicate JSON keys are rejected.
- Evidence drift reopens dependent claims; unsupported custom aspects remain outstanding.
- Shared lineage, identical evidence bytes, and a run serving as its own expected result cannot establish independent verification.
- Later failures, conflicting timestamps, future results, and changed model or method contracts cannot retain a passing result.
- Exclusive writer locks, interrupted publication/replacement, permission preservation, and report reads after lock acquisition protect local artifacts.
- Checkpoints are content-addressed; reports cannot overwrite evidence or authored notes; symlink escapes and duplicate lesson IDs are rejected.

The plugin manifest and both skills pass the plugin-creator and skill-creator validators. Markdown relative links were checked for existing targets.

## Independent workflow exercise

An independent agent used map-domain on a fictional Cedar appointment-cancellation case with conflicting product notes. Its actual artifacts contained a raw narrative, a model with nine concepts and eight relations, three unexecuted scenarios, an audit, a checkpoint, and proposed next investigations. Inspection confirmed that it preserved the contradiction, did not invent execution or practitioner review, and kept unresolved work visible. The model passed structural validation, not domain completion.

The exercise exposed wording that could exclude downstream waitlist behavior merely because it did not share the cancellation transaction. The discovery reference now distinguishes causal relevance from transactional atomicity. A separate held-out follow-up correctly kept the unresolved waitlist handoff visible while allowing a narrower local cancellation cycle to be described separately.

The eight rubric cases in `evals/cases.json` are supplied for future comparative evaluations. A complete independent run of all eight cases, across multiple models and repetitions, has not been performed. The workflow trial and targeted follow-up are initial evidence, not a measured general success rate.

Independent code and adversarial review identified the integrity and persistence counterexamples covered by the regressions above. These findings were corrected before installation.

## Limits and next validation

Linux and Windows were not executed in this session. The helper uses standard Python path/process APIs; new-artifact publication requires a filesystem supporting hard links. POSIX permission preservation has a platform-specific test. Local locks coordinate cooperating plugin writers only; direct editors must pause during writes. Process interruption tests do not establish power-loss durability.

No production UI/API experiment, full Cliniko corpus conversion, PostgreSQL/AGE integration, or independent reimplementation was performed. The helper verifies local record integrity and reported outcomes. It cannot authenticate test execution, participant expertise, semantic truth, remote source freshness, or universal completeness.

The next meaningful product validation is a practitioner walkthrough and independent implementation of one bounded process with a cross-context handoff. Track the clarifications that implementation requires, turn omissions into redacted regression cases, and compare any proposed method change with this preserved baseline.
