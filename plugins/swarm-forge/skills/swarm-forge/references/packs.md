# SwarmForge packs

A pack is a roster. It supplies `swarmforge.conf` (which agents run, on which backend, in
which worktree) plus one `roles/<role>.prompt` per agent and the pack's own constitution
articles. The engine is shared; only the roster changes.

Conf line format:

```text
window-invisible <role> <agent> <worktree> [task|batch] [extra-cli-args...]
window           <role> <agent> <worktree> [task|batch] [extra-cli-args...]
```

`window-invisible` runs the agent in tmux with no Terminal window — the pack default,
because the cockpit is the operator surface. Exactly one role must use the worktree
`master`; that role runs in the main checkout and is the **master agent** that New Task and
the cockpit chat rail talk to. Every other role gets `.worktrees/<name>` on branch
`swarmforge-<name>`. `batch` means the role consumes all queued equal-priority handoffs as
one unit instead of one task at a time.

---

## `two-pack` — quick backend loop

```text
window-invisible coder   codex master        --yolo
window-invisible cleaner codex cleaner batch --yolo
```

- **coder** (master) — Implements requested behavior with TDD, owning the unit tests that
  define each slice and keeping IO behind small adapter boundaries.
- **cleaner** — Takes coder handoffs in batches and does one cleanup pass: coverage, CRAP
  (target ≤ 6), DRY, module boundaries, encapsulation, and mutation hardening. It absorbs
  the architect, hardener, and QA jobs that six-pack splits out.

Flow: coder → cleaner → coder. No specification or acceptance-test stage, and no approval
gate — with no specifier, handoffs deliver immediately.

## `four-pack` — compact specification workflow

```text
window-invisible specifier  codex master           --yolo
window-invisible coder      codex coder            --yolo
window-invisible refactorer codex refactorer       --yolo
window-invisible architect  codex architect batch  --yolo
```

- **specifier** (master) — Turns user intent into Gherkin acceptance specs, prunes
  redundant parameters with `ir-dry-checker`, then commits and queues the handoff to coder
  without asking in its pane.
- **coder** — Stands up the acceptance pipeline and implements approved slices with TDD
  units plus generated acceptance tests.
- **refactorer** — Structure-preserving cleanup, coverage, and property testing.
- **architect** — High-level design, module boundaries, dependency direction; sends the
  completion notice back to the specifier.

Flow: specifier → coder → refactorer → architect → specifier.

## `six-pack` — full workflow

```text
window-invisible specifier grok  master
window-invisible coder     codex coder             --yolo
window-invisible cleaner   codex cleaner   batch   --yolo
window-invisible architect grok  architect batch
window-invisible hardender codex hardender batch   --yolo
window-invisible QA        grok  QA        batch
```

Note the split backends: the three judging roles run on grok, the three writing roles on
codex. Grok's yolo equivalent is added by the launcher, which is why those lines carry no
`--yolo`.

- **specifier** (master) — Gherkin specs *and* end-to-end QA procedures.
- **coder** — Implements approved slices; keeps generated acceptance tests separate from
  unit tests.
- **cleaner** — Local clarity only: names, cohesion, local coupling, duplication, dead
  code. Explicitly leaves dependency direction to the architect.
- **architect** — Module partitioning, isolating high-level from near-IO code, making
  dependencies point low → high. Behavior-preserving.
- **hardender** — Mutation hardening; installs the mutation/CRAP/DRY and Gherkin tools and
  kills mutation survivors. *(The spelling is an upstream typo baked into the role name and
  its prompt filename. Do not "fix" it — the conf, the prompt file, and the worktree name
  must agree.)*
- **QA** — Final independent verification: converts QA procedures to executable scripts and
  runs spec, acceptance, unit, property, and architecture checks. Its multi-recipient
  end-of-chain handoff is what moves a card to **Done** on the board.

Flow: specifier → coder → cleaner → architect → hardender → QA → done.

## `adversaries` — legacy

```text
window coder    codex master
window reviewer codex reviewer
```

- **coder** (master) — TDD implementation, and also implements the reviewer's committed
  recommendations from `review/recommendations/NNN-recommendations.md`.
- **reviewer** — Adversarially reviews code, tests, commit history, and handoff state.
  Writes concrete recommendations; never edits production or test code.

Last updated upstream in June 2026, before the cockpit existed. It is the only pack still
using visible `window` lines and the only one without `--yolo`, and upstream's README does
not document it. Use `two-pack` unless the user asks for `adversaries` by name.

---

## Tooling

The `specifier`, `coder`, `refactorer`, `hardender`, `architect`, and `QA` roles require the
Acceptance Pipeline tools — `gherkin-parser`, `ir-dry-checker`, `gherkin-mutator`. Upstream
git-clones those from GitHub on first use. This plugin bundles them and the install
pre-seeds them into the project, so `swarm_tool.sh require <tool>` succeeds offline and
`swarm_tool.sh ensure <tool>` rebuilds from the bundled copy rather than the network.

The per-language quality tools named in the constitution — `crap4clj`, `dry4clj`,
`clj-mutate`, `mutate4go`, and the rest of that table — are *not* bundled. They depend on
the project's language and the agents install them on demand, exactly as upstream.

## Choosing between them

Size the pack to the work, not to ambition. Every extra role adds a handoff hop, and each
hop is a place where a task can stall waiting on a human gate. `two-pack` finishes small
work fastest; `six-pack` is for work where you genuinely want an independent agent owning
each quality gate.

Packs with a `specifier` add a human approval gate: the daemon holds the master agent's
first `git_handoff` in `pending_approval/` until someone clicks Approve in the cockpit.
`two-pack` and `adversaries` have no specifier, so their handoffs deliver immediately.
