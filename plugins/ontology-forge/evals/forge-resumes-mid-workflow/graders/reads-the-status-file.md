---
type: regex
pattern: STATUS\.md
target: trace
match: contains
---

STATUS.md is the file that carries the position across sessions, and the fixture stages one.
A response that reconstructs the position by listing the directory has ignored the mechanism
under test even if it happens to guess the stage correctly.

Matched against the trace rather than a specific tool, so reading it with Read, Grep, or a
Bash cat all count.
