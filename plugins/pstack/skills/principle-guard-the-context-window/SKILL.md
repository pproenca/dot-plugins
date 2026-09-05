---
name: principle-guard-the-context-window
description: "Keep retrieval and tool results focused when outputs are large, files are long, or reads repeat."
---

# Guard the Context Window

Retrieve the evidence needed for the current decision and keep tool results bounded.

- Search the owning directories first. Exclude dependencies, generated output, and build artifacts unless the question concerns them. Inspect the generator and a representative generated result before expanding to the full output.
- Check file type and size before reading an unfamiliar executable or large file as text. Use metadata or the executable's documented inspection command for binaries.
- Filter structured results and logs before returning them to the model. Request specific fields or bounded excerpts; keep full evidence in a durable project artifact when it needs to survive the task. If a result is truncated, narrow the query rather than repeatedly requesting the same large output.
- Reuse unchanged source excerpts and instructions already available in context. Re-read when an edit or missing context makes it necessary.
- Delegate interpretation when it is independent useful work, not merely to move a large dump into another agent. Give that worker the same retrieval limits and ask for findings with source locations.
