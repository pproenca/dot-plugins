---
name: agent-plugin-builder
description: Build plugins that conform to the Agent Plugins Specification v1.0.0 — a plugin.json manifest plus skills/ and mcp.json components — and verify them with a bundled conformance validator. Use this skill whenever the user wants to create, scaffold, package, or fix an agent plugin; mentions plugin.json, mcp.json, PLUGIN_ROOT, PLUGIN_DATA, or the Agent Plugins spec; or asks to turn existing skills or MCP servers into something distributable, even if they never say "Agent Plugins" by name.
license: MIT
compatibility: Requires Python 3.8+ to run the bundled validator.
---

# Agent Plugin Builder

Agent Plugins v1.0.0 packages reusable agent components — Agent Skills and MCP servers — into a directory that any conformant client can load. This skill builds those packages and proves they conform.

The format is deliberately small and strict. Two things follow from that, and they shape everything below:

- **The schemas are closed.** Only the listed fields exist. A client that sees an unlisted field treats the manifest as non-conforming. That strictness is the point: it makes typos detectable and enables schema-driven completion, instead of silently ignoring a misspelled `descrption`. So never invent a field to carry extra information — put it under `extensions` (§8).
- **Component locations are fixed.** `skills/` and `mcp.json`, both at the plugin root. The manifest cannot relocate them or hold inline component config. There is no discovery indirection to configure, which is why a plugin is readable with `ls` and `cat`.

**v1 defines exactly two component types: skills and MCP servers.** Commands, hooks, agents, rules, and LSP servers are *not* portable components. If the user wants those, they belong in a client extension directory (see [Client extensions](#client-extensions)) — not invented as new top-level directories.

## Workflow

### 1. Establish what the plugin actually contains

Before writing files, settle:

- **Plugin name** — lowercase `a-z0-9-.`, and this is a *display/package* name, not a directory constraint.
- **Which components** — skills, MCP servers, or both. A plugin with neither is valid but useless; say so and confirm it's intentional.
- **For each MCP server** — transport (`stdio` / `streamable-http` / `sse`), and for stdio whether the executable ships in the package or is expected on the user's PATH. This decision changes the `command` value and is awkward to reverse later, so ask now.
- **Any client-specific material** — hooks, slash commands, subagent definitions. These need a reverse-domain home.

If the user is converting an existing client-specific plugin, inventory what they have first and map each piece to either a portable component or an extension directory.

### 2. Create the layout

```text
my-plugin/
├── plugin.json          # required, at root
├── skills/              # optional; immediate children hold SKILL.md
│   └── summarize/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
├── mcp.json             # optional, at root
├── com.example.client/  # optional client extension directory
├── LICENSE
└── CHANGELOG.md
```

Omit what you don't need. A missing `skills/` or `mcp.json` is not an error (§6.2) — but a `skills` that exists as a *file*, or an `mcp.json` that exists as a *directory*, invalidates that whole component type. Create them with the right filesystem kind or not at all.

### 3. Write `plugin.json`

Minimal:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "my-plugin"
}
```

`$schema` and `name` are the only required fields, and `$schema` must be exactly that string — clients select their validation rules from it and are forbidden from fetching it over the network, so it functions as a version tag, not a URL to resolve.

Optional metadata, all of it: `version`, `description`, `author` (object with only `name`/`email`/`url`), `homepage`, `repository`, `license`, `keywords` (array of strings), `extensions`. Nothing else. Prefer including `version` (SemVer) and `description` — clients use `version` for update checks and cache freshness.

**Name constraints** (§5.5) — 1–64 chars, only `a-z 0-9 - .`, first and last character alphanumeric, no `--` and no `..`. Valid: `my-plugin`, `acme.tools`, `a`. Invalid: `My-Plugin`, `-start`, `has--double`.

### 4. Write the components

**Skills** go in `skills/<name>/SKILL.md`. Discovery is exactly one level deep — a `SKILL.md` at `skills/a/b/SKILL.md` is never found, and clients are forbidden from searching deeper. Each skill must conform to the Agent Skills specification, and the two most common mistakes are:

- `name` in the frontmatter must equal the directory name.
- **Skill names allow no periods.** Plugin names do (`acme.tools`), skill names don't (`a-z 0-9 -` only). Reusing a dotted plugin name as a skill name is a silent conformance failure.

If the skill's own content needs real design work — instructions, test cases, iteration — use the `skill-creator` skill for that and come back here to package the result.

**MCP servers** go in `mcp.json` at the root. Read `references/mcp-servers.md` before writing one: the server variants are a closed union with several rules that have no analogue in other MCP config formats (`command` is a single token with no placeholder expansion; `cwd` accepts only three shapes; `env` may not define `PLUGIN_ROOT`/`PLUGIN_DATA`).

The one rule worth stating up front, because it silently disables the whole file: `mcp.json`'s `$schema` version **must match** the version in `plugin.json`. Mixed versions make the MCP config invalid (§10.1).

### 5. Validate

```bash
python3 <skill-dir>/scripts/validate_plugin.py path/to/my-plugin
```

`<skill-dir>` is this skill's own directory, given to you when the skill loads. The script needs only Python 3.8+ — PyYAML is used if installed and a built-in parser covers frontmatter otherwise.

Run this on every plugin you produce, and again after any edit. It checks the manifest schema, name constraints, skill discovery and frontmatter, the `mcp.json` closed union, path containment, and placeholder usage — the mechanical rules that are tedious to verify by eye and easy to get subtly wrong.

Errors are conformance violations; fix all of them. Warnings are things a client tolerates but that usually indicate a real mistake (a skill directory with no `SKILL.md`, a bundled executable that doesn't exist yet, a credential-shaped value in `env`) — read each one and either fix it or explain to the user why it's intentional. `--json` emits machine-readable findings; `--quiet` suppresses warnings.

Report the result honestly. If something can't be fixed — a `command` that genuinely needs a shell pipeline, say — tell the user what's non-conformant and why, rather than quietly shipping it.

## Rules authors get wrong

These are the failures worth internalizing; the validator catches them, but knowing them avoids the round trip.

**Nothing outside the plugin root.** Every path the package supplies must resolve inside the plugin root after symlinks are followed (§4.1). Plugin-relative paths in config must begin with `./` — `data` and `../bin/tool` are both invalid, the first because it isn't marked plugin-relative and the second because it escapes.

**Secrets are never package data.** `env` values and HTTP `headers` ship inside the plugin, visible to anyone who reads it. The spec forbids embedding credentials there and defines no portable credential mechanism — authorization is client-managed. If a server needs a token, the plugin's job is to document that, not to carry it.

**Don't depend on the ambient environment.** Clients may inherit, omit, or sanitize environment variables, and whether a configured `PATH` affects bare-command lookup is explicitly client-defined. A conformant plugin relies only on `PLUGIN_ROOT`, `PLUGIN_DATA`, and what its own `env` block supplies. If you bundle an executable, reference it with a `./` path — a bare name is a bet on the user's PATH.

**`PLUGIN_ROOT` is read-only in spirit; `PLUGIN_DATA` is where state lives.** The client replaces package contents on update but preserves `PLUGIN_DATA`. So: bundled scripts, binaries, and config → `${PLUGIN_ROOT}`. Installed dependencies, virtualenvs, generated code, caches → `${PLUGIN_DATA}`. Writing state into the package is how a plugin loses it on the next update.

**Failures are isolated, not fatal — design for that.** One bad MCP server entry is skipped while the rest of the plugin loads; a malformed skill is skipped while sibling skills load. Only an invalid `plugin.json` takes the whole plugin down. Practical consequence: keep the manifest boringly correct, and don't build a plugin whose skills silently assume its MCP server connected.

## Client extensions

Anything client-specific — hooks, slash commands, subagents, settings — lives under a **reverse-domain namespace** the client owns, in one or both of:

- `plugin.json` → `extensions` → `"com.example.client": { ... }` (the value must be an object)
- a top-level directory named exactly `com.example.client/`

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
  "name": "example-plugin",
  "extensions": {
    "com.example.client": { "setting": true }
  }
}
```

Reverse-domain keys avoid collisions without a central registry, and clients ignore namespaces they don't implement without validating their contents — so an extension for one client is inert, not broken, everywhere else. The spec assigns *no* portable meaning to what's inside; the owning client defines it entirely. Don't guess at another client's schema — look it up or ask.

## References

- `references/mcp-servers.md` — the full `mcp.json` format: transport variants, `command` and `cwd` rules, placeholder expansion, URL and header requirements. Read before writing any MCP config.
- `references/spec-reference.md` — complete author-facing rule index with spec section citations, plus the client-behavior rules that constrain authoring choices. Consult when you need the exact normative wording or are resolving an edge case.
