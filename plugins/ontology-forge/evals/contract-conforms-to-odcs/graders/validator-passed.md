---
type: regex
pattern: "[1-9]\\d*/\\d+ conformant with ODCS"
target: trace
match: contains
---

`validator-was-run` proves the validator was invoked. It does not prove it passed — a run that
executed the check, saw errors, and wrote the contract anyway satisfies it.

This closes that gap. The validator prints `N/M conformant with ODCS v3.1.0` and appends
`— N error(s)` when anything failed, so a clean run starts the count at 1 or more and a failed
one starts at 0. Requiring a non-zero numerator is the difference between "checked" and
"passed".
