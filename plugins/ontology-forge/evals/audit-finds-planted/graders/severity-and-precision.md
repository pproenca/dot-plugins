---
type: llm
---

Two quality checks on the report itself.

**Severity sanity.** The God Object, the silo patterns, and the security-duplicated
types should be ranked most severe. Misnomers and missing descriptions should be
ranked least severe. FAIL if a missing description outranks the God Object.

**No fabrication.** A finding counts as fabricated only if it is **untrue of the
fixture files** — not merely because it is absent from the graders above. Check the
claim against the files before calling it a false positive.

The fixture is known to contain correct findings beyond the planted list: broken
references from the `set*` actions to properties `hrSystemEmployee` does not declare,
a `venture` type that does not exist, undefined link types in `facility`'s `via`
chains, four competing date-naming conventions, and identifiers used as title
properties. All are true. Credit them.

FAIL only if the response makes more than two claims that are demonstrably false of
the files — an audit that invents problems to look thorough is worse than one that
misses some.
