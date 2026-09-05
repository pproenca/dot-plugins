### Feature

Build the requested behavior with a clear data model and evidence that it works.

1. Inspect the affected entry points, callers, and existing conventions. Use **how** when the subsystem needs a deeper walkthrough.
2. Settle the data shape and ownership before spreading logic across modules. Use **architect** when a consequential design choice has plausible competing answers.
3. Identify blocking prerequisites and independent work. Delegate bounded work when it improves throughput or confidence while you do useful local work. Use the configured `feature, refactoring` role when valid. Keep coupled code with one owner and isolate concurrent writers under the Codex collaboration contract.
4. Implement the smallest coherent change. Re-ground upstream-derived files against their source. Update affected consumers together and inspect delegated diffs yourself.
5. Verify the changed behavior on the relevant artifact and run required repository checks. An untested integration is a stated limitation, not a passing result. Stop expanding tests once the required checks and behavior evidence are sufficient.
6. Review the diff for unsupported guards, dead compatibility paths, unrelated changes, and comments that only narrate code. Use **interrogate** for unresolved consequential concerns.
7. If PR delivery is in scope, run **Opening a PR**. Otherwise leave the verified changes ready for review.

For larger work, sequence small verifiable units. Record the dependency and ownership decisions that matter; a single-file change does not need a throughput worksheet.

**Reply:** the resulting behavior, significant design choices, and verification.
