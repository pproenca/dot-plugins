# Pstack instruction comparison — 2026-09-05

The original has a manual Eval playbook, but no reusable implementation-quality suite. This run adds executable checks and a recorded comparison. It does **not** establish that the simplified Codex instructions preserve quality across pstack, or that restoring the longer instructions would fix the observed failures.

## Source and controls

The supplied original is `/Users/pedroproenca/Documents/Projects/cursor-plugins/pstack/`, repository commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`. Its Eval playbook already calls for organic prompts, blind candidates, and one anonymous comparative judge. We retain those ideas and its engineering standards: caller-first interfaces, domain ownership, root-cause fixes, and verification of the actual result.

The executable comparison uses two Codex-compatible versions from this marketplace repository:

| Arm | Revision | Instruction-tree SHA-256 |
|---|---|---|
| Earlier Codex control | `7f0b4a87c4b37b6592997e741c1ca9c7fcad8cef` | `66f645dcb799ef15bbe977f3c581fbeadfc07203869b31b9a0f186ed65eff78b` |
| Simplified Codex candidate | `c4aac7780228998d217bba34fee0f85ea397e501` | `f24fe59cfdf0067c6c2fbea758f23aaf6254685e1450c6cb14020885c20e33a0` |

Hashes use `run.py`'s sorted relative paths, lengths, and bytes over the prepared `guide/`. Each completed run retained its assigned instruction hash. This is a comparison against the earlier adapter, not a direct runtime comparison against Cursor. The [upstream audit](../docs/codex-adaptation.md) separately accounts for the source content and host adaptations.

## Method and corrections

Fresh GPT-6 Astra agents received identical task prompts and starting projects within each case, with medium or high reasoning selected explicitly. Each worked directly without delegation, external services, personal configuration, commits, or PRs. The guide was supplied explicitly. Hidden checks stayed outside their projects; agents could write ordinary tests. The budget was two repetitions per case, effort, and arm: 16 candidate runs.

A setup error initially produced two identical simplified snapshots because the checkout had advanced before the control archive was taken. Hash inspection caught this before a comparative conclusion. Those eight outputs are recorded as two repetitions of the simplified version. The actual control was then frozen from the explicit earlier commit and run separately. Runs were therefore not randomized or interleaved by version.

Automatic approval review blocked two control implementation patches, interpreting the temporary fixtures as unrelated to the user's comparison. The high-effort queue run made no implementation changes; the high-effort feed run added failing regressions but could not apply its fix. Both are excluded, leaving 14 completed runs. They are not quality failures.

Before grading, the frozen checks rejected both unfinished seeds and accepted independently authored implementations. The coordinator then ran acceptance checks, unchanged seed smoke checks against each candidate implementation, and each candidate's tests. All 14 completed candidates passed their own tests and the seed smoke checks.

The original acceptance suite has seven event-feed checks, including a 160-combination traversal matrix, and twelve queue checks. Two queue probes were added after blind review and reported separately: a valid 1,100-level nested payload, and `claim(1e308, 1e308)` with valid finite arguments. Independent implementations pass those probes too. No candidate received hidden failures and continued into a supposedly fresh pass.

Frozen case hashes before the review probes:

- Event feed: `00be7dc34d76e71e04082d6e8cc32c5b5715467188ad9d5b50d88bb1c4b7d87d`.
- Lease queue: `f64f2030fdc5e18e9eee9fbd0740ac6c557dc242047b81ca05ee6c04b2b53994`.

## Observed results

Counts are completed implementations passing every check in that column, not individual assertions. A dash means the extra probes do not apply.

| Task | Effort | Earlier: frozen checks | Simplified: frozen checks | Earlier: also passes review probes | Simplified: also passes review probes |
|---|---|---:|---:|---:|---:|
| Event feed | Medium | 2/2 | 2/2 | — | — |
| Event feed | High | 1/1 | 2/2 | — | — |
| Lease queue | Medium | 1/2 | 1/2 | 0/2 | 0/2 |
| Lease queue | High | 1/1 | 2/2 | 1/1 | 1/2 |

Both versions produced a medium-effort queue that ranked an expired lease by expiry instead of the job's due time. Other outputs rejected valid deep payloads or finite arguments whose sum overflowed. These are observable contract failures despite passing author-written tests. Shared failures and differences between repetitions of the same instructions prevent attributing them confidently to simplification.

Run-level accounting:

| Arm | Effort | Case | Run | Frozen checks | Added probes |
|---|---|---|---|---|---|
| Simplified | Medium | Queue | maple-dispatch | Fail: due ordering | Fail: depth, overflow |
| Simplified | Medium | Queue | cedar-dispatch | Pass | Fail: depth |
| Simplified | High | Queue | oak-dispatch | Pass | Fail: depth, overflow |
| Simplified | High | Queue | pine-dispatch | Pass | Pass |
| Earlier | Medium | Queue | fern-dispatch | Pass | Fail: depth |
| Earlier | Medium | Queue | hazel-dispatch | Fail: due ordering | Fail: overflow |
| Earlier | High | Queue | larch-dispatch | Pass | Pass |
| Earlier | High | Queue | spruce-dispatch | Excluded: approval block | — |
| Simplified | Medium | Feed | elm-feed, birch-feed | Both pass | — |
| Simplified | High | Feed | willow-feed, ash-feed | Both pass | — |
| Earlier | Medium | Feed | olive-feed, moss-feed | Both pass | — |
| Earlier | High | Feed | reed-feed | Pass | — |
| Earlier | High | Feed | clover-feed | Excluded: approval block | — |

## Blind artifact review

A fresh GPT-5.6 Sol reviewer at high reasoning assessed five anonymous pairs without instruction, model, or effort labels. Each output received the same 0–2 ratings for domain ownership, simplicity, verification, and completion, with correctness as a hard gate. The reviewer reran all ten submitted test suites and independently reproduced the ordering, depth, and overflow defects.

| Pair | Preference | Basis |
|---|---|---|
| fern-dispatch / maple-dispatch | Earlier | Preserves due ordering and accepts large finite time arguments; still fails deep payloads. |
| cedar-dispatch / hazel-dispatch | Simplified | Preserves due ordering and accepts large finite time arguments; still fails deep payloads. |
| oak-dispatch / larch-dispatch | Earlier | Explicit queued/leased states and stronger boundary coverage; no failure found in reviewed behavior. |
| olive-feed / elm-feed | Tie | Both implement the composite cursor boundary directly and verify useful behavior. |
| willow-feed / reed-feed | Tie | Both preserve the contract with small, direct implementations. |

An earlier anonymous review covered the simplified repetitions, including the passing `pine-dispatch` output. It demonstrates variation within that version, not an earlier-versus-simplified result. The coordinator checked the findings against code and execution. A proposed cross-instance token-uniqueness deduction was removed because the contract did not clearly require uniqueness across separate queues. Review must not silently expand the contract.

## Decision and next iteration

Do not certify the simplified instructions as quality-equivalent from this run. Keep the engineering principles and existing consequential review gates; do not add mandatory planning or broad testing to every task in response to these fixture failures. No further model or reasoning defaults are changed by this evaluation.

The new loop makes a narrower decision possible: reproduce a real regression, isolate the instruction or capability responsible, make a targeted change, and rerun affected pairs plus a fresh transfer task. Require correctness and design quality before promoting that change. This follows Eric Provencher's advice to reduce unnecessary instruction while revisiting assumptions as models change. [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/status/2095991462416490862).

Coverage remains small: two Python tasks, two reasoning levels, one candidate model, and no nested orchestration or automatic skill discovery. Caller-facing design alternatives, multi-file refactoring, adversarial review workflows, shipping, sustained programs, and low or higher reasoning levels remain unmeasured. Token, cost, timing, tool-count, and complete execution-trace telemetry were unavailable. A shorter entrypoint is a text-size result, not evidence of lower cost or equal quality.

The local run inventory, immutable output copies, prompts, behavioral results, and anonymous reviews are retained outside the plugin in `/tmp/pstack-quality-evidence/`. Temporary evidence may expire; the suite and this report remain in the repository.

## Harness validation

The repository suite passed with 232 tests and 22 skips. Four new regression tests exercise preparation isolation, refusal to overwrite work, content receipts, rejection of unfinished seeds, real subprocess results, and timeouts. Ruff and plugin conformance passed; all 45 skill entrypoints remain present. These checks validate the evaluation machinery and packaging, not the quality of future agent outputs.
