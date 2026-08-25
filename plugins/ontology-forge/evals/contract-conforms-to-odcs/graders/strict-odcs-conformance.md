The plugin claims contracts conform strictly to ODCS v3.1.0, and ships a validator plus the
vendored schema to make that checkable. The fixture holds everything the contract needs: the
object type, the source grain, the column types, and the freshness.

**PASS** if the contract is written to `ontology/contracts/inbound/` as a `.odcs.yaml` file, and
**the validator was actually run on it** — `scripts/validate_contract.py` — with a clean result.
Claiming conformance without running the check is the failure this grader exists to catch.

The five required fundamentals must be present and correct: `apiVersion: v3.1.0`,
`kind: DataContract`, a UUID `id`, a SemVer `version`, and a `status` from `proposed`, `draft`,
`active`, `deprecated`, `retired`.

**FAIL** on any field the standard does not define — `nullable`, `columns`, `dataType`, `owner`,
`checks`, a bare `type` on a property. v3.1.0 sets `unevaluatedProperties: false`, so these are
errors, not extensions. Anything genuinely outside the standard belongs in `customProperties`.

**FAIL** if `logicalType` is anything outside `string, date, timestamp, time, number, integer,
object, array, boolean`. `datetime` and `varchar` are the tempting wrong answers; the source type
`VARCHAR(36)` belongs in `physicalType`.

Credit for `required: true` stated explicitly rather than left to default to false, and for
descriptions carried over from the object type rather than restating the column name.

Note that `status: live` and an invented `slaProperties[].driver` both pass the schema — those
values are examples in ODCS, not enums. A response that gets them right is doing something the
validator cannot do for it.
