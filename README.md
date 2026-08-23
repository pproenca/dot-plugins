# dot-plugins

A plugin marketplace. Every plugin here is packaged to the
[Agent Plugins Specification](spec.md) v1.1.0 — a root `plugin.json` plus
`skills/` and `mcp.json` — so it loads in any conformant client.

## Install

```bash
/plugin marketplace add <owner>/dot-plugins
/plugin install pstack@dot-plugins
/plugin install agent-plugin-builder@dot-plugins
```

Or point at a local clone: `/plugin marketplace add ./dot-plugins`.

## Plugins

| Plugin | What it does |
| ------ | ------------ |
| [`agent-plugin-builder`](plugins/agent-plugin-builder) | Scaffolds and validates plugins against Agent Plugins v1.1.0. Ships the conformance validator this repo runs in CI. |
| [`pstack`](plugins/pstack) | Rigorous agent workflows — playbooks, engineering principles, and subagent orchestration. By [Lauren Tan](https://github.com/cursor/plugins/tree/main/pstack), MIT, vendored here. |

## Layout

```text
.claude-plugin/marketplace.json   # the catalog: one entry per plugin
plugins/<name>/                   # one self-contained plugin per directory
├── plugin.json                   # Agent Plugins v1.1.0 manifest (required, at the root)
├── skills/<name>/SKILL.md        # portable component
└── mcp.json                      # portable component
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

`pstack` currently passes with warnings: its `agents/` directory and its
Cursor-specific frontmatter keys (`disable-model-invocation`, `icon`, `color`,
`mode`, `reminder`) are not v1 component types or Agent Skills fields, so
conformant clients ignore them. The skills themselves load everywhere.

## Tests

```bash
uv run pytest
uv run ruff check .
```

`pyyaml` is a dev dependency because the validator parses `SKILL.md`
frontmatter. Without it the validator falls back to a built-in YAML subset
parser; the test suite asserts both paths agree.
