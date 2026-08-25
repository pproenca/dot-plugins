---
type: llm
---

This is the open-for-extension principle stated as a concrete task. The core type is
in production with dependent consumers, and the new fields would be null for roughly
80% of instances.

**PASS** if the response proposes a **new linked object type** carrying the
certification data — and optionally an interface such as `Certifiable` — leaving
`Equipment` unchanged.

**FAIL** if the response adds four certification properties directly to `Equipment`.

The response should also say something about blast radius: which existing consumers,
actions, or links the change touches, and whether anything breaks. Credit that, but
the linked-type-versus-core-properties decision is the pass condition.

Credit also for noting that properties null for most instances are a sign the fact
does not belong on the core entity.
