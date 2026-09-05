### Opening a PR

Use when PR delivery is part of the requested task. Follow repository conventions and the user's requested delivery state.

**Worktree.** Use the requested checkout and base. Create a worktree when isolation is needed. Collaboration agents share the parent checkout unless the parent creates separate worktrees. Before parallel writes, create one explicit worktree per branch and pass each owner its absolute path. The owner runs every command with that path as its working directory. Never assign two writers to one worktree. If the current checkout contains unrelated work or becomes snarled, preserve it and create a fresh worktree. Do not reset away existing changes.

**Commits.** Commit liberally; rebase into small, ordered commits before opening PRs. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs in a just-made commit; new commit when separable.

**PRs.** Inspect the diff for dead compatibility paths, unsupported guards, unrelated edits, and narrating comments before commit. Use **no-comments** for a requested independent comment audit or unresolved comment concerns. Use **technical-writing** or **unslop** when an editorial pass would improve the description.

**Titles and descriptions.** Follow repository conventions and its PR template. Lead with the concrete problem and resulting behavior. Describe significant tradeoffs, affected consumers, and verification results when they help review. Scale length to the change. Include screenshots or video when they substantiate a visual claim. A commit body does not restate its subject.

**Forge.** Resolve the forge before the first PR operation and keep that choice for create, edit, view, watch, and merge. GitHub CLI (`gh`) is the default. If `command -v origin` succeeds and Origin can resolve the repository, prefer `origin pr ...`; if Origin is absent or cannot resolve the repository, stay on `gh` and record the fallback. Do not require Graphite (`gt`).

**Size and stacks.** Split independently reviewable changes when it helps; a focused change can be one PR. A stack is a base-branch chain. The root PR targets trunk; each child branch rebases onto its parent's exact tip and its PR targets the parent branch. Create a child with `origin pr create --status open --base <parent-branch>` or `gh pr create --base <parent-branch>` according to the resolved forge. Retarget an existing child with `origin pr edit <pr> --base <parent-branch>` or `gh pr edit <pr> --base <parent-branch>`. Branch from trunk only for independent work. Rebase on trunk before substantial stack work.

**Readiness.** Follow the requested draft or ready state and repository practice. Mark a PR ready when its required checks and review preparation are complete. Run `origin pr view <number>` or `gh pr view <number>` according to the resolved forge before you refer to PR status.

**Babysit.** Opening a PR does not start a babysit. Post the URL and keep building. Finish the phase or stack first. Run a separate babysit pass only when the user asks for one after the whole stack exists. A babysit for each new PR stalls the build and spends checks on commits that later waves restart. Push back when feedback drifts from intent.

A delegated PR owner returns the URL, verification evidence, and remaining concerns. Run additional review or babysitting only when included in its assignment.
