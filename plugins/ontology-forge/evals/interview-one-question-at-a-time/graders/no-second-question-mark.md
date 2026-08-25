---
type: regex
pattern: "\\?[\\s\\S]*\\?"
target: last_message
match: not_contains
---

The plugin's rule is "one question per message, **never a second question mark**." That is a
guard against a second, not a requirement for a first — a question can be asked with no question
mark at all ("What decisions should it support — describe two or three concretely."), and this
suite has produced exactly that.

So the deterministic check is *at most one*, not *exactly one*: the pattern matches a question
mark followed later by another, and the grader requires that pattern to be absent. Zero marks
and one mark both pass; two or more is the batching failure under test.

Whether the one question is really one question — rather than two joined by "and" — is
`compound-question`, which needs judgement this cannot supply.
