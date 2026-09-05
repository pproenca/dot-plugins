# Closing the improvement loop — 2026-09-05

Independent contract review followed by repair improved the four queue outputs from **2/4 to 4/4 passing** the frozen acceptance and boundary checks. A separate instruction addition showed no benefit and was discarded. A fresh inventory implementation then exercised the resulting review route and passed all 18 transfer checks.

The retained change restores review separation for consequential features with coupled state transitions or ordering rules. An existing lead/worker split can supply it; otherwise the playbook calls for one bounded reviewer. The reviewer compares public requirements with both implementation and test expectations, and substantiated defects are repaired before delivery. This preserves a useful mechanism from the original pstack without restoring its mandatory design panels, implementation delegation, and throughput worksheets for every feature.

## First intervention: rejected

The earlier study found tests that explicitly expected incorrect behavior. The first hypothesis was that deriving expectations before implementation would reduce this shared mistake. We froze the current plugin at marketplace commit `28c1e3a` and a copy with one conditional paragraph added to Feature: derive examples from the contract before implementation, distinguish plausible interpretations, and avoid tests that legitimize unsupported restrictions.

The controlled run used eight fresh GPT-6 Astra agents at medium reasoning: two cases, two instruction variants, two repetitions. Task prompts, tools, starting projects, and the no-delegation constraint matched within each case. Dispatch order alternated by variant. Instruction hashes differed; case hashes matched. Inventory reservations were authored independently before these runs as a transfer task, with no access to the queue outcomes or proposed instruction.

| Case | Current instructions | Added paragraph |
|---|---:|---:|
| Queue: original 12 acceptance checks | 2/2 | 2/2 |
| Queue: also passes both previously frozen boundary probes | 1/2 | 1/2 |
| Inventory: 18 acceptance checks | 2/2 | 2/2 |

All eight outputs passed their submitted tests. The paragraph produced no observed improvement and did not meet the predeclared promotion rule. It was not added to the plugin.

Prepared instruction-tree SHA-256 receipts, using `run.py`'s hashing algorithm:

- Current: `ff0026a4c1b0e91cf37d84e0daf2480f8bf4765bc7aab6f69e540210500e51d4`.
- Added paragraph: `b411158d2ba01e878de7a3dfde5331794c89c775953d4301f927f0c0a40128ba`.

## Second intervention: review and repair

A fresh GPT-5.6 Sol reviewer at high reasoning received all four queue outputs under anonymous labels, their public READMEs, and their submitted tests. It received no instruction labels, hidden checks, or hints about the failures. It independently reproduced failures on deep valid payloads in two outputs and rejection of valid finite time arguments in one. It also found a float-rounding ambiguity; neither interpretation was penalized because the contract did not settle it.

Only the substantiated public-contract findings went back to the original implementers. They reproduced and fixed the problems, replaced an incorrect rejection test with positive lifecycle coverage, and added relevant payload checks. The original outputs and scores remain frozen. These continuations are repair stages of the same work, not new independent candidate passes.

| Queue output | Instruction variant | Before review | After review and repair |
|---|---|---|---|
| juniper-dispatch | Current | Pass | Pass; unchanged |
| aspen-dispatch | Current | Fail: depth, expiry overflow | Pass |
| rowan-dispatch | Added paragraph | Fail: depth | Pass |
| acacia-dispatch | Added paragraph | Pass | Pass; unchanged |

The coordinator reran the original 12 acceptance checks, both already-frozen boundary probes, and the repaired test suites. The independent reviewer inspected both diffs and reran its own reproductions. Both repairs passed with no new restriction or lifecycle regression found. The repaired submitted suites contain 15 and 12 test methods respectively.

This establishes a concrete benefit on these artifacts: independent review found and repair removed defects that implementation-time testing had missed. It does not estimate the success rate or optimal review frequency across all tasks; the review stage adds work. That is why the retained route is limited to consequential stateful features and reuses review separation when it already exists.

## Fresh check of the retained workflow

We froze a third variant with the targeted review route in Feature and ran one fresh Astra-medium inventory task, `saffron-stock`, with at most one helper allowed. This was a separately declared workflow check after the eight-run comparison.

The worker read the Feature playbook, recognized the coupled transitions, and explicitly requested an independent review from its lead before final delivery. The lead read the complete implementation and test expectations against the public contract, checked atomic multi-item reservations, terminal replay, expiry accounting, and snapshot ownership, and found no actionable discrepancy. The worker reused the existing lead/worker split, so an additional reviewer agent was unnecessary.

The finished implementation passed all 18 coordinator-owned transfer checks and all 14 submitted tests. The guide hash remained unchanged:

`d0762f21e788b97414c3ae8813cc52bd747b393e5e7319897487d057eabac975`

This checks the actual coordination route as well as the resulting artifact. It does not require every feature to spawn a new panel or prescribe a particular reviewer model.

## Retained changes and evidence

- Feature restores targeted independent contract review and requires substantiated findings to be resolved and checked.
- Eval makes a change-and-retest decision the deliverable for improvement requests. It distinguishes initial outputs, review-assisted repairs, and fresh runs.
- The suite gains the inventory transfer case. Its unfinished seed is rejected, its two smoke checks pass, and an independently authored implementation passes all 18 acceptance checks.
- The additional contract-first paragraph is rejected; model and reasoning defaults are unchanged.

The [original comparison](2026-09-05-comparison.md) remains intact. Frozen inputs, protocols, initial outputs, repair outputs, anonymous reviews, and execution results are stored outside the plugin at `/tmp/pstack-outcome-iteration/`; fixture calibration is at `/tmp/pstack-inventory-authoring/`. These temporary artifacts may expire. This report and the reusable behavioral checks remain in the repository.

The result applies Eric Provencher's guidance by retaining a mechanism that improved the observed work and rejecting instruction that did not. [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/status/2095991462416490862).
