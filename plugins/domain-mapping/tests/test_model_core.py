from __future__ import annotations

import copy
import hashlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from model_core import audit as audit_model  # noqa: E402
from model_core import fingerprint, load_obligations, validate


def audit(model, root):
    return audit_model(model, root, as_of=datetime(2001, 1, 1, tzinfo=timezone.utc))


def sha(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


class ModelFixture:
    def __init__(self, root: Path):
        self.root = root
        self.contents = {
            "support.txt": b"source support\n",
            "oracle.txt": b"independent oracle\n",
            "verification.txt": b"verification result\n",
            "review.txt": b"review notes\n",
        }
        for name, content in self.contents.items():
            (root / name).write_bytes(content)

    def evidence(self, evidence_id: str, kind: str, path: str, lineage: str) -> dict:
        return {
            "id": evidence_id,
            "kind": kind,
            "path": path,
            "sha256": sha(self.contents[path]),
            "lineage": lineage,
            "source": "fixture v1",
            "locator": path,
            "captured_at": "2000-09-05T10:00:00+00:00",
        }

    def complete_model(self) -> dict:
        aspects = load_obligations()["actor"]
        claims = [
            {
                "id": f"claim-{index}",
                "concept": "actor-1",
                "aspect": aspect,
                "statement": f"The actor has recorded {aspect} behavior.",
                "perspective": "observed",
                "status": "supported",
                "evidence_ids": ["ev-support"],
                "depends_on": ["claim-0"] if index == 1 else [],
            }
            for index, aspect in enumerate(aspects)
        ]
        model = {
            "schema_version": 1,
            "scope": {
                "id": "scope-1",
                "revision": "1",
                "system": "Legacy SaaS",
                "system_version": "2000-09-05",
                "perspective": "observed",
                "description": "Observed receptionist workflow",
                "conditions": ["UK tenant", "receptionist role"],
                "exclusions": [],
            },
            "concepts": [{"id": "actor-1", "kind": "actor", "name": "Receptionist", "context": "Scheduling"}],
            "relations": [],
            "claims": claims,
            "evidence": [
                self.evidence("ev-support", "source", "support.txt", "source-tree-v1"),
                self.evidence("ev-oracle", "observation", "oracle.txt", "blind-observation-v1"),
                self.evidence("ev-verification", "verification", "verification.txt", "run-v1"),
                self.evidence("ev-review", "review", "review.txt", "people-review-v1"),
            ],
            "inventory": [
                {
                    "id": "inventory-1",
                    "kind": "persona",
                    "description": "Receptionist persona",
                    "disposition": "mapped",
                    "concept_ids": ["actor-1"],
                    "evidence_ids": ["ev-support"],
                    "rationale": "",
                }
            ],
            "scenarios": [
                {
                    "id": "scenario-1",
                    "name": "Receptionist behavior",
                    "claim_ids": [claim["id"] for claim in claims],
                    "given": "A receptionist is authenticated in the declared tenant.",
                    "when": "They perform the mapped work.",
                    "then": "The independently observed outcome occurs.",
                    "oracle_evidence_ids": ["ev-oracle"],
                }
            ],
            "runs": [],
            "reviews": [],
        }
        basis = fingerprint(model)
        model["runs"] = [
            {
                "id": "run-1",
                "scenario_id": "scenario-1",
                "result": "passed",
                "basis": basis,
                "evidence_ids": ["ev-verification"],
                "recorded_at": "2000-09-05T11:00:00+00:00",
            }
        ]
        model["reviews"] = [
            {
                "id": f"review-{kind}",
                "kind": kind,
                "result": "passed",
                "basis": basis,
                "evidence_ids": ["ev-review"],
                "recorded_at": "2000-09-05T12:00:00+00:00",
            }
            for kind in ("walkthrough", "blind_inventory", "challenge")
        ]
        return model


class ModelCoreTests(unittest.TestCase):
    def test_malformed_record_ids_and_evidence_lists_return_errors(self):
        for collection, field, value in (
            ("evidence", "id", []),
            ("evidence", "id", {}),
            ("runs", "evidence_ids", [{}]),
            ("reviews", "evidence_ids", [{}]),
        ):
            broken = copy.deepcopy(self.model)
            broken[collection][0][field] = value
            result = audit(broken, self.root)
            self.assertTrue(result["structural_errors"])
            self.assertFalse(result["recorded_checks_satisfied"])

    def test_future_pass_cannot_hide_a_real_failure(self):
        future = copy.deepcopy(self.model["runs"][0])
        future.update(id="future-pass", recorded_at="9999-12-31T23:59:59+00:00")
        failed = copy.deepcopy(self.model["runs"][0])
        failed.update(id="real-failure", result="failed", recorded_at="2000-09-06T00:00:00+00:00")
        self.model["runs"].extend([future, failed])
        result = audit(self.model, self.root)
        self.assertFalse(result["recorded_checks_satisfied"])
        self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)
        self.assertIn("future_result", {item["code"] for item in result["issues"]})

    def test_custom_hypothesis_keeps_frontier_open(self):
        self.model["claims"].append(
            {
                "id": "custom-question",
                "concept": "actor-1",
                "aspect": "emergency-override",
                "statement": "An emergency override may exist.",
                "perspective": "observed",
                "status": "hypothesis",
                "evidence_ids": [],
                "depends_on": [],
            }
        )
        for record in [*self.model["runs"], *self.model["reviews"]]:
            record["basis"] = fingerprint(self.model)
        result = audit(self.model, self.root)
        self.assertFalse(result["recorded_checks_satisfied"])
        self.assertIn("custom-question", {item["subject"] for item in result["frontier"]})

    def test_run_artifact_cannot_be_its_own_oracle(self):
        self.model["scenarios"][0]["oracle_evidence_ids"] = ["ev-verification"]
        for record in [*self.model["runs"], *self.model["reviews"]]:
            record["basis"] = fingerprint(self.model)
        result = audit(self.model, self.root)
        self.assertFalse(result["recorded_checks_satisfied"])
        self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)
        self.assertIn("circular_run_oracle", {item["code"] for item in result["issues"]})

    def test_relabeling_run_artifact_does_not_create_independent_oracle(self):
        copied = copy.deepcopy(next(item for item in self.model["evidence"] if item["id"] == "ev-verification"))
        copied.update(id="copied-oracle", kind="observation", lineage="different-label")
        self.model["evidence"].append(copied)
        self.model["scenarios"][0]["oracle_evidence_ids"] = ["copied-oracle"]
        for record in [*self.model["runs"], *self.model["reviews"]]:
            record["basis"] = fingerprint(self.model)
        result = audit(self.model, self.root)
        self.assertFalse(result["recorded_checks_satisfied"])
        self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.fixture = ModelFixture(self.root)
        self.model = self.fixture.complete_model()

    def tearDown(self):
        self.temp.cleanup()

    def test_complete_recorded_scope_can_satisfy_conservative_gate(self):
        self.assertEqual(validate(self.model), [])

        result = audit(self.model, self.root)

        self.assertTrue(result["recorded_checks_satisfied"])
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["frontier"], [])
        self.assertEqual(result["metrics"]["obligations_total"], 5)
        self.assertEqual(result["metrics"]["obligations_supported"], 5)
        self.assertEqual(result["metrics"]["scenarios_current_passed"], 1)
        self.assertIn("does not prove universal completeness", result["disclaimer"])

    def test_actual_hash_drift_transitively_invalidates_dependent_claim(self):
        (self.root / "support.txt").write_bytes(b"changed after capture\n")

        result = audit(self.model, self.root)

        self.assertFalse(result["recorded_checks_satisfied"])
        codes = {(item["code"], item["subject"]) for item in result["issues"]}
        self.assertIn(("evidence_hash_mismatch", "ev-support"), codes)
        dependent = next(
            item for item in result["issues"] if item["code"] == "claim_not_current" and item["subject"] == "claim-1"
        )
        self.assertIn("dependency 'claim-0'", dependent["message"])
        self.assertIn("evidence 'ev-support'", dependent["message"])
        self.assertEqual(result["metrics"]["obligations_supported"], 0)

    def test_fingerprint_ignores_order_stamps_and_unreferenced_evidence(self):
        changed = copy.deepcopy(self.model)
        changed["claims"].reverse()
        changed["scope"]["conditions"].reverse()
        changed["scenarios"][0]["claim_ids"].reverse()
        changed["runs"][0]["result"] = "failed"
        changed["reviews"] = []
        unreferenced = self.fixture.evidence("unused", "documentation", "support.txt", "unused-lineage")
        unreferenced["notes"] = "This is intentionally irrelevant to the modeled claims."
        changed["evidence"].append(unreferenced)

        self.assertEqual(fingerprint(changed), fingerprint(self.model))

        changed["claims"][0]["statement"] += " Changed semantics."
        self.assertNotEqual(fingerprint(changed), fingerprint(self.model))

    def test_newer_failure_is_not_hidden_by_older_pass(self):
        self.model["runs"].append(
            {
                "id": "run-2",
                "scenario_id": "scenario-1",
                "result": "failed",
                "basis": fingerprint(self.model),
                "evidence_ids": ["ev-verification"],
                "recorded_at": "2000-09-05T13:00:00+00:00",
            }
        )

        result = audit(self.model, self.root)

        self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)
        self.assertIn(
            ("scenario_not_passed", "scenario-1"),
            {(item["code"], item["subject"]) for item in result["issues"]},
        )

    def test_shared_lineage_prevents_oracle_from_counting_as_independent(self):
        oracle = next(item for item in self.model["evidence"] if item["id"] == "ev-oracle")
        oracle["lineage"] = "source-tree-v1"
        current_basis = fingerprint(self.model)
        self.model["runs"][0]["basis"] = current_basis
        for review in self.model["reviews"]:
            review["basis"] = current_basis

        result = audit(self.model, self.root)

        self.assertIn(
            ("non_independent_oracle", "scenario-1"),
            {(item["code"], item["subject"]) for item in result["issues"]},
        )
        self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)

    def test_validation_rejects_malformed_references_paths_and_timestamps(self):
        broken = copy.deepcopy(self.model)
        broken["evidence"][0]["path"] = "C:/outside.txt"
        broken["claims"][0]["depends_on"] = ["missing-claim"]
        broken["runs"][0]["recorded_at"] = "2000-09-05T10:00:00"
        broken["unexpected"] = True

        errors = validate(broken)

        self.assertTrue(any("unknown top-level field: unexpected" == error for error in errors))
        self.assertTrue(any("relative POSIX path" in error for error in errors))
        self.assertTrue(any("unknown claim 'missing-claim'" in error for error in errors))
        self.assertTrue(any("ISO timestamp with a timezone" in error for error in errors))

    def test_audit_handles_non_object_without_traceback_or_vacuous_success(self):
        result = audit([], self.root)

        self.assertFalse(result["recorded_checks_satisfied"])
        self.assertTrue(result["structural_errors"])
        self.assertEqual(result["metrics"]["concepts"], 0)

    def test_audit_handles_unhashable_enum_value_as_structural_error(self):
        broken = copy.deepcopy(self.model)
        broken["claims"][0]["status"] = ["supported"]

        result = audit(broken, self.root)

        self.assertFalse(result["recorded_checks_satisfied"])
        self.assertTrue(any("claims[0].status is invalid" == error for error in result["structural_errors"]))

    def test_cycles_require_each_claim_to_have_independent_evidence(self):
        first, second = self.model["claims"][:2]
        first["depends_on"] = [second["id"]]
        second["depends_on"] = [first["id"]]
        first["evidence_ids"] = []
        current_basis = fingerprint(self.model)
        self.model["runs"][0]["basis"] = current_basis
        for review in self.model["reviews"]:
            review["basis"] = current_basis

        result = audit(self.model, self.root)

        dependent_issue = next(
            item for item in result["issues"] if item["code"] == "claim_not_current" and item["subject"] == second["id"]
        )
        self.assertIn(f"dependency '{first['id']}'", dependent_issue["message"])
        self.assertIn("claim has no evidence", dependent_issue["message"])

    def test_equal_latest_timestamps_with_different_basis_are_not_accepted(self):
        conflicting = copy.deepcopy(self.model["runs"][0])
        conflicting["id"] = "run-same-time-stale"
        conflicting["basis"] = "f" * 64
        self.model["runs"].append(conflicting)

        result = audit(self.model, self.root)

        self.assertIn(
            ("conflicting_latest_runs", "scenario-1"),
            {(item["code"], item["subject"]) for item in result["issues"]},
        )
        self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)


if __name__ == "__main__":
    unittest.main()
