# MCP servers in `mcp.json`

Agent Plugins defines its own portable MCP configuration format. It is **not** any client's native format — clients translate it. Field names and shapes that work in a client-specific config file are not evidence of what is valid here.

## Contents

- [File shape](#file-shape)
- [The closed union](#the-closed-union)
- [stdio](#stdio)
- [streamable-http and sse](#streamable-http-and-sse)
- [Placeholder expansion](#placeholder-expansion)
- [What a client does on failure](#what-a-client-does-on-failure)
- [Worked example](#worked-example)

## File shape

Fixed location: `mcp.json` at the plugin root (§7.2.1). MCP config may **not** be declared inline in `plugin.json`, and no alternative path exists.

Exactly two top-level fields, both required, nothing else:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {}
}
```

An empty `mcpServers` object is valid.

`$schema` must be the canonical identifier for the version, and **its version must match the version declared in `plugin.json`** (§10.1). A mismatch — or a malformed file, or an unknown top-level field — disables MCP for the entire plugin while other component types keep loading (§7.2.2 rule 2). This is the highest-blast-radius mistake in the format: one wrong character in `$schema` silently removes every server.

## The closed union

Each member of `mcpServers` is a server configuration object. It **must** have `type`, and it must match exactly one variant. Three things independently invalidate an entry (§7.2.1):

1. an unknown field,
2. an unknown `type` value,
3. a field belonging to a *different* variant — `command` on an `sse` server, `headers` on a `stdio` server.

An invalid entry is skipped; sibling servers and other component types still load (§7.2.2 rule 3).

## stdio

| Field     | Type              | Required | Notes                                          |
| --------- | ----------------- | -------- | ---------------------------------------------- |
| `type`    | `"stdio"`         | Yes      |                                                |
| `command` | string            | Yes      | Single executable token.                       |
| `args`    | string[]          | No       | Placeholders expand.                           |
| `env`     | object of strings | No       | Placeholders expand in values, not keys.       |
| `cwd`     | string            | No       | Three permitted forms; placeholders expand.    |

### `command`

One executable token — **not** a shell command string. Only two forms are legal:

- a **bare executable name** (`npx`, `python3`), resolved by the platform's executable search rules; or
- a **plugin-relative path beginning with `./`** (`./bin/validator`), resolved against the plugin root.

Everything else is invalid: absolute paths, `../` paths, `bin/server` without the `./`, anything with spaces, pipes, redirects, or quoting. Treating `command` as a single token is what lets clients launch it without parsing and escaping author-written shell syntax.

**No placeholder expansion happens in `command`** (§9.2). `${PLUGIN_ROOT}/bin/tool` does not work — it stays literal and fails to resolve. The `./` form already resolves against the plugin root, which is why the placeholder is unnecessary here.

Whether a configured `PATH` participates in resolving a bare name is client-defined, and **a conformant plugin must not depend on it** (§7.2.1). Therefore: *if the executable ships inside the package, the `command` must be a `./` path.* A bare name is only appropriate for a tool the plugin expects the user's system to already provide, and that expectation belongs in the plugin's documentation.

Clients may use a platform command interpreter where one is required to launch the resolved executable (a `.bat`/`.cmd` on Windows), but must keep `command` as one token with `args` passed separately.

### `cwd`

Omitted, the working directory is the plugin root. Present, it must be exactly one of:

1. a plugin-relative path beginning with `./` — e.g. `./data`
2. `${PLUGIN_ROOT}` or a path beginning with `${PLUGIN_ROOT}/`
3. `${PLUGIN_DATA}` or a path beginning with `${PLUGIN_DATA}/`

Placeholders expand *before* resolution. Forms 1 and 2 must land inside the plugin root; form 3 must land inside the plugin data directory. Any other shape — a bare relative path, an absolute path, a `../` escape — invalidates the entry.

Use `${PLUGIN_DATA}` when the server writes: package contents are replaced on update, `PLUGIN_DATA` is preserved.

### `env`

An object of string keys to string values, overlaid on a client-chosen base environment.

`env` **must not** contain entries named `PLUGIN_ROOT` or `PLUGIN_DATA` — such an entry invalidates the server (§9.2). The client supplies both itself, setting them *after* applying `env`, so an attempted override would be discarded anyway.

`env` values are visible package data. **Never put credentials there.** The spec defines no portable secret mechanism; credential storage and authorization are client-managed.

## streamable-http and sse

| Field     | Type                           | Required | Notes                          |
| --------- | ------------------------------ | -------- | ------------------------------ |
| `type`    | `"streamable-http"` or `"sse"` | Yes      |                                |
| `url`     | string                         | Yes      | No placeholder expansion.      |
| `headers` | object of strings              | No       | No placeholder expansion.      |

`streamable-http` is the current MCP Streamable HTTP transport. `sse` is the **deprecated** HTTP+SSE transport from the MCP 2024-11-05 spec — it does not mean "SSE responses within Streamable HTTP", and client support for it is optional. Choose `streamable-http` unless the server genuinely only speaks the old transport.

`url` must be an absolute HTTP or HTTPS URL with **no user information and no fragment**. Non-loopback endpoints must use HTTPS; plain HTTP is permitted only when the host is exactly `localhost` or a loopback IP literal.

`headers` are fixed headers sent to the configured origin. Names are case-insensitive, so two entries differing only in case make the entry invalid. Names and values must be valid HTTP header fields. Client-generated HTTP/MCP/authorization headers win over configured ones with the same name, and a client will not forward configured headers to a different origin across a redirect without explicit user authorization.

**No expansion of any kind occurs in `url`, header names, or header values** (§7.2.1) — a `${PLUGIN_ROOT}` there stays literal. And as with `env`: headers are visible package data, so no credentials.

### Transport support

A client supporting MCP must implement at least one of `stdio` or `streamable-http` and should implement both; `sse` is optional. The client uses the declared `type` for its initial connection attempt and the format defines no fallback. An entry whose transport the client doesn't support is skipped, and the rest of the plugin loads normally.

## Placeholder expansion

Only `${PLUGIN_ROOT}` and `${PLUGIN_DATA}` expand, and only in **`args` elements, `env` values, and `cwd`** (§9.2).

| Location            | Expands? |
| ------------------- | -------- |
| `args` elements     | Yes      |
| `env` values        | Yes      |
| `cwd`               | Yes      |
| `env` keys          | No       |
| `command`           | No       |
| `url`, `headers`    | No       |

Expansion is a single non-recursive textual replacement of every exact occurrence; text introduced by a replacement is not rescanned. Unrecognized placeholder-like text stays literal — `${HOME}` is the four characters plus `HOME`, not the user's home directory, and no other environment-variable substitution is performed.

`PLUGIN_ROOT` is the absolute path to the plugin root. `PLUGIN_DATA` is an absolute path to a client-managed, writable, per-installation directory that survives plugin updates and may be deleted on uninstall. Both are also present in the subprocess environment (§9.1), so a bundled program can read them directly instead of relying on config-time expansion.

## What a client does on failure

Worth knowing because it determines how visible a mistake is:

| Problem                                                   | Result                                          |
| --------------------------------------------------------- | ----------------------------------------------- |
| `mcp.json` invalid JSON / bad top-level shape / `$schema` mismatch | **All** MCP disabled for the plugin; rest of plugin loads |
| One server entry violates its variant rules               | That server skipped; others load                |
| Transport not supported by the client                     | That server skipped; others load                |
| Server fails to start, connect, authenticate, or handshake | Reported; everything else keeps loading         |

Authorization failure is a *connection* failure, not invalid configuration. Don't try to fix it in `mcp.json`.

## Worked example

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "local-validator": {
      "type": "stdio",
      "command": "./bin/validator",
      "args": ["--data", "${PLUGIN_DATA}/validator"],
      "env": { "CONFIG": "${PLUGIN_ROOT}/config.json" },
      "cwd": "${PLUGIN_ROOT}"
    },
    "deployment-api": {
      "type": "streamable-http",
      "url": "https://deploy.example.com/mcp",
      "headers": { "X-Tenant": "public-tenant" }
    },
    "legacy-events": {
      "type": "sse",
      "url": "https://legacy.example.com/sse"
    }
  }
}
```

Note the division of labour: the bundled binary is referenced with `./`, its read-only config with `${PLUGIN_ROOT}`, and its writable state with `${PLUGIN_DATA}`.
