# Repository Guidelines

## Project Structure & Module Organization

This repository is a marketplace of self-contained Agent Plugins. Each package lives in `plugins/<name>/` and contains a portable `plugin.json`, a Codex discovery manifest at `.codex-plugin/plugin.json`, and one or more `skills/<skill>/SKILL.md` files. Optional commands, MCP configuration, references, assets, and evals stay inside the owning plugin; installed plugins must not depend on paths outside their directory.

Client catalogs live in `.agents/plugins/marketplace.json` (Codex) and `.claude-plugin/marketplace.json` (Claude Code). Keep both synchronized with every directory under `plugins/`. The portable specification is `spec.md`; repository-level conformance and catalog tests are in `tests/`. Treat `plugins/*/vendor/` as vendored upstream code and make intentional downstream changes through the plugin's established patch mechanism.

## Build, Test, and Development Commands

- `uv sync`: create or refresh the Python 3.12 development environment from `uv.lock`.
- `uv run pytest`: run manifest, containment, marketplace, CLI, MCP, and plugin integration tests.
- `uv run ruff check .`: check Python correctness, imports, and style.
- `uv run python scripts/test_codex_plugins.py [plugin]`: load one plugin or the whole marketplace through the latest published Codex CLI.
- `uv run python scripts/test_codex_plugins.py --codex-repo ../codex [plugin]`: build a Codex checkout and test its native marketplace loader.
- `uv run python plugins/agent-plugin-builder/skills/agent-plugin-builder/scripts/validate_plugin.py plugins/<name>`: validate one plugin against Agent Plugins v1.1.0. Add `--json` for machine-readable output.
- `cd plugins/swarm-forge && bb test`: run SwarmForge helper tests.
- `cd plugins/swarm-forge-squad && bb test`: run squad tests; use `bb simulation-test` for the slower simulator suite.

## Coding Style & Naming Conventions

Use four spaces for Python and keep lines within Ruff's 120-character limit. Ruff enforces `E`, `F`, `I`, `B`, and `W` rules. Follow existing JSON formatting (two-space indentation) and keep Markdown direct and task-oriented. Plugin and skill directories use lowercase kebab-case; Python tests and functions use `test_<behavior>` snake_case. Keep manifest metadata aligned across portable, Codex, and marketplace files.

## Testing Guidelines

Pytest is the primary test framework; place repository tests in `tests/test_<area>.py`. Add focused regression tests for validator or catalog behavior and plugin-local tests for runtime changes. There is no numeric coverage threshold, but every new plugin must validate cleanly, appear in both catalogs, and pass the full pytest suite. Do not leave caches or generated artifacts inside plugin directories.

Do not add implementation-detail configuration tests that parse repository config files or assert literal source, workflow, key, or value strings. These snapshot/string-presence tests duplicate the implementation and fail on harmless refactors without proving behavior. Validate configuration with its native linter or CLI, and test release or workflow behavior through dry runs and integration tests instead.

## Commit & Pull Request Guidelines

Recent commits use short, imperative subjects such as `Add Codex marketplace support alongside Claude Code`. Keep each commit focused and explain licensing or vendored-code decisions in the body when relevant. Pull requests should summarize behavior, identify affected plugins, report the commands run, link related issues, and include screenshots when changing marketplace cards or icons.
