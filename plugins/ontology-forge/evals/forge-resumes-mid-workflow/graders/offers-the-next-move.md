---
type: llm
---

"What do I do next" is the question this plugin was failing to answer. A correct response ends
with the user able to act without knowing a stage name.

**PASS** if the response offers a concrete next move — resuming stage 02 at its links phase, or
settling the "job" conflict first because it blocks whether `Job` is one type or two — and
either runs it or asks which to take.

**FAIL** if the response ends by listing the plugin's five stage commands and leaving the user
to pick. Naming the menu is not the same as answering the question.

**FAIL** if the response jumps straight to stage 03 or to mapping source data. Stage 02 is
unfinished and there are no links yet.

Credit for treating the blocked open question as the more valuable move than mechanically
resuming at phase 3, since it changes the type structure downstream.

Only one question may be asked. A response that fires several at once fails on the interview
rule regardless of how well it read the position.
