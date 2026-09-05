#!/usr/bin/env python3
"""Local bookkeeping for evidence-backed domain mapping; never executes experiments."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
import tempfile
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from model_core import audit, fingerprint, validate
from schema_check import decode_json

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
REPORT_HEADER = "# Domain mapping report\n"


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")


def read_model(path):
    raw = path.read_bytes()
    model = decode_json(raw)
    errors = validate(model)
    if errors:
        raise ValueError("Invalid model:\n" + "\n".join(errors))
    return model, raw


def atomic_write(path, data, *, expected=None):
    """Detect prior edits under a cooperative writer lock; exclusive-create new artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if expected is None:
            # Same-directory hard-link publication is atomic and never replaces a target.
            os.link(temporary, path)
        else:
            if path.read_bytes() != expected:
                raise ValueError("File changed during this operation; reconcile the newer version first.")
            os.chmod(temporary, stat.S_IMODE(path.stat().st_mode))
            os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


@contextmanager
def writer_lock(model_path):
    lock = model_path.with_name(model_path.name + ".lock")
    token = encoded({"pid": os.getpid(), "token": uuid.uuid4().hex})
    try:
        with lock.open("xb") as stream:
            stream.write(token)
    except FileExistsError as exc:
        raise ValueError(f"Writer lock exists: {lock}. Inspect its owner; do not remove an active lock.") from exc
    try:
        yield
    finally:
        if lock.exists() and lock.read_bytes() == token:
            lock.unlink()


def now():
    return datetime.now(timezone.utc).isoformat()


def fresh_evidence(model, model_path, identifiers, kind=None):
    records = {record["id"]: record for record in model["evidence"]}
    for identifier in identifiers:
        if identifier not in records:
            raise ValueError(f"Unknown evidence: {identifier}")
        record = records[identifier]
        if kind is not None and record["kind"] != kind:
            raise ValueError(f"Evidence {identifier} must have kind {kind}.")
        path = (model_path.parent / record["path"]).resolve()
        if not path.is_relative_to(model_path.parent) or not path.is_file():
            raise ValueError(f"Evidence {identifier} is missing or outside the project.")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError(f"Evidence {identifier} changed; inspect it before recording a result.")


def record_result(args, path):
    with writer_lock(path):
        model, raw = read_model(path)
        is_run = args.command == "record-run"
        fresh_evidence(model, path, args.evidence_id, "verification" if is_run else "review")
        record = {
            "id": args.id,
            "result": args.result,
            "basis": fingerprint(model),
            "evidence_ids": args.evidence_id,
            "recorded_at": now(),
        }
        record["scenario_id" if is_run else "kind"] = args.scenario if is_run else args.kind
        model["runs" if is_run else "reviews"].append(record)
        errors = validate(model)
        if errors:
            raise ValueError("\n".join(errors))
        atomic_write(path, encoded(model), expected=raw)
    return {"recorded": record, "notice": "Recorded supplied results only; no experiment or review was executed."}


def render_report(model, result):
    lines = [
        REPORT_HEADER.rstrip(),
        "",
        f"Scope: {model['scope']['description']}",
        f"System: {model['scope']['system']} / {model['scope']['system_version']}",
        f"Scope revision: {model['scope']['revision']}",
        f"Basis: {result['basis']}",
        "",
        result["disclaimer"],
        "",
        "## Recorded metrics",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {key} | {value} |" for key, value in result["metrics"].items())
    lines.extend(
        [
            "",
            f"Recorded checks satisfied: {str(result['recorded_checks_satisfied']).lower()}",
            "",
            "## Outstanding work",
            "",
        ]
    )
    for item in result["frontier"]:
        lines.append(f"- {item['subject']} / {item['aspect']}: {item['reason']}")
    if not result["frontier"]:
        lines.append("No generated frontier items. Independent semantic review still applies.")
    lines.extend(["", "## Integrity and verification issues", ""])
    lines.extend(f"- {item['code']} [{item['subject']}]: {item['message']}" for item in result["issues"])
    lines.extend(f"- Invalid structure: {error}" for error in result["structural_errors"])
    if not result["issues"] and not result["structural_errors"]:
        lines.append("No issues found by the record checker.")
    return "\n".join(lines) + "\n"


def save_report(path, model, output, content, replace):
    target = Path(output).expanduser().resolve()
    protected = {path}
    protected.update((path.parent / item["path"]).resolve() for item in model["evidence"])
    if (
        not target.is_relative_to(path.parent)
        or target in protected
        or target.is_relative_to(PLUGIN_ROOT)
        or target.is_relative_to(path.parent / "checkpoints")
    ):
        raise ValueError(
            "Report output must stay inside the model project and outside model, evidence, "
            "checkpoints, and plugin source."
        )
    expected = None
    if target.exists():
        if not replace:
            raise ValueError("Report already exists; use --replace only for a generated report.")
        expected = target.read_bytes()
        if not expected.startswith(REPORT_HEADER.encode()):
            raise ValueError("Refusing to replace a file that is not a generated domain mapping report.")
    atomic_write(target, content.encode("utf-8"), expected=expected)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Create an incomplete project model without overwriting anything")
    init.add_argument("model")
    init.add_argument("--system", required=True)
    init.add_argument("--description", required=True)
    for command in ("audit", "frontier", "checkpoint", "basis"):
        sub.add_parser(command).add_argument("model")
    report = sub.add_parser("report", help="Render a disposable Markdown report")
    report.add_argument("model")
    report.add_argument("--output")
    report.add_argument("--replace", action="store_true")
    for name in ("record-run", "record-review"):
        command = sub.add_parser(name, help="Stamp an actual result; does not execute it")
        command.add_argument("model")
        command.add_argument("--id", required=True)
        command.add_argument("--result", required=True, choices=["passed", "failed", "blocked"])
        command.add_argument("--evidence-id", action="append", required=True)
        if name == "record-run":
            command.add_argument("--scenario", required=True)
        else:
            command.add_argument("--kind", required=True, choices=["walkthrough", "blind_inventory", "challenge"])
    lesson = sub.add_parser("lesson", help="Append an improvement proposal without applying it")
    lesson.add_argument("model")
    for name in ("case-id", "failure", "proposal"):
        lesson.add_argument("--" + name, required=True)
    lesson.add_argument("--evidence-id", action="append", required=True)
    args = parser.parse_args(argv)
    path = Path(args.model).expanduser().resolve()
    try:
        result, status = execute(args, path)
        if result is not None:
            print(result if isinstance(result, str) else json.dumps(result, indent=2, ensure_ascii=False))
        return status
    except (OSError, ValueError, TypeError, KeyError, OverflowError, RecursionError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


def execute(args, path):
    if args.command == "init":
        model = {
            "schema_version": 1,
            "scope": {
                "id": "scope-" + uuid.uuid4().hex,
                "revision": "1",
                "system": args.system,
                "system_version": "unresolved",
                "perspective": "observed",
                "description": args.description,
                "conditions": [],
                "exclusions": [],
            },
        }
        model.update(
            {
                key: []
                for key in ("concepts", "relations", "claims", "evidence", "inventory", "scenarios", "runs", "reviews")
            }
        )
        errors = validate(model)
        if errors:
            raise ValueError("\n".join(errors))
        atomic_write(path, encoded(model))
        return {"created": str(path), "notice": "Incomplete scope; run audit to see the discovery frontier."}, 0
    if args.command in {"record-run", "record-review"}:
        return record_result(args, path), 0
    if args.command == "report" and args.output:
        with writer_lock(path):
            model, _ = read_model(path)
            result = audit(model, path.parent)
            content = render_report(model, result)
            save_report(path, model, args.output, content, args.replace)
        return {"report": str(Path(args.output).expanduser().resolve())}, 0
    model, raw = read_model(path)
    if args.command == "basis":
        return {"basis": fingerprint(model)}, 0
    if args.command == "checkpoint":
        digest = hashlib.sha256(raw).hexdigest()
        target = path.parent / "checkpoints" / (digest + ".json")
        if target.parent.is_symlink() or not target.resolve().is_relative_to(path.parent):
            raise ValueError("Checkpoint directory must be a real directory inside the model project.")
        if target.exists():
            if target.read_bytes() != raw:
                raise ValueError("Existing checkpoint has different bytes; preserve and investigate it.")
        else:
            atomic_write(target, raw)
        return {"checkpoint": str(target), "sha256": digest}, 0
    if args.command == "lesson":
        with writer_lock(path):
            model, _ = read_model(path)
            fresh_evidence(model, path, args.evidence_id)
            if any(not value.strip() for value in (args.case_id, args.failure, args.proposal)):
                raise ValueError("Lesson id, failure, and proposal must be nonblank.")
            target = path.parent / "lessons.jsonl"
            protected = {path, *((path.parent / item["path"]).resolve() for item in model["evidence"])}
            if target.is_symlink() or target.resolve() in protected:
                raise ValueError("Lessons must use a dedicated project-local file, not a symlink or evidence path.")
            previous = target.read_bytes() if target.exists() else None
            if previous is not None:
                records = [decode_json(line) for line in previous.decode("utf-8").splitlines() if line.strip()]
                if any(item["id"] == args.case_id for item in records):
                    raise ValueError("Lesson id already exists; preserve the original proposal.")
            record = {
                "id": args.case_id,
                "basis": fingerprint(model),
                "recorded_at": now(),
                "failure": args.failure,
                "proposal": args.proposal,
                "evidence_ids": args.evidence_id,
                "status": "proposed",
            }
            data = json.dumps(record, ensure_ascii=False).encode("utf-8") + b"\n"
            atomic_write(target, (previous or b"") + data, expected=previous)
        return {"lesson": record, "notice": "Proposal recorded; no plugin changes applied."}, 0
    result = audit(model, path.parent)
    if args.command == "report":
        content = render_report(model, result)
        return content, 0
    if args.command == "frontier":
        return {"basis": result["basis"], "frontier": result["frontier"], "issues": result["issues"]}, 0 if result[
            "recorded_checks_satisfied"
        ] else 1
    return result, 0 if result["recorded_checks_satisfied"] else 1


if __name__ == "__main__":
    sys.exit(main())
