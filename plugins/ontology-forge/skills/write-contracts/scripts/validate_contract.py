#!/usr/bin/env python3
"""Validate data contracts against the vendored Open Data Contract Standard v3.1.0 schema.

ODCS v3.1.0 sets additionalProperties/unevaluatedProperties to false throughout, so a field
the standard does not define is an error rather than a tolerated extension. That strictness is
the point: it is what turns "written to ODCS" into something checkable.

Usage:
    validate_contract.py <file-or-directory> [...]
    validate_contract.py ontology/contracts --json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from difflib import get_close_matches
from pathlib import Path
from typing import Any

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SCHEMA = PLUGIN_ROOT / "vendor" / "odcs" / "odcs-json-schema-v3.1.0.json"
CONTRACT_GLOB = "*.odcs.yaml"
BOOTSTRAP_ENV = "ODCS_VALIDATOR_BOOTSTRAPPED"
REQUIREMENTS = ("jsonschema>=4.23", "pyyaml>=6")


def _bootstrap() -> None:
    """Re-run under `uv run --with` when the dependencies are not importable.

    Keeps the script usable on a bare interpreter without asking the user to manage a
    virtualenv. Guarded by an environment variable so a failed bootstrap cannot recurse.
    """
    if os.environ.get(BOOTSTRAP_ENV):
        sys.exit(
            "error: jsonschema and PyYAML are required but could not be installed.\n"
            "       Install them directly:  pip install %s" % " ".join(REQUIREMENTS)
        )
    uv = os.environ.get("UV", "uv")
    command = [uv, "run", "--quiet"]
    for requirement in REQUIREMENTS:
        command += ["--with", requirement]
    command += [str(Path(__file__).resolve()), *sys.argv[1:]]
    env = dict(os.environ, **{BOOTSTRAP_ENV: "1"})
    try:
        raise SystemExit(subprocess.call(command, env=env))
    except FileNotFoundError:
        sys.exit(
            "error: jsonschema and PyYAML are missing, and `uv` is not on PATH to install them.\n"
            "       Install them directly:  pip install %s" % " ".join(REQUIREMENTS)
        )


try:
    import yaml
    from jsonschema import Draft201909Validator
except ModuleNotFoundError:  # pragma: no cover - exercised by the bootstrap path
    _bootstrap()


def _contract_paths(targets: list[str]) -> list[Path]:
    paths: list[Path] = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            paths.extend(sorted(path.rglob(CONTRACT_GLOB)))
        else:
            paths.append(path)
    return paths


# Field names borrowed from other contract formats and warehouse DDL that authors reach for
# by habit. ODCS rejects every one of them, and the schema error alone does not say what to
# write instead. `nullable` is the dangerous one: it is not a rename of `required`, it is its
# inverse, so a mechanical substitution silently flips the meaning.
KNOWN_MISTAKES = {
    "nullable": "required (note the inversion: nullable: true means required: false)",
    "isnullable": "required (note the inversion: isNullable: true means required: false)",
    "type": "logicalType for the ODCS type, or physicalType for the source system's type",
    "datatype": "physicalType",
    "columns": "properties",
    "fields": "properties",
    "table": "a schema[] entry with name and physicalType: table",
    "dataset": "a schema[] entry",
    "owner": "team, or a roles[] entry",
    "owners": "team.members[]",
    "pii": "classification",
    "sensitivity": "classification",
    "primary_key": "primaryKey",
    "foreign_key": "a relationships[] entry with type: foreignKey",
    "checks": "quality[]",
    "tests": "quality[]",
    "sla": "slaProperties[]",
    "freshness": "a slaProperties[] entry with property: frequency",
    "deprecated": "status: deprecated",
}
UNEXPECTED = re.compile(r"'([^']+)' was unexpected")


def _allowed_here(schema: dict[str, Any], instance: dict[str, Any]) -> list[str]:
    """Find the definition the offending object was meant to satisfy.

    `unevaluatedProperties` fires at a composition boundary, where the error's own subschema
    carries no property list. Score every definition by how many of the object's keys it does
    define; the best match is the shape the author was aiming at.
    """
    candidates = [schema, *schema.get("$defs", {}).values()]
    best: list[str] = []
    best_score = 0
    for candidate in candidates:
        properties = candidate.get("properties")
        if not isinstance(properties, dict):
            continue
        score = len(set(instance) & set(properties))
        if score > best_score:
            best, best_score = sorted(properties), score
    return best


def _suggest(unexpected: str, allowed: list[str]) -> str:
    """Offer the field the author probably meant, from the known mistakes or by similarity."""
    known = KNOWN_MISTAKES.get(unexpected.lower())
    if known:
        return " — use %s" % known
    close = get_close_matches(unexpected, allowed, n=1, cutoff=0.6)
    if close:
        return " (did you mean %r?)" % close[0]
    if allowed:
        return " — anything outside the standard belongs in customProperties"
    return ""


def _location(error: Any) -> str:
    parts = [str(part) for part in error.absolute_path]
    return ".".join(parts) if parts else "<root>"


def _describe(error: Any, schema: dict[str, Any]) -> str:
    """Render one schema error, adding a suggestion for the strictness failures."""
    message = error.message
    if error.validator not in ("additionalProperties", "unevaluatedProperties"):
        return message
    if not isinstance(error.instance, dict):
        return message
    match = UNEXPECTED.search(message)
    if not match:
        return message
    return "%s%s" % (message, _suggest(match.group(1), _allowed_here(schema, error.instance)))


def _load(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        text = path.read_text()
    except OSError as exc:
        return None, "cannot read: %s" % exc
    try:
        document = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        return None, "not valid YAML: %s" % exc
    if not isinstance(document, dict):
        return None, "expected a YAML mapping at the top level"
    return document, None


def validate_file(path: Path, validator: Draft201909Validator, schema: dict[str, Any]) -> list[dict[str, str]]:
    document, failure = _load(path)
    if failure is not None:
        return [{"location": "<file>", "message": failure}]

    # The schema composes subschemas, so one mistake can surface through several branches.
    # Report each distinct (location, message) once; duplicates read as separate problems.
    seen: set[tuple[str, str]] = set()
    findings: list[dict[str, str]] = []
    for error in sorted(validator.iter_errors(document), key=lambda e: list(map(str, e.absolute_path))):
        finding = (_location(error), _describe(error, schema))
        if finding in seen:
            continue
        seen.add(finding)
        findings.append({"location": finding[0], "message": finding[1]})
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("targets", nargs="+", help="contract files, or directories searched for %s" % CONTRACT_GLOB)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA, help="override the vendored ODCS schema")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    args = parser.parse_args()

    if not args.schema.is_file():
        return _fail(parser, "schema not found: %s" % args.schema)

    schema = json.loads(args.schema.read_text())
    validator = Draft201909Validator(schema)
    paths = _contract_paths(args.targets)
    if not paths:
        return _fail(parser, "no %s files found under: %s" % (CONTRACT_GLOB, ", ".join(args.targets)))

    results = {str(path): validate_file(path, validator, schema) for path in paths}
    total = sum(len(errors) for errors in results.values())

    if args.as_json:
        print(json.dumps({"schema": args.schema.name, "contracts": results, "errorCount": total}, indent=2))
        return 1 if total else 0

    for path, errors in results.items():
        if not errors:
            print("PASS  %s" % path)
            continue
        print("FAIL  %s" % path)
        for error in errors:
            print("  ✗ %s: %s" % (error["location"], error["message"]))

    conformant = len(paths) - sum(1 for errors in results.values() if errors)
    print(
        "\n%d/%d conformant with ODCS v3.1.0%s"
        % (conformant, len(paths), "" if not total else " — %d error(s)" % total)
    )
    return 1 if total else 0


def _fail(parser: argparse.ArgumentParser, message: str) -> int:
    parser.exit(status=2, message="error: %s\n" % message)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
