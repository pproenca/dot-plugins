# Synthesis brief

Use this only when a separate synthesis task can run alongside other necessary work. Otherwise synthesize in the lead's existing context.

```text
Answer the historical question from the supplied evidence, read-only:
{QUESTION_AND_CODE_ANCHOR}

Findings and citations:
{FINDINGS}

Relevant sources searched, unavailable, or left unsearched:
{COVERAGE}

Apply the supplied epistemics framework. Lead with the strongest supported answer.
Cite explicit rationale, distinguish inference, and show material contradictions.
Verify questionable citations using bounded retrieval. Do not turn a null search
into proof that no record exists, or code mechanics into evidence of intent.

Use a short explanation for a narrow question. A broad investigation may need
separate findings, hypotheses, and gaps. Describe actual coverage without implying
that every possible source was searched. Never invent missing evidence to finish
the story. Do not edit files or contact people.
```

Supply the relevant guidance from [epistemics.md](epistemics.md) with the brief. Preserve its confidence distinctions when editing the final answer.
