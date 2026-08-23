# Squad role contracts

Every squad role has a `.contract.edn` beside its `.prompt`. Persistent roles live in
`swarmforge/roles/`; transient worker templates live in `swarmforge/role-templates/`. The
engine reads the contract when it builds an assignment, and the prompt itself tells the
agent to read and obey it.

## Fields

| Key | Meaning |
| --- | --- |
| `:role` | Template name; must match the filename. |
| `:persistent` | True for squad-leader and troubleshooter. |
| `:handoff-targets` | Who this role may hand off to. Workers: `["squad-leader"]`. |
| `:may-spawn` | Only the squad-leader is true. |
| `:may-talk-to-user` | squad-leader and troubleshooter only. |
| `:may-web-search` | Mostly false; `cleaner` has it scoped to finding a property-testing framework. |
| `:may-fetch-tools` | Whether the role may install its own tooling. |
| `:may-run-broad-tests` | `senior-implementer` only. |
| `:required-tool-ids` | Tools that must be present before the role can work. |
| `:writes` / `:forbidden-writes` | Artifact classes the role may or may not produce. |
| `:artifact-roots` / `:forbidden-artifact-roots` | Directory scopes. |
| `:singleton` / `:batch-kind` | Scheduling. Caps are also enforced from `squad.conf`. |
| `:behavior-preserving` | The role may not change accepted behavior. |

## The shape of the team

Workers are defined by what they may write. Two examples, deliberately inverted:

```clojure
{:role "implementer"
 :handoff-targets ["squad-leader"]
 :may-web-search false
 :may-fetch-tools false
 :may-spawn false
 :may-talk-to-user false
 :required-tool-ids ["dependency-checker"]
 :writes ["production-code" "unit-tests" "acceptance-tests" "acceptance-pipeline"]
 :artifact-roots ["src/" "test/" "features/" "qa/" "acceptance/" "bb/"]
 :workflow-readiness-source "squad_next.sh"}
```

```clojure
{:role "squad-leader"
 :persistent true
 :may-talk-to-user true
 :may-spawn true
 :may-web-search true
 :writes ["orchestration-metadata" "assignment-instructions" "approval-records"
          "review-dispositions" "batch-manifests" "status-reports"]
 :forbidden-writes ["stories" "gherkin" "qa-procedures" "acceptance-test-infrastructure"
                    "production-code" "unit-tests" "review-reports" "hardening-changes"
                    "qa-scripts" "architecture-critiques" "cleanup-changes"]
 :singleton-roles ["hardener" "qa" "architect" "senior-implementer"]
 :transient-slot-config "max_transient_agents"}
```

The worker is defined by what it *may* write; the leader by what it may *not*. That is the
core invariant: the leader coordinates and never produces product artifacts, and no worker
can reach around it to another worker.

The `code-reviewer` is the sharpest case — it writes recommendations into `reviews/` and is
forbidden from editing `src/` or `test/`. Its recommendations go to the `hardener`, which
applies them, not back to the implementer.

## Editing them

Change a prompt and its contract in the same edit. A prompt instructing an agent to do
something its contract forbids yields an agent that stalls or is refused mid-assignment,
and the failure surfaces as a vague scheduling problem rather than a permission error.

Concurrency is not set here. `:singleton` documents intent, but the enforced caps come from
`max_active_template` in `swarmforge/squad.conf`, which is the only place that sets them.
