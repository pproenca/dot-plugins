### Pause safely

**You own a clean stop. Leave a checkpoint a cold-start agent can resume from.** For "pause safely", "I need to go offline", "restart Codex", or "board my flight", and when context is about to compact or summarize. This is explicit only. On "keep going", "going to bed, keep going", or "don't stop", do not pause.

1. Stop at a safe boundary. Finish the current atomic step or back out of it. Never stop mid-edit in a known-broken state. Start nothing new. Stop each nested agent's current turn when the collaboration capability supports interruption. Otherwise record every running agent and do not claim a clean stop.
2. Don't cross an irreversible line to pause. No PR and no push unless you already had one out.
3. Make the work durable. Preserve uncommitted edits on disk and record the dirty paths. Commit only changes owned by this task when the user has authorized a commit. Do not include unrelated user edits in a WIP commit. Record any broken state in the resume note.
4. Write the resume note off-context. Capture intent, what you were doing, progress and what's verified, current state, next steps, key files, and gotchas. Use a durable workspace file or the task summary for the resume note. Do not rely on a temporary directory as the only copy. If a show-me-your-work trail exists, point at it instead of duplicating it.

**Reply:** where you are in the loop, what's on disk versus still in your head (paths, no diff dumps), the commits you made and whether the tree is clean, and the first action on resume. This is a pause, not a final report. Resume is the Session pickup playbook reading this note.
