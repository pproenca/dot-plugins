---
name: swarm-forge-squad
description: Run the SwarmForge squad workflow — a persistent squad leader that spawns short-lived specialist workers on demand, each bound by a capability contract. Use for "squad", "squad leader", "spawn a worker", or backlog-driven multi-agent orchestration with approval gates.
compatibility: Requires zsh, git, tmux, Babashka (bb), and at least one configured agent CLI (codex, claude, copilot, or grok). macOS or Linux.
---

# SwarmForge squad

Squad is a different orchestration model from the SwarmForge packs, not a bigger pack. A
pack starts a fixed roster and leaves it running. Squad starts **two** persistent agents
and spawns everything else on demand, one worker per assignment, retiring each when its
work is done.

If the user wants a fixed team on a repo, they want the `swarm-forge` plugin instead.
Squad is for backlog-driven work where a leader decomposes stories and farms them out.

## Before you start — read this out loud to the user

Squad launches third-party agent CLIs with permission checks disabled and then spawns more
of them automatically, up to `max_transient_agents` (default 10). Those agents run
unattended against the user's repository.

Confirm the user wants this, and prefer a scratch repository for a first run. Review
`swarmforge/squad.conf` after install — it is where the concurrency caps and the human
approval gates live.

Prerequisites, all hard requirements:

```bash
for c in zsh git tmux bb; do command -v "$c" >/dev/null || echo "missing: $c"; done
for c in codex claude copilot grok; do command -v "$c" >/dev/null && echo "backend: $c"; done
```

## The two kinds of agent

**Persistent**, declared in `swarmforge/swarmforge.conf`, started by `./swarm`:

- **squad-leader** — Owns main git and orchestration. Merges each worker's handed-off SHA
  and resolves conflicts itself. Writes only orchestration metadata, assignments,
  approvals, and status — never product code. It is the only role that may spawn.
- **troubleshooter** — The operator's front door. Idle until a human calls it, then has
  full authority over swarm structure: add or remove stories, start or retire workers, edit
  packets. It answers rather than acting autonomously.

**Transient**, spawned per assignment from `swarmforge/role-templates/`, then retired:
`system-analyst`, `analyst`, `gherkin-writer`, `qa-procedure-writer`, `implementer`,
`cleaner`, `code-reviewer`, `hardener`, `qa`, `architect`, `senior-implementer`.

Each worker hands back only to the squad-leader and may not spawn. Strict hub and spoke.

## Capability contracts

Every role carries a `.contract.edn` beside its prompt — a machine-readable manifest the
engine reads when it builds an assignment. It declares what the agent may do
(`:may-spawn`, `:may-web-search`, `:may-talk-to-user`), where it may write
(`:artifact-roots`, `:forbidden-writes`), which tools it needs (`:required-tool-ids`), who
it hands off to (`:handoff-targets`), and scheduling facts (`:singleton`, `:batch-kind`).

```clojure
{:role "implementer"
 :handoff-targets ["squad-leader"]
 :may-spawn false
 :may-talk-to-user false
 :writes ["production-code" "unit-tests" "acceptance-tests" "acceptance-pipeline"]
 :artifact-roots ["src/" "test/" "features/" "qa/" "acceptance/" "bb/"]}
```

Editing a contract changes what that agent is permitted to do. Change the prompt and the
contract together — a prompt that tells an agent to do something its contract forbids will
produce an agent that stalls or is refused.

## Install and launch

```bash
scripts/install_squad.sh <project-dir>
cd <project-dir> && ./swarm
```

Install copies the roster, both role sets, contracts, project templates, the constitution,
and the engine into the project, and pre-seeds the Acceptance Pipeline tooling
(`gherkin-parser`, `ir-dry-checker`, `gherkin-mutator`) into squad's tool cache from the
copy bundled with this plugin.

**The result is self-contained.** Nothing in the project points back at this plugin, so it
keeps working if the plugin is upgraded, moved, or uninstalled — and no step needs network.

Use `--update` to refresh an existing project's engine and tooling without touching its
confs, roles, or role-templates:

```bash
scripts/install_squad.sh --update <project-dir>
```

Squad's remaining tools — `clj-mutate`, `crap4clj`, `dry4clj`, `dependency-checker` — are
Clojure-specific and are still fetched on demand by `squad_tool.sh ensure`, as upstream.
`squad_tool.sh require` fails closed (`SQUAD_TOOL_MISSING`, exit 3) rather than installing,
so a role blocked on one of those needs `ensure` to have run first.

## Tuning `swarmforge/squad.conf`

This is the file to read before a first run. It controls, with no hardcoded fallbacks:

| Setting | Meaning |
| --- | --- |
| `max_transient_agents N` | Total concurrent workers. |
| `transient_agent <backend>` | Global backend default for workers. |
| `transient_agent <template> <backend>` | Per-template override. |
| `max_active_template <template> N` | Per-template cap; `1` makes it a singleton. |
| `approval_required <artifact> true\|false` | Whether a human gates that artifact. |
| `save_agent_sessions true` | Keep a retired worker's pane under `.squad/sessions/`. |

Backend resolution order: `SWARMFORGE_SQUAD_AGENT` → per-template `transient_agent` →
global `transient_agent` → the squad-leader's backend. The values `squad-leader` and
`leader` are sentinels meaning "inherit the leader's backend", not CLI names.

The shipped defaults run writing roles on Codex and judging roles (`code-reviewer`,
`architect`) on Grok, gate the implementation plan, frame, Gherkin, and QA procedure behind
human approval, and make `hardener`, `qa`, `architect`, `senior-implementer`, and
`system-analyst` singletons.

## Operating it

Squad serves its own dashboard (`squadd`), separate from the pack cockpit — the URL is
printed at startup. The troubleshooter is the in-swarm operator: call it when you want to
change the swarm's shape rather than editing state by hand.

Handoff mechanics are shared with the packs: `swarm_handoff.sh`, `ready_for_next.sh`, and
`done_with_current.sh`, with runtime state under `.swarmforge/handoffs/`. Never hand-edit,
stage, or commit that state.

Tear down from the dashboard, or `cd <project-dir> && ./close-swarm`.
