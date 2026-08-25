---
type: llm
---

An `llm` grader sees the final message, not the contract file, and the file's name is chosen by
the response so it cannot be pinned with `focus: {source: file}`. Field-level conformance is
therefore graded by `validator-passed`, which runs the real v3.1.0 schema. This rubric grades
what only a reader of the message can judge: whether the response reports that check honestly
and understands what it wrote.

**PASS** if the response states the validator's actual result rather than asserting conformance
on its own authority, and says where the contract was written.

**FAIL** if it claims the contract conforms to ODCS without reference to having checked, or
reports a clean result the trace does not support. Claiming conformance is the failure this
case exists to catch; the standard is strict precisely because plausible-looking guesses pass
human review.

**FAIL** if it describes writing a field the standard does not define — `nullable`, `columns`,
`dataType`, a bare `type` on a property — as though that were acceptable, or if it names a
`logicalType` outside `string, date, timestamp, time, number, integer, object, array, boolean`.

Credit for saying out loud what a contract cannot express: ODCS has no interface and no action
type, so a property populated by an action must be called out or the contract reads as though
the source supplies it. The fixture stages exactly that case — `creditRating` is action-populated
with no source column.

Credit for `status` being one of `proposed`, `draft`, `active`, `deprecated`, `retired`. Those
are examples in the schema rather than an enum, so the validator cannot catch a wrong one and
this rubric is the only thing that will.
