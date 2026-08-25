---
type: llm
---

`one-question-only` counts question marks mechanically. This grader covers only the part that
genuinely needs judgement: a question that is two questions wearing one question mark.

**PASS** if the response asks exactly one question and it asks for one thing. Count questions by
meaning, not by punctuation — a question phrased without a question mark still counts, and this
suite has produced exactly that.

**FAIL** on a compound question joined by "and" or "or" — *"What does it recommend, and who
receives it?"* is two questions and one mark. The user answers whichever half they noticed and
the other becomes a silent assumption, which is the exact failure the one-question rule exists
to prevent.

**FAIL** if the question is not substantive domain elicitation — asking which stage to run, or
whether to proceed, is a menu rather than an interview.

Framing, context, or a single worked example alongside the question is fine and should not be
read as extra questions.
