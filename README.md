# dot-plugins

Tooling for the [Agent Plugins Specification](spec.md) v1.1.0.

## Layout

```text
spec.md                              # the specification (v1.1.0, working draft)
skills/agent-plugin-builder/         # skill for authoring conformant plugins
├── SKILL.md
├── scripts/validate_plugin.py       # conformance validator
└── references/                      # mcp.json format, full rule index
tests/                               # pytest suite for the validator
```

## Setup

```bash
uv sync
```

To make the skill active in Claude Code, link it into your skills directory:

```bash
ln -s "$PWD/skills/agent-plugin-builder" ~/.claude/skills/agent-plugin-builder
```

The symlink keeps this repo the single source of truth — edits here take effect
immediately, with nothing to copy back.

## Validating a plugin

```bash
uv run python skills/agent-plugin-builder/scripts/validate_plugin.py <plugin-dir>
```

Exit code is 0 when conformant and 1 on any violation, so it drops into CI as-is.
`--json` emits machine-readable findings; `--quiet` prints errors only.

Findings cite the spec section they come from. Errors are conformance violations;
warnings are things a client tolerates but that usually indicate a mistake — a
skill directory with no `SKILL.md`, a bundled executable that isn't there yet, a
credential-shaped value in `env`.

`pyyaml` is a dev dependency because the validator parses `SKILL.md` frontmatter.
Without it the validator falls back to a built-in YAML subset parser; the test
suite asserts both paths agree.

## Tests

```bash
uv run pytest
uv run ruff check .
```
