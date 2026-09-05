# Codex adaptation and upstream comparison

Reviewed on 2026-09-05 against the supplied Cursor checkout at commit `93b00b89ef425a9c1bac0d0b317dfc49c930ac99`, whose pstack manifest reports version `0.14.8`. The Codex package has its own version history. This comparison uses that local source snapshot, not an assertion about the latest upstream release.

## What survives

All 45 skills, 23 playbook files, supporting skill assets, both Cursor agent prompts, and 12 Benny automation files are accounted for. The agent prompts and Benny files remain under `com.cursor/` as source material. They are not active Codex configuration.

Pstack still uses caller-first design candidates, independent adversarial review, reproduction before a bug fix, measured performance comparisons, and verification on the actual artifact. Specialized Arena, Swarm, Shipping, and program workflows retain their evidence requirements. Existing implicit-invocation policies are unchanged; this revision narrows descriptions and routing without hiding additional skills.

## Drift corrected

The port had made Graphite mandatory for ordinary PR and stack workflows. The supplied original uses `gh` by default with optional Origin. The restored playbooks prepare and land only the bottom verified PR, compare the stable patch identity of each base-to-head diff, and recheck the next PR after each merge.

The bundled `orch frontier` implementation is Graphite-specific in the original too. Its runtime remains unchanged. Orchestrate now identifies that requirement and routes other stacks through the forge-neutral playbooks rather than claiming the helper supports them.

## Astra adjustments

Eric Provencher recommends concise discovery descriptions, conditional reference loading, less prescribed process, and completion boundaries that support the intended work. This revision applies those recommendations to the entrypoint and common workflows. [Rethinking skills and prompts for GPT-6 Astra](https://x.com/pvncher/status/2095991462416490862).

The previous entrypoint required loading the mode, full rulebook, and collaboration contract before planning. Those files contained 3,375 whitespace-separated words. The new entrypoint contains 573 words and loads references as needed, an 83% reduction in the mandatory initial reading. This is a text-size comparison, not a measured latency or quality improvement.

The full rulebook becomes an optional principles index. Function boundaries no longer automatically trigger design panels. Ordinary explanations and synthesis run locally; independent exploration remains available for useful parallel slices. Common tasks reuse existing checks instead of automatically adding harnesses, reviewers, or PR ceremony. Build the Lever and Prove It Works retain reproducibility while making new tooling proportional to the task.

The [Codex collaboration contract](../skills/poteto-mode/references/codex-tools.md) keeps model inheritance as the default and validates overrides against current host metadata. It describes available-slot limits, separate writer worktrees, bounded briefs, and task-versus-subagent behavior. It also distinguishes scheduled continuation from work in the current turn.

The collaboration contract now keeps agent workspaces and deliverables in durable project locations. Swarm and Arena previously suggested `/tmp` output paths, and worktree instructions left the destination unspecified. Workers now use the host or repository worktree convention, with a sibling `<repository-name>-worktrees/<task-slug>/` directory as the fallback. Project output directories hold reports and screenshots. Temporary tool caches and test scratch files remain allowed; moving an existing temporary worktree requires coordination with its active owner.

Observed runs also repeated skill reads, inherited full conversations for bounded assignments, polled unfinished reports, and expanded design candidates beyond the approved phase. Briefs now carry phase exclusions and use selective context. Candidates check scope early without a routine approval handoff, and runners no longer reload parent orchestration. Retrieval guidance bounds large results and checks file type before text reads. Reviewers retain independent responsibilities and verify fixes without repeating settled questions. Following Eric's guidance above, these are conditional decision rules rather than another mandatory itinerary. They address observed work patterns, not a measured percentage reduction in usage.

Official Astra guidance calls out sensitivity to skill instructions, possible approval pauses, limited spontaneous delegation, and excessive testing on small changes. Our effort table is a starting heuristic for workload tuning, not an OpenAI benchmark: lower effort for bounded mechanical work, more for unresolved judgment. A skill cannot change the active parent's settings. [Using GPT-6 Astra](https://developers.openai.com/api/docs/guides/latest-model#prompting-best-practices).

## Remaining capability boundaries

A persistent webhook bot requires host support that ordinary Codex task creation does not provide. `make-bot-ui` preserves that distinction and requires an accepted product change before building an independent-task substitute. Benny's Cursor automation pack remains dormant. Model diversity is reported only when distinct models actually run; different reasoning levels on one model are independent same-model work.

## Validation and maintenance

The full repository suite passed with 228 tests and 22 skips. Plugin conformance and all 45 skill validators passed. The latest published Codex CLI, `0.153.4`, loaded all 45 skills through the native marketplace loader. All 222 relative links in changed Markdown resolved, and Ruff passed. An independent agent used the revised mode to fix a typo in a temporary README and verified the text directly, without commits or PRs. This is a behavioral smoke check; it does not establish quality or cost across reasoning levels.

Use `scripts/check_pstack_cursor_parity.py <cursor-pstack-path>` from the marketplace repository to check file accounting and the reviewed translation receipts. Those receipts detect unreviewed drift; they do not prove semantic equivalence. Manifest receipts normalize release versions so an automatic version bump preserves the review; other manifest fields remain covered. Repository validators check version validity and synchronization. Review changed instructions before updating a receipt. Use the repository validators and native Codex loader for packaging checks, and representative tasks at the user's chosen model and effort before changing personal defaults.
