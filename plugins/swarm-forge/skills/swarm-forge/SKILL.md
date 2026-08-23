---
name: swarm-forge
description: Run a SwarmForge swarm — install a pack of specialist agents into a project, launch them in tmux with one git worktree each, and tear the swarm down. Use for "swarmforge", "start a swarm", "two-pack/four-pack/six-pack", or setting up multi-agent orchestration on a repo.
compatibility: Requires zsh, git, tmux, Babashka (bb), and at least one configured agent CLI (codex, claude, copilot, or grok). macOS or Linux.
---

# SwarmForge

SwarmForge runs several AI agents as one team on a single repository. Each agent gets a
role prompt, its own git worktree, and its own tmux session. They pass work to each other
with file-based handoffs, and a human drives the whole thing from a local web cockpit.

## Before you start — read this out loud to the user

SwarmForge launches third-party agent CLIs **with permission checks disabled**. The
launcher passes `--yolo` to codex and copilot and `--permission-mode bypassPermissions` to
claude and grok, and the bundled pack configs pass `--yolo` explicitly. Those agents then
run unattended, committing to git worktrees of the user's repository.

Confirm the user wants this before installing, and prefer a scratch repository for a first
run. To reduce autonomy, edit `swarmforge/swarmforge.conf` after install and drop the
`--yolo` arguments.

Check the prerequisites first — the launcher hard-fails without them:

```bash
for c in zsh git tmux bb; do command -v "$c" >/dev/null || echo "missing: $c"; done
for c in codex claude copilot grok; do command -v "$c" >/dev/null && echo "backend: $c"; done
```

Babashka is the one people usually lack: `brew install borkdude/brew/babashka`.

## 1. Choose a pack

A *pack* is a roster: which agents exist, what each one does, and which backend runs it.
Full role-by-role detail is in [references/packs.md](references/packs.md).

| Pack | Agents | Use it when |
| --- | --- | --- |
| `two-pack` | coder, cleaner | Small tasks. A tight implement/refine loop, no specs. |
| `four-pack` | specifier, coder, refactorer, architect | Moderate work needing Gherkin specs without a gate per concern. |
| `six-pack` | specifier, coder, cleaner, architect, hardender, QA | Major work. Every quality gate gets its own agent. |
| `adversaries` | coder, reviewer | Legacy, pre-cockpit. Only if the user asks for it by name. |

If the user has not said, ask. The packs are not interchangeable mid-flight — switching
means re-installing and restarting.

## 2. Install it into the project

```bash
scripts/install_pack.sh <pack> <project-dir>
```

This does locally exactly what upstream's `./swarm` does over the network. It writes:

- `<project>/swarmforge/` — the roster, role prompts, and constitution;
- `<project>/swarmforge/scripts/` — the engine, and `<project>/close-swarm`;
- `<project>/.swarmforge/{tools,bin}/` — the Acceptance Pipeline tooling
  (`gherkin-parser`, `ir-dry-checker`, `gherkin-mutator`), pre-seeded from the copy bundled
  with this plugin;
- `<project>/swarm` and `.gitignore` entries for the runtime state.

**The result is self-contained.** Nothing in the project points back at this plugin, so it
keeps working if the plugin is upgraded, moved, or uninstalled — and no step needs network.
It does not touch the user's source.

Re-run with a different pack to switch. Use `--update` to refresh an existing project's
engine and tooling after a plugin upgrade, leaving its `swarmforge.conf`, `roles/`, and
constitution alone:

```bash
scripts/install_pack.sh --update <project-dir>
```

The install merges this plugin's shared constitution articles (`engineering`, `handoffs`,
`workflow`) into the pack's own articles, skipping any the pack already defines so a pack
keeps its overrides. It reports which it added and which it kept.

## 3. Check the host (automatic)

Install runs `scripts/doctor.sh` at the end. It exercises the real machinery against this
host's real configuration rather than assuming it matches:

- prerequisites and available agent backends;
- all 36 engine helpers and 5 terminal adapters present and executable;
- **whether the cockpit can actually type into an agent pane** — it stands up a tmux server
  with the host's own config and asserts delivery. This is the failure that reports success:
  if the dashboard cannot reach a pane, New Task and chat silently do nothing while the API
  returns `{"ok":true}`;
- whether teardown actually stops sessions;
- that the APS tooling runs offline and the project holds no path back into the plugin.

Run it any time:

```bash
scripts/doctor.sh <project-dir>
```

It exits non-zero on failure. Pass `--no-verify` to `install_pack.sh` to skip it during
install. **Run the doctor first whenever something behaves strangely** — it distinguishes a
broken host from a misbehaving agent.

## 4. Launch

```bash
cd <project-dir> && ./swarm
```

Startup initializes a git repo if there is not one, creates `.worktrees/<name>` per role,
installs a `commit-msg` hook that stamps `By <role>.` on commits, starts the handoff
daemon, and opens the cockpit in a browser. It prints the dashboard URL and also writes it
to `.swarmforge/dashboard-url`.

Driving the running swarm is a separate job — see the `swarm-forge-cockpit` skill.

Environment overrides, all set before `./swarm`:

| Variable | Effect |
| --- | --- |
| `SWARMFORGE_OPEN_BROWSER=0` | Print the dashboard URL, do not open a browser. |
| `SWARMFORGE_PREVENT_SLEEP=0` | Do not hold the machine awake while the swarm runs. |
| `SWARMFORGE_TERMINAL=<backend>` | `ghostty`, `terminal-app`, `iterm2`, `windows-terminal`, `none`. |

## 5. Tear down

Teardown from the cockpit header is the normal path. From a shell:

```bash
cd <project-dir> && ./close-swarm
```

Both kill the agent sessions, tmux, the handoff daemon, and the dashboard. Project files
stay on disk; `.worktrees/` and `.swarmforge/` remain until removed by hand.

## Troubleshooting

- **"Config not found"** — `install_pack.sh` was never run against this directory, or it
  was run against a different one.
- **"Required helper script not found"** — the project's `swarmforge/scripts/` is
  incomplete. Run `install_pack.sh --update`. Never add or remove files in that directory:
  the launcher copies it wholesale into every worktree on each launch, and validates all 36
  helpers on startup.
- **"SwarmForge engine missing"** from `./swarm` — the project's `swarmforge/scripts/` was
  deleted (it is gitignored, so a fresh clone will not have it). Run
  `install_pack.sh --update`.
- **"Dashboard did not start"** — `bb` is missing, or port binding failed. Check
  `.swarmforge/dashboard.log`.
- **Agents sit at a prompt doing nothing on first launch** — the agent CLI is asking its own
  question before SwarmForge can reach it. codex asks "Do you trust the contents of this
  directory?" the first time it runs somewhere new. Open the agent's pane from the Work
  Queue and answer it; SwarmForge cannot answer it for you.
- **New Task or chat appears to do nothing** — the cockpit reports success even when it
  cannot reach an agent. Run `scripts/doctor.sh <project-dir>`; it reproduces this exact
  path. Also check `.swarmforge/dashboard.log` for `inject failed`.
- **`swarm_tool.sh` reports a missing APS tool** — the pre-seeded tooling under
  `.swarmforge/` was removed. `swarm_tool.sh ensure <tool>` rebuilds it from the vendored
  copy without network; if that copy is gone too, run `install_pack.sh --update`.
