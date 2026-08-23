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
