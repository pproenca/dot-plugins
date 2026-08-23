# Local patches

The engine under `swarmforge/` is vendored verbatim from upstream
`unclebob/swarm-forge` so it can be re-vendored with a plain copy. These patches are the
only deliberate exceptions. **If you re-vendor, re-apply them** — `tests/test_swarm_forge_patches.py`
in the marketplace repo fails if they are missing, so CI will catch it.

Apply from the plugin root:

```bash
for p in patches/*.patch; do patch -p1 < "$p"; done
```

## 0001 — honor tmux `pane-base-index`, and make teardown resilient

Two defects in `swarmforge/scripts/pack_web.bb`, both present in upstream `main`.

### The cockpit typed into a pane that does not exist

`pane-target` hardcoded pane index `.0`:

```clojure
(str session ":" window ".0")
```

The launcher does not make this mistake — `swarmforge.bb` detects `pane-base-index` via
`tmux-option` and builds its target with `tmux-agent-target`. The dashboard disagreed with
it. On any host whose tmux sets `pane-base-index 1` (a very common `.tmux.conf` setting, and
one upstream's README explicitly claims to support), every cockpit action that types into an
agent — **New Task, the chat rail, clarification answers** — silently did nothing:
`tmux send-keys` failed with `can't find pane: 0`, `inject-role!` swallowed the exception in
a bare `catch`, and the HTTP API still returned `{"ok":true}`.

Reads were unaffected, which is why the board and thermometer still looked alive:
`capture-pane` already falls back to a session-scoped target. Only writes were dead.

The patch adds `pane-base-index`, which asks the running tmux server for the setting and
caches it per socket, and threads the socket into `pane-target`. It defaults to `0` — the
tmux default, and what the argv stub reports under test — so upstream's own test suite passes
unmodified. It also gives injection a session-scoped fallback when the pane target does not
resolve, and logs failures to `.swarmforge/dashboard.log` instead of discarding them.

### Teardown could stop halfway, silently

`run-teardown!` called its four steps in sequence with no isolation, and
`schedule-teardown!` wrapped the whole chain in `(catch Exception _)` before calling
`System/exit`. A failure in the first step (`close-swarm`) therefore skipped stopping the
handoff daemon and killing the tmux sessions, killed the dashboard anyway, and reported
nothing anywhere. Observed live: the cockpit's **Teardown** left both agents and `handoffd`
running while the dashboard disappeared.

The patch runs each step independently through `teardown-step!` and reports failures, so a
misbehaving step can no longer leave agents running.

## 0002 — persist the resolved host facts as a contract

`0001` fixed the two symptoms. This fixes what produced them.

The launcher is the only component that probes the host: `detect-tmux-base-indexes`
resolves `base-index` and `pane-base-index`, and `detect-terminal-backend` resolves which
terminal adapter to drive. It then keeps all three to itself. `.swarmforge/` already carries
the rest of the runtime state — `tmux-socket`, `roles.tsv`, `sessions.tsv`, `tmux-env` — but
not these, and `start-pack-web!` spawns the dashboard with no `:extra-env` at all.

So every other program re-derives them, and each re-derivation is an independent chance to
disagree with the process that actually created the panes:

- `pack_web.bb` needed the pane index, was not told, and assumed `0`.
- `swarm-cleanup.sh` needs the terminal backend, is not told, and assumes `terminal-app` —
  which can contradict what the launcher chose, and drives an adapter the swarm never used.

Both bugs in `0001` are instances of that one defect. Patching them individually leaves the
next one free to appear somewhere else.

This patch makes the resolution part of the state contract. The launcher writes
`.swarmforge/env.tsv`:

```text
tmux-pane-base-index	1
tmux-window-base-index	1
terminal-backend	terminal-app
script-dir	/path/to/swarmforge/scripts
```

written in `prepare-workspace!` beside `roles.tsv` and `sessions.tsv`, rewritten once
`:terminal-backend` is final, and synced into every worktree by `sync-worktree-scripts!`
alongside the state files already copied there. `pack_web.bb` and `swarm-cleanup.sh` read it
instead of guessing.

Both readers keep their old derivation as a fallback, so a project created before this
existed still works — the contract is an improvement in precision, not a new requirement.

Upstream would be the right home for this. It is a small change to a file the project
already owns, and it removes a whole class of "the dashboard and the launcher disagree about
the host" bugs rather than the two that happened to be found.
