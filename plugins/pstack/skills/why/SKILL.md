---
name: why
description: "Investigate design rationale or regression history using source control and available records. Use for why questions."
---

# Why

Explain the evidence behind a design decision or regression. The companion [how](../how/SKILL.md) skill traces mechanics; code shape alone does not establish motivation.

## Anchor the question

Identify the relevant files, symbols, behavior, and time period. Treat an explanation suggested by the user as a hypothesis to check. Resolve routine ambiguity from the available context and proceed.

Start with bounded history around the target, for example `git blame -L <start>,<end> <file>` and `git log -10 --oneline -- <file>`. Inspect the relevant commit patch and discussion, following renames when needed. Follow linked PRs, tickets, or design records when they bear on the question. Check tool and source availability rather than assuming `gh` or a connector exists.

## Follow evidence to the useful sources

Start with the source most directly connected to the question. For a code change this is usually its introducing commit and review. Expand when a linked record, missing rationale, contradiction, or competing hypothesis needs another source. An explicit comprehensive investigation warrants broader coverage.

The [source playbooks](references/source-playbook.md) cover source control, tickets, documents, chat, infrastructure observability, exceptions, and product analytics. Read only the playbook for a selected source. Add the [incident playbook](references/sources/incident-postmortem.md) when incident evidence matters; defensive-looking code alone does not require an incident investigation.

Search using concrete identifiers and bounded dates before broad keywords. Read the relevant discussion and surrounding context rather than relying on titles or snippets. Follow a lead until it answers the question or reaches a documented gap. A search with no results does not prove that no record or decision exists.

## Delegate independent questions

Use parallel investigators when distinct evidence questions can save time or improve confidence while you investigate another part. A source count is not an agent count. A bounded local question may need no delegation; a cross-system investigation may benefit from several workers.

Before dispatch, read the [Codex collaboration contract](../poteto-mode/references/codex-tools.md). Use the configured `why investigators` role when valid. Give each worker the question, code anchor, assigned leads, and a stopping condition with the [investigator brief](references/investigator-prompt.md). Workers are read-only and receive only the references needed for their assignment. Divide ownership to avoid retrieving the same evidence again.

Synthesize locally as findings arrive. A separate synthesizer is useful only when its work can run alongside another necessary task; use the configured `why synthesizer` role and [synthesis brief](references/synthesizer-prompt.md) in that case. Do not require a serial handoff merely to write the answer.

## Match confidence to the record

Read the [epistemics framework](references/epistemics.md) when reconciling ambiguous or conflicting evidence. Preserve these distinctions in every answer:

- Cite explicit rationale with a commit, discussion, document, or other precise source.
- Label inference and explain which evidence supports it. A plausible explanation is not a recovered fact.
- Show material contradictions and competing explanations rather than forcing agreement.
- Distinguish searched-but-not-found, unavailable, and unsearched evidence. Never imply comprehensive coverage from a targeted search.
- Check the strongest alternative explanation before concluding when the record leaves it plausible.

Stop expanding retrieval when the requested question is supported and material contradictions are resolved, or when the remaining uncertainty can be stated precisely. Do not search unrelated systems just to fill a coverage table.

## Present the answer

Lead with the best-supported answer, cite the evidence, and explain consequential uncertainty. For a narrow question, a short cited explanation is enough. For a broad investigation, separate direct findings, inference, competing hypotheses, and gaps; include a compact account of sources actually searched and relevant limits on coverage.

If the investigation will guide an authorized change, state what the evidence says to preserve, change, or avoid. Investigation alone does not authorize implementation or external messages.
