---
name: extend-prefers-linked
tags: [extend]
allowed_tools: [Read, Grep, Glob, Write, Edit, Skill]
max_turns: 20
---

Our `Equipment` object type is in production and several applications read it.
The compliance team now needs to track certification for equipment: which authority
issued it, when it expires, its current status, and when it was last audited. Only
about a fifth of our equipment is certified at all.

Add this to the ontology.
