---
name: swarm-forge-cockpit
description: Operate a running SwarmForge swarm from its web cockpit — start tasks, approve handoffs, answer agent clarifications, read the board and Work Queue, and tear down. Use for "the swarm dashboard", "approve the handoff", "the swarm is stuck", or driving agents already running.
compatibility: Requires a SwarmForge swarm already launched with ./swarm.
---

# The SwarmForge pack cockpit

The cockpit is the operator surface for a running swarm. Agents live in tmux; this is how a
human steers them. It is a local web app on `127.0.0.1` at an ephemeral port.

Find it at the URL printed by `./swarm`, or:

```bash
cat <project-dir>/.swarmforge/dashboard-url
```

If that file is missing the swarm is not running. If the page says **Swarm disconnected**,
the UI is live but the pack behind it is gone — the page polls `/api/state` every 2
seconds and shows that on failure.

## Layout

- **Header** — pack title, live marker, **New Task**, **Open** (master agent's pane),
  **Teardown**.
- **Attention** — the human gates. Only two things appear here: spec approvals and agent
  clarification requests. Treat an empty Attention panel as "nothing needs me".
- **Board** — one swimlane per role, plus a **Done** well. Cards are tasks, not stories; a
  card sits with whichever agent currently holds it.
- **Work Queue** — one row per role: task name, role name (click to open that agent's live
  pane), live/idle, and a six-bar activity thermometer.
- **Chat** — follow-ups to the master agent.

## Starting work

Click **New Task**, give a short **stable name** and the task text, then OK. That creates a
card in the master lane and injects `Task: <name>` plus the text into the master agent.

The name matters: every downstream role carries it as `task:` on every handoff, and it is
how the board tracks the card. Do not invent a second name in chat for the same work — the
card will not follow.

## The two Attention gates — do not confuse them

**Approval.** In packs with a `specifier`, the daemon holds the master agent's first
`git_handoff` until a human decides. Attention shows the task, a **Documents** menu for the
artifacts, **Approve**, and **Reject**. Approve delivers the handoff and moves the card.
Reject leaves the card with the specifier and tells that agent. `two-pack` and
`adversaries` have no specifier and therefore no approval gate.

**Request clarification.** An agent is blocked and is asking a human a question. Attention
shows the question and a text box; submitting injects the answer into that agent's pane.
Use the text box — Approve/Reject do not apply and will not answer the question.

## Reading the swarm

Cards move when the handoff daemon delivers a `git_handoff`. Click a card for its task
body. A card can show the agent's latest status sentence, scraped from the last pane line
containing "I'm" — treat it as a hint, not a report. The thermometer is a crude diff of
recent pane output, so it shows *motion*, not progress.

To see what an agent is really doing, click its role name in the Work Queue, or **Open** in
the header, to pop a live pane capture. Those windows are resizable and refresh on their
own. The agents stay in tmux; these views are read-only observation, not a replacement for
the cockpit.

## When it looks stuck

1. Check **Attention** — the usual cause is an unanswered gate.
2. Open the holding agent's pane and read the last lines. Agents wait quietly.
3. Check the daemon: `tail <project>/.swarmforge/daemon/handoffd.log`.
4. Check for a handoff that failed validation:
   `ls <project>/.swarmforge/handoffs/failed/`.

Do not hand-edit anything under `.swarmforge/handoffs/` to unstick a swarm, and do not
stage or commit it. It is runtime state with a lifecycle the daemon owns; editing it
desynchronizes the board from the agents.

## Stopping

**Teardown** in the header, then confirm. It kills the agent sessions, tmux, the handoff
daemon, and the dashboard itself. Project files stay on disk.

From a shell instead: `cd <project-dir> && ./close-swarm`. The install puts `close-swarm`
in the project, so this works whether or not the plugin is still installed.
