# dot-plugins

A plugin marketplace. Every plugin here is packaged to the
[Agent Plugins Specification](spec.md) v1.1.0 — a root `plugin.json` plus
`skills/` and `mcp.json` — so it loads in any conformant client.

## Install

```bash
/plugin marketplace add <owner>/dot-plugins
/plugin install pstack@dot-plugins
/plugin install agent-plugin-builder@dot-plugins
/plugin install swarm-forge@dot-plugins
/plugin install swarm-forge-squad@dot-plugins
```

Or point at a local clone: `/plugin marketplace add ./dot-plugins`.

## Plugins

| Plugin | What it does |
| ------ | ------------ |
| [`agent-plugin-builder`](plugins/agent-plugin-builder) | Scaffolds and validates plugins against Agent Plugins v1.1.0. Ships the conformance validator this repo runs in CI. |
| [`pstack`](plugins/pstack) | Rigorous agent workflows — playbooks, engineering principles, and subagent orchestration. By [Lauren Tan](https://github.com/cursor/plugins/tree/main/pstack), MIT, vendored here. |
| [`swarm-forge`](plugins/swarm-forge) | Runs a pack of specialist agents on one repo — a git worktree and tmux session each, file-based handoffs, and a local web cockpit. By [Robert C. Martin](https://github.com/unclebob/swarm-forge), vendored here; no license stated upstream. |
| [`swarm-forge-squad`](plugins/swarm-forge-squad) | The SwarmForge squad workflow: a persistent squad leader that spawns short-lived workers on demand, each bound by a capability contract. Same upstream, same license caveat. |

## Layout

```text
.claude-plugin/marketplace.json   # the catalog: one entry per plugin
plugins/<name>/                   # one self-contained plugin per directory
├── plugin.json                   # Agent Plugins v1.1.0 manifest (required, at the root)
├── skills/<name>/SKILL.md        # portable component
└── mcp.json                      # portable component
                                  # anything else a plugin ships (docs, engines,
                                  # test suites) stays at its own root
spec.md                           # the specification (v1.1.0, working draft)
tests/                            # validator suite + marketplace/catalog checks
```

Agent Plugins v1.1.0 specifies the *package* and deliberately leaves
distribution to each client, so it defines no marketplace format. The catalog
is therefore a client artifact — `.claude-plugin/marketplace.json`, read by
Claude Code — while the plugin directories underneath it stay portable.

Each plugin is self-contained: a client copies the directory on install, so
nothing inside may reference a path outside its own root (§4.1). Shared tooling
lives *inside* the plugin that owns it, not at the repo root.

## Adding a plugin

1. Create `plugins/<name>/` with a root `plugin.json`.
2. Validate it (see below) until it passes.
3. Add an entry to `.claude-plugin/marketplace.json` with `"source": "./plugins/<name>"`.
4. Run `uv run pytest` — the suite fails on an unlisted directory or a catalog
   entry whose `name`, `version`, or `description` drifts from the manifest.

## Validating

```bash
uv sync
uv run python plugins/agent-plugin-builder/skills/agent-plugin-builder/scripts/validate_plugin.py plugins/<name>
```

Exit code is 0 when conformant and 1 on any violation, so it drops into CI as-is.
`--json` emits machine-readable findings; `--quiet` prints errors only.

Findings cite the spec section they come from. Errors are conformance
violations; warnings are things a client tolerates but that usually indicate a
mistake — a skill directory with no `SKILL.md`, a bundled executable that isn't
there yet, a credential-shaped value in `env`.

All four plugins validate clean. Two needed work to get there.

`pstack`: its Cursor subagents, automation pack, and Cursor manifest moved into
the `com.cursor/` extension directory (§8), and its Cursor-specific frontmatter keys
(`disable-model-invocation`, `icon`, `color`, `mode`, `reminder`) moved under
`metadata` as strings, since §7.1 closes the Agent Skills field set. Both are
preserved rather than portable: a client that does not implement `com.cursor`
ignores that directory, and clients read `metadata` but do not act on it.

`swarm-forge`: upstream splits the product across git branches — `main` carries
the engine and the dashboard, while `two-pack`, `four-pack`, `six-pack`, and
`adversaries` each carry only a roster of role prompts, and `squad` is a forked
engine entirely. Choosing a workflow upstream means extracting a different
branch tarball, and the launcher then downloads the engine from GitHub on first
run. A package cannot be five branches, so the rosters were vendored as data
under `packs/`; `squad` became its own plugin because it shares no code with the
others. The upstream tree is otherwise kept verbatim at the plugin root, which is
what keeps its web dashboard and its Babashka test suite working unmodified.

Installing `swarm-forge` runs a host check (`doctor.sh`) that exercises the
real machinery — including whether the cockpit can type into a tmux pane under
this host's own config — so a host-specific breakage fails at install rather
than silently mid-swarm.

`swarm-forge` also carries two small patches to the vendored engine, recorded
as diffs in `plugins/swarm-forge/patches/` and guarded by tests: upstream's
dashboard hardcoded tmux pane index `.0`, so on any host with
`pane-base-index 1` every cockpit action that types into an agent silently did
nothing, and its teardown could stop halfway without reporting why. Everything
else under `swarmforge/` is byte-identical to upstream.

Both swarm-forge plugins also vendor the Acceptance Pipeline Specification, the
one thing the engine itself git-clones at runtime, and their install scripts
seed it into the project. So installing and running a swarm needs no network,
and — because the engine is copied into the project exactly as upstream's
bootstrap does — the installed project holds no path back into the plugin and
survives the plugin being upgraded or removed. The per-language quality tools
the constitution names are still installed on demand by the agents, as upstream.

Neither swarm-forge plugin declares a `license`: neither upstream repository —
swarm-forge nor the Acceptance Pipeline Specification — ships a LICENSE file or
a license header, and the field is optional. That is a gap worth raising with
the author rather than guessing at terms.

## Tests

```bash
uv run pytest
uv run ruff check .
```

`pyyaml` is a dev dependency because the validator parses `SKILL.md`
frontmatter. Without it the validator falls back to a built-in YAML subset
parser; the test suite asserts both paths agree.
