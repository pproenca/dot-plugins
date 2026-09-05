---
name: principle-prove-it-works
description: "Apply after completing a task, before declaring done. Verify against the real artifact (run the feature, read the actual value, inspect the diff), not a proxy, self-report, or 'it compiles.'. Use when explicitly invoked or when this exact workflow is needed."
---

# Prove It Works

Verify every task output by checking the real thing directly. Do not infer from proxies, self-reports, or "it compiles."

**Why:** Unverified work has unknown correctness. Indirect verification (file mtimes, output freshness, agent self-reports, cached screenshots) feels cheaper than direct observation. Acting on a wrong inference costs far more than checking the source.

**Pattern:** After completing any task, ask: "how do I prove this actually works?"

Check the real thing, not a proxy:
- Check process liveness directly, not indirectly through derived state
- Read the actual value, not a cached or derived representation
- When verification fails, suspect the observation method before suspecting the system

Code and features:
1. Build it (necessary but not sufficient)
2. Run it and exercise the actual feature path
3. Check the full chain: does data flow from input to output?
4. For integrations, test the full communication path end-to-end

Delegation: trust artifacts, not self-reports.
When verifying delegated work, inspect the actual output artifact (git diff, file contents, runtime behavior), not the delegate's summary. Agents report what they intended, not always what happened.

## Script the check when you can

Prefer an existing reproducible check. Add a script when a repeated or complex comparison needs one. Match verification to the claim: documentation edits need content and link checks; runtime changes need behavior evidence. Once required checks and relevant evidence pass, repeat or broaden testing only for a new change, failure, or unresolved concern.

Keep the artifact visible for the human. Commit it only for large or complex work where the trail has to be auditable later, like a big port or migration (the **show-me-your-work** skill). Most work just needs it visible, not committed.
