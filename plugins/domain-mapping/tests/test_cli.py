from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import domain_map
import model_core
from test_model_core import ModelFixture

SCRIPT = Path(__file__).parents[1] / "scripts" / "domain_map.py"


class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.path = self.root / "model.json"
        self.model = ModelFixture(self.root).complete_model()
        self.path.write_bytes(domain_map.encoded(self.model))

    def tearDown(self):
        self.temp.cleanup()

    def call(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)], capture_output=True, text=True, check=False
        )

    def test_initialization_is_incomplete_and_never_overwrites(self):
        other = self.root / "new" / "model.json"
        result = self.call("init", other, "--system", "Cedar", "--description", "Cancellation")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.call("audit", other).returncode, 1)
        original = other.read_bytes()
        self.assertEqual(self.call("init", other, "--system", "Other", "--description", "Other").returncode, 2)
        self.assertEqual(original, other.read_bytes())

    def test_records_actual_failure_without_hiding_it_behind_earlier_pass(self):
        with patch.object(domain_map, "now", return_value="2026-09-06T12:00:00+00:00"), redirect_stdout(io.StringIO()):
            status = domain_map.main(
                [
                    "record-run",
                    str(self.path),
                    "--id",
                    "new-failure",
                    "--scenario",
                    "scenario-1",
                    "--result",
                    "failed",
                    "--evidence-id",
                    "ev-verification",
                ]
            )
        self.assertEqual(status, 0)
        output = json.loads(self.call("audit", self.path).stdout)
        self.assertFalse(output["recorded_checks_satisfied"])
        self.assertEqual(output["metrics"]["scenarios_current_passed"], 0)

    def test_result_with_changed_artifact_cannot_be_stamped(self):
        original = self.path.read_bytes()
        (self.root / "verification.txt").write_text("changed")
        result = self.call(
            "record-run",
            self.path,
            "--id",
            "new-pass",
            "--scenario",
            "scenario-1",
            "--result",
            "passed",
            "--evidence-id",
            "ev-verification",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(original, self.path.read_bytes())

    def test_duplicate_id_and_wrong_evidence_kind_preserve_model(self):
        original = self.path.read_bytes()
        for identifier, evidence in (("run-1", "ev-verification"), ("new-id", "ev-support")):
            result = self.call(
                "record-run",
                self.path,
                "--id",
                identifier,
                "--scenario",
                "scenario-1",
                "--result",
                "passed",
                "--evidence-id",
                evidence,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(original, self.path.read_bytes())

    def test_active_writer_lock_is_never_removed_or_bypassed(self):
        lock = self.path.with_name("model.json.lock")
        lock.write_text("another owner")
        original = self.path.read_bytes()
        result = self.call(
            "record-review",
            self.path,
            "--id",
            "new-review",
            "--kind",
            "challenge",
            "--result",
            "passed",
            "--evidence-id",
            "ev-review",
        )
        self.assertEqual(result.returncode, 2)
        self.assertEqual(lock.read_text(), "another owner")
        self.assertEqual(original, self.path.read_bytes())

    def test_failed_atomic_replace_preserves_original_and_cleans_temp(self):
        original = self.path.read_bytes()
        before = set(self.root.iterdir())
        with patch.object(domain_map.os, "replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                domain_map.atomic_write(self.path, b"new contents", expected=original)
        self.assertEqual(original, self.path.read_bytes())
        self.assertEqual(before, set(self.root.iterdir()))

    def test_compare_before_replace_rejects_intervening_edits(self):
        original = self.path.read_bytes()
        self.path.write_bytes(b"a newer model")
        with self.assertRaises(ValueError):
            domain_map.atomic_write(self.path, b"stale proposal", expected=original)
        self.assertEqual(self.path.read_bytes(), b"a newer model")

    def test_report_rebuild_is_repeatable_and_does_not_change_source(self):
        original = self.path.read_bytes()
        report = self.root / "reports" / "status.md"
        result = self.call("report", self.path, "--output", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        content = report.read_bytes()
        self.assertEqual(self.call("report", self.path, "--output", report, "--replace").returncode, 0)
        self.assertEqual(report.read_bytes(), content)
        self.assertEqual(self.path.read_bytes(), original)

    def test_report_cannot_overwrite_evidence_model_or_authored_notes(self):
        notes = self.root / "notes.md"
        notes.write_text("authored notes")
        for path in (self.path, self.root / "support.txt", notes):
            original = path.read_bytes()
            self.assertEqual(self.call("report", self.path, "--output", path, "--replace").returncode, 2)
            self.assertEqual(path.read_bytes(), original)

    def test_checkpoints_are_content_addressed_and_idempotent(self):
        first = self.call("checkpoint", self.path)
        second = self.call("checkpoint", self.path)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        target = Path(json.loads(first.stdout)["checkpoint"])
        self.assertEqual(target.read_bytes(), self.path.read_bytes())
        self.assertEqual(target.stem, hashlib.sha256(self.path.read_bytes()).hexdigest())

    def test_checkpoint_and_lesson_reject_external_symlinks(self):
        with tempfile.TemporaryDirectory() as other:
            outside = Path(other)
            try:
                (self.root / "checkpoints").symlink_to(outside, target_is_directory=True)
                (self.root / "lessons.jsonl").symlink_to(outside / "lessons.jsonl")
            except OSError as error:
                self.skipTest(f"Symlink creation unavailable on this host: {error}")
            self.assertEqual(self.call("checkpoint", self.path).returncode, 2)
            result = self.call(
                "lesson",
                self.path,
                "--case-id",
                "escape",
                "--failure",
                "example",
                "--proposal",
                "example",
                "--evidence-id",
                "ev-support",
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(list(outside.iterdir()), [])

    def test_lessons_are_proposals_preserving_previous_entries(self):
        original = self.path.read_bytes()
        for identifier in ("case-a", "case-b"):
            result = self.call(
                "lesson",
                self.path,
                "--case-id",
                identifier,
                "--failure",
                "Missed a condition",
                "--proposal",
                "Add an independent scenario",
                "--evidence-id",
                "ev-support",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
        journal = self.root / "lessons.jsonl"
        previous = journal.read_bytes()
        records = [json.loads(line) for line in journal.read_text().splitlines()]
        self.assertEqual([record["id"] for record in records], ["case-a", "case-b"])
        self.assertTrue(all(record["status"] == "proposed" for record in records))
        duplicate = self.call(
            "lesson",
            self.path,
            "--case-id",
            "case-a",
            "--failure",
            "Overwrite",
            "--proposal",
            "Overwrite",
            "--evidence-id",
            "ev-support",
        )
        self.assertEqual(duplicate.returncode, 2)
        self.assertEqual(journal.read_bytes(), previous)
        self.assertEqual(self.path.read_bytes(), original)

    def test_malformed_json_returns_operational_error_without_traceback(self):
        self.path.write_text("{")
        result = self.call("audit", self.path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", json.loads(result.stderr))
        self.assertNotIn("Traceback", result.stderr)

    def test_duplicate_result_keys_cannot_turn_failure_into_pass(self):
        original = self.path.read_text().replace('"result": "passed"', '"result": "failed", "result": "passed"', 1)
        self.path.write_text(original)
        result = self.call("audit", self.path)
        self.assertEqual(result.returncode, 2)
        self.assertIn("duplicate", result.stderr.lower())
        self.assertEqual(self.path.read_text(), original)

    def test_method_changes_invalidate_recorded_results(self):
        candidate = self.root / "candidate"
        shutil.copytree(SCRIPT.parent.parent, candidate, ignore=shutil.ignore_patterns("__pycache__"))
        with patch.object(model_core, "__file__", str(candidate / "scripts" / "model_core.py")):
            baseline = model_core.fingerprint(self.model)
            self.assertEqual(baseline, self.model["runs"][0]["basis"])
            for relative in ("skills/map-domain/SKILL.md", ".codex-plugin/plugin.json", "scripts/domain_map.py"):
                target = candidate / relative
                previous = target.read_bytes()
                target.write_bytes(previous + b"\n")
                result = model_core.audit(self.model, self.root)
                self.assertNotEqual(result["basis"], baseline)
                self.assertFalse(result["recorded_checks_satisfied"])
                self.assertEqual(result["metrics"]["scenarios_current_passed"], 0)
                target.write_bytes(previous)

    def test_failed_new_artifact_publication_leaves_no_partial_file(self):
        target = self.root / "new-model.json"
        before = set(self.root.iterdir())
        with patch.object(domain_map.os, "link", side_effect=OSError("publication failed")):
            with self.assertRaises(OSError):
                domain_map.atomic_write(target, b"complete contents")
        self.assertFalse(target.exists())
        self.assertEqual(set(self.root.iterdir()), before)
        domain_map.atomic_write(target, b"complete contents")
        self.assertEqual(target.read_bytes(), b"complete contents")

    @unittest.skipIf(os.name == "nt", "POSIX mode bits are not the Windows permission model")
    def test_replacement_preserves_existing_permission_bits(self):
        self.path.chmod(0o640)
        domain_map.atomic_write(self.path, b"replacement", expected=self.path.read_bytes())
        self.assertEqual(stat.S_IMODE(self.path.stat().st_mode), 0o640)

    def test_saved_report_reads_changes_committed_before_lock_acquisition(self):
        report = self.root / "report.md"
        original_lock = domain_map.writer_lock

        @contextmanager
        def intervening_writer(path):
            changed = json.loads(path.read_bytes())
            changed["runs"][0]["result"] = "failed"
            path.write_bytes(domain_map.encoded(changed))
            with original_lock(path):
                yield

        with patch.object(domain_map, "writer_lock", intervening_writer), redirect_stdout(io.StringIO()):
            status = domain_map.main(["report", str(self.path), "--output", str(report)])
        self.assertEqual(status, 0)
        self.assertIn("Recorded checks satisfied: false", report.read_text())


if __name__ == "__main__":
    unittest.main()
