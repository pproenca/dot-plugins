---
type: llm
---

Beyond the eight anti-patterns, the fixture plants structural and platform defects.
Credit the response for each it catches:

- `facility.inspectionScore` is `derived: true` **and** `required: true` — not allowed.
- The same property also carries a `range` constraint — derived properties cannot.
- `facility.primaryKey` points at `derivedFacilityKey`, which is derived — not allowed.
- Its `via` path is four hops; the limit is three.
- `facility` implements `inspectable` and `schedulable`, neither of which is defined.
- `facility` has five `address*` properties that should be one struct.
- `employeeVenture` is a direct link whose description names role, start date and allocation — it needs to be object-backed.
- `publicPatient` and `restrictedPatient` duplicate a schema for security.
- `directReportCount` and `openWorkOrderCount` are manual counts that should derive from links.

PASS if **at least four** are caught, including at least one of the four
derived-property violations on `facility.inspectionScore`.
