# Agent Plugins v1.0.0 — author-facing rule index

Every rule a plugin author must satisfy, with spec section citations, plus the client-behavior rules that constrain authoring choices. The specification itself is authoritative; this is a navigation aid.

## Contents

- [1. Package model and path containment](#1-package-model-and-path-containment)
- [2. Manifest: `plugin.json`](#2-manifest-pluginjson)
- [3. Component discovery](#3-component-discovery)
- [4. Skills](#4-skills)
- [5. MCP servers](#5-mcp-servers)
- [6. Client extensions](#6-client-extensions)
- [7. Environment and placeholders](#7-environment-and-placeholders)
- [8. Versioning](#8-versioning)
- [9. Client behavior that constrains authors](#9-client-behavior-that-constrains-authors)
- [10. Canonical identifiers](#10-canonical-identifiers)

## 1. Package model and path containment

| Rule | § |
| ---- | -- |
| A plugin is a directory rooted at one filesystem location. | 4.1 |
| A manifest MUST exist at `plugin.json` in the plugin root. | 4.1, 5.1 |
| Every package file/directory a client reads MUST resolve within the resolved plugin root. Symlinks may point to targets inside the root; anything resolving outside is rejected. | 4.1 |
| A field defined as a plugin-relative path MUST begin with `./`, resolve against the plugin root, and stay inside it after resolution. | 4.1 |
| Values not defined as paths — command arguments, environment values — are opaque strings and are not treated as package paths. | 4.1 |

Failure boundaries are deliberately narrow (§4.1): a bad `plugin.json` rejects the plugin; a bad fixed component location invalidates that component *type*; a bad `SKILL.md` skips that *skill*; a bad `command`/`cwd` invalidates that *server entry*.

Containment governs package-supplied files only. It does not sandbox a launched subprocess or restrict paths supplied at runtime.

## 2. Manifest: `plugin.json`

Closed schema. The **only** permitted top-level fields:

`$schema`, `name`, `version`, `description`, `author`, `homepage`, `repository`, `license`, `keywords`, `extensions` (§5.2).

### Required (§5.3)

| Field | Type | Requirement |
| ----- | ---- | ----------- |
| `$schema` | string | Exactly `https://agent-plugins.org/schemas/1.0.0/plugin.schema.json` for v1.0.0. |
| `name` | string | Satisfies §5.5 name constraints. |

Missing, wrong-typed, empty, or otherwise invalid required field ⇒ the manifest is invalid, the client rejects the plugin, and **no** component is discovered or executed.

### Metadata (§5.4)

| Field | Type |
| ----- | ---- |
| `version` | string (SemVer RECOMMENDED) |
| `description` | string |
| `author` | object, only `name` / `email` / `url`, each a string |
| `homepage` | string |
| `repository` | string |
| `license` | string (SPDX RECOMMENDED) |
| `keywords` | string[] |

Any other member of `author`, or a non-string value in it, makes the manifest invalid. Otherwise metadata is validated by JSON type only — a client MUST NOT reject a manifest merely because `version` isn't SemVer, a URL field isn't a recognizable URL, `author.email` isn't a recognizable address, or `license` isn't an SPDX identifier.

### Name constraints (§5.5)

| Constraint | Requirement |
| ---------- | ----------- |
| Length | 1–64 characters inclusive |
| Character set | `a-z`, `0-9`, `-`, `.` |
| Start and end | Alphanumeric |
| Repetition | No `--`, no `..` |

Valid: `my-plugin`, `acme.tools`, `lint3r`, `a`. Invalid: `My-Plugin`, `-start`, `has--double`, `too.many..dots`, empty.

### Non-fatal exceptions

Two violations are non-fatal — the client reports and ignores them, then keeps loading (§5.2, §8.1, §11.3):

- an unknown top-level field (it is still a schema violation; a conforming plugin has none),
- an `extensions` value that is not an object.

Every other schema violation is fatal to the plugin.

### `$schema` handling

Clients select validation rules from a recognized `$schema` value, MAY map several canonical identifiers to one implementation only where they explicitly recognize the versions as compatible, and **MUST NOT retrieve the schema over the network while loading** (§5.2). An unsupported declared version means the plugin is rejected.

## 3. Component discovery

| Component type | Fixed location | Pattern |
| -------------- | -------------- | ------- |
| Skills | `skills/` | Immediate subdirectories containing `SKILL.md` |
| MCP servers | `mcp.json` | JSON configuration |

`plugin.json` cannot override these locations or carry inline component configuration (§6.1).

Absent location ⇒ not an error (§6.2). Present but wrong filesystem kind — `skills` not a directory, `mcp.json` not a regular file — ⇒ that component type is invalid; other types still load (§6.2).

v1 defines exactly two component types (§7). Commands, hooks, agents, rules, and LSP servers are outside the v1 format; clients ignore component types they don't support.

## 4. Skills

Discovery (§7.1): each immediate child directory of `skills/` that contains a path named exactly `SKILL.md` resolving to a regular file is one skill. Clients **MUST NOT** search deeper descendants.

The skill format itself is governed by the [Agent Skills specification](https://agentskills.io/specification), which is the source of truth for `SKILL.md`, frontmatter, and the `scripts/` / `references/` / `assets/` layout. A non-conforming skill is skipped; siblings and other component types still load.

### Agent Skills frontmatter

| Field | Required | Constraint |
| ----- | -------- | ---------- |
| `name` | Yes | 1–64 chars; lowercase `a-z`, `0-9`, `-` only; no leading/trailing hyphen; no `--`; **must match the parent directory name**. |
| `description` | Yes | 1–1024 chars, non-empty; says what it does *and* when to use it. |
| `license` | No | License name or bundled file reference. |
| `compatibility` | No | 1–500 chars; environment requirements. |
| `metadata` | No | Map of string keys to string values. |
| `allowed-tools` | No | Space-separated tool list. Experimental. |

Note the divergence: **plugin names permit `.`, skill names do not.** A dotted plugin name cannot be reused verbatim as a skill name.

## 5. MCP servers

See `mcp-servers.md` for the full treatment. Summary of the normative points:

- Config lives only at `mcp.json` in the plugin root; never inline in `plugin.json`, never at an alternative core path (§7.2.1).
- Top-level: required `$schema` and `mcpServers`, no other fields. `mcpServers` maps names to server objects; empty is valid (§7.2.1).
- `$schema` must be the canonical MCP schema identifier and its version **must match** `plugin.json`'s (§10.1).
- Each server object must have `type` and match exactly one closed variant. Unknown field, unknown `type`, or a foreign-variant field ⇒ invalid entry (§7.2.1).
- **stdio**: `type`, `command` (required), `args`, `env`, `cwd`. `command` is a single token — bare name or `./` path — with no placeholder expansion. `cwd` omitted ⇒ plugin root; present ⇒ `./…`, `${PLUGIN_ROOT}`/`${PLUGIN_ROOT}/…`, or `${PLUGIN_DATA}`/`${PLUGIN_DATA}/…`, with post-expansion containment enforced (§7.2.1).
- **streamable-http / sse**: `type`, `url` (required), `headers`. Absolute HTTP(S) URL, no userinfo, no fragment, HTTPS unless loopback. Header names case-insensitive and unique; no expansion in `url` or headers (§7.2.1).
- `env` MUST NOT contain `PLUGIN_ROOT` or `PLUGIN_DATA` keys (§9.2).
- Plugins MUST NOT embed credentials in `env` or `headers` (§7.2.1, §9.2). No portable credential mechanism exists; authorization is client-managed and an auth failure is a connection failure, not a config error.
- Clients must support at least one of `stdio` / `streamable-http`; `sse` support is optional. The declared `type` is used for the initial connection; no fallback is defined (§7.2.1).

Loading failure boundaries are in §7.2.2 and tabulated in `mcp-servers.md`.

## 6. Client extensions

| Rule | § |
| ---- | -- |
| Client-specific manifest data MUST live under a reverse-domain namespace in `extensions`; values MUST be objects. | 8, 8.1 |
| Client-specific files MUST live in a top-level directory named exactly the namespace. | 8, 8.2 |
| A client MAY use either representation or both. | 8 |
| A namespace SHOULD be based on a domain the client controls and SHOULD stay stable. | 8 |
| Clients ignore namespaces they don't implement, without validating the contents. | 8.1, 11.1 |
| Agent Plugins assigns **no** portable discovery, validation, loading, or failure semantics to extension data or files. | 8 |

## 7. Environment and placeholders

**Subprocess environment** (§9.1). Clients launching stdio servers MUST provide:

- `PLUGIN_ROOT` — absolute path to the resolved plugin root.
- `PLUGIN_DATA` — absolute path to a client-managed persistent directory for that installed plugin instance. Created before launch, writable, preserved across updates, MAY be deleted on uninstall.

Use `PLUGIN_DATA` for installed dependencies, virtualenvs, generated code, caches, and other state that must survive updates. Use `PLUGIN_ROOT` for bundled scripts, binaries, and config.

The client chooses the base environment and MAY inherit, omit, or sanitize ambient variables. Configured `env` overlays that base; the client then sets `PLUGIN_ROOT`/`PLUGIN_DATA`, replacing equivalents. **Except for the platform executable search used to resolve a bare `command`, a conformant plugin MUST NOT depend on any base-environment variable the spec doesn't require or the config doesn't supply** (§9.1).

**Expansion** (§9.2). Only `${PLUGIN_ROOT}` and `${PLUGIN_DATA}`, only in `args` elements, `env` values, and `cwd`. Not in `env` keys, not in `command`, not in fixed component locations, not in `url` or headers. A single non-recursive textual replacement of every exact occurrence; introduced text is not rescanned. Unrecognized placeholder-like text stays literal, and no other environment-variable expansion is performed.

## 8. Versioning

- The spec version covers the normative text and both schemas, which are republished at the same version every release even when unchanged (§10.1).
- `plugin.json`'s `$schema` declares the targeted version; when `mcp.json` is present its `$schema` version MUST match. Mismatch invalidates the MCP config only (§10.1, §7.2.2).
- Published canonical schema identifiers are never reassigned to different contents. Plugins MAY keep targeting older versions (§10.1).
- Plugins SHOULD use SemVer for `version`: major = breaking, minor = backward-compatible feature, patch = backward-compatible fix. Clients MAY use it for update checks and cache freshness (§10.2).

## 9. Client behavior that constrains authors

These are client requirements, but each one forecloses an authoring shortcut.

| Client requirement | Consequence for the author | § |
| ------------------ | -------------------------- | -- |
| Clients MUST NOT fetch `$schema` at load time. | `$schema` is a version tag; the URL need not be reachable, and a custom URL is simply unrecognized. | 5.2, 7.2.1 |
| Clients MUST NOT search below `skills/<dir>/SKILL.md`. | Grouping skills into subfolders hides them entirely. | 7.1 |
| Clients MUST NOT assign semantics to unknown manifest fields. | Extra fields carry no information anywhere. Use `extensions`. | 5.2 |
| Whether configured `PATH` affects bare-command resolution is client-defined. | Bundled executables MUST use a `./` command. | 7.2.1 |
| Clients MAY sanitize the ambient environment. | Never assume `HOME`, `PATH`, or user shell config is present. | 9.1 |
| Clients set `PLUGIN_ROOT`/`PLUGIN_DATA` *after* applying `env`. | Attempting to override them is both invalid and futile. | 9.1, 9.2 |
| Clients MUST ignore unsupported component types and transports. | Non-v1 components are silently inert on clients that lack them — never a load error you can detect. | 7, 11.3 |
| Component failures are isolated and non-fatal. | Skills must not silently assume a sibling MCP server connected. | 11.3 |
| Clients MAY delete `PLUGIN_DATA` on uninstall and replace package contents on update. | `PLUGIN_DATA` is durable-but-disposable; the package is disposable. | 9.1 |

Minimum client conformance (§11.1) requires supporting at least one component type, so a skills-only client is conformant (§11.2). A plugin cannot assume both component types will be honored.

## 10. Canonical identifiers

```text
plugin.json  $schema  https://agent-plugins.org/schemas/1.0.0/plugin.schema.json
mcp.json     $schema  https://agent-plugins.org/schemas/1.0.0/mcp.schema.json
```

Both must carry the same version.
