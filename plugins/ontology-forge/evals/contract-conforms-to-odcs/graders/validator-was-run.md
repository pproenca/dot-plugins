---
type: regex
pattern: validate_contract\.py
target: trace
match: contains
---

The skill requires the validator to run before a contract is reported written. Claiming ODCS
conformance without running the check is the failure this grader catches, and it is a fact
about the trace rather than a judgement about the prose — an LLM judge reading the last
message cannot tell a run validator from a claimed one.
