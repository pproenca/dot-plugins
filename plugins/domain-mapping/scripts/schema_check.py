"""Pure structural and reference validation for domain-map JSON values."""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import PurePosixPath
from typing import Any

SCHEMA_VERSION = 1
TOP_LEVEL_KEYS = {
    "schema_version",
    "scope",
    "concepts",
    "relations",
    "claims",
    "evidence",
    "inventory",
    "scenarios",
    "runs",
    "reviews",
}
ARRAY_KEYS = (
    "concepts",
    "relations",
    "claims",
    "evidence",
    "inventory",
    "scenarios",
    "runs",
    "reviews",
)
PERSPECTIVES = {"observed", "intended"}
CLAIM_PERSPECTIVES = PERSPECTIVES | {"proposed"}
CLAIM_STATUSES = {"hypothesis", "supported", "contradicted", "not_applicable"}
RELATION_TYPES = {
    "initiates",
    "handles",
    "produces",
    "triggers",
    "informs",
    "governs",
    "transitions",
    "references",
    "belongs_to",
    "crosses",
    "terminates",
    "follows",
}
EVIDENCE_KINDS = {
    "source",
    "observation",
    "documentation",
    "data",
    "verification",
    "review",
}
RUN_RESULTS = {"passed", "failed", "blocked"}
REVIEW_KINDS = {"walkthrough", "blind_inventory", "challenge"}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:/")


def decode_json(raw):
    """Parse imported records without silently discarding duplicate keys or invalid numbers."""

    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result

    def invalid_number(value):
        raise ValueError(f"Non-JSON numeric value: {value}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_number)


def validate(model: Any, obligations: dict[str, list[str]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(model, dict):
        return ["model must be a JSON object"]

    missing = TOP_LEVEL_KEYS - set(model)
    unknown = set(model) - TOP_LEVEL_KEYS
    for key in sorted(missing, key=str):
        errors.append(f"missing top-level field: {key}")
    for key in sorted(unknown, key=str):
        errors.append(f"unknown top-level field: {key}")
    if type(model.get("schema_version")) is not int or model.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")

    scope = model.get("scope")
    if not isinstance(scope, dict):
        errors.append("scope must be an object")
    else:
        for field in ("id", "revision", "system", "system_version", "perspective", "description"):
            _require_nonblank(scope, field, "scope", errors)
        if not _member(scope.get("perspective"), PERSPECTIVES):
            errors.append("scope.perspective must be observed or intended")
        _require_string_list(scope, "conditions", "scope", errors)
        _require_string_list(scope, "exclusions", "scope", errors)

    records: dict[str, list[dict[str, Any]]] = {}
    ids: dict[str, str] = {}
    for collection in ARRAY_KEYS:
        value = model.get(collection)
        if not isinstance(value, list):
            errors.append(f"{collection} must be an array")
            records[collection] = []
            continue
        records[collection] = [item for item in value if isinstance(item, dict)]
        for index, item in enumerate(value):
            where = f"{collection}[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{where} must be an object")
                continue
            record_id = item.get("id")
            if not _nonblank(record_id):
                errors.append(f"{where}.id must be a nonblank string")
            elif record_id in ids:
                errors.append(f"duplicate global id {record_id!r} in {where} and {ids[record_id]}")
            else:
                ids[record_id] = where

    concept_ids = _id_set(records["concepts"])
    claim_ids = _id_set(records["claims"])
    evidence_ids = _id_set(records["evidence"])
    scenario_ids = _id_set(records["scenarios"])

    for index, concept in enumerate(records["concepts"]):
        where = f"concepts[{index}]"
        for field in ("id", "kind", "name", "context"):
            _require_nonblank(concept, field, where, errors)
        if obligations and not _member(concept.get("kind"), set(obligations)):
            errors.append(f"{where}.kind is not defined in obligations.json")

    for index, relation in enumerate(records["relations"]):
        where = f"relations[{index}]"
        _require_nonblank(relation, "id", where, errors)
        _require_ref(relation, "source", concept_ids, where, "concept", errors)
        _require_ref(relation, "target", concept_ids, where, "concept", errors)
        if not _member(relation.get("type"), RELATION_TYPES):
            errors.append(f"{where}.type is invalid")
        _require_ref_list(relation, "claim_ids", claim_ids, where, "claim", errors)

    for index, claim in enumerate(records["claims"]):
        where = f"claims[{index}]"
        for field in ("id", "aspect", "statement"):
            _require_nonblank(claim, field, where, errors)
        _require_ref(claim, "concept", concept_ids, where, "concept", errors)
        if not _member(claim.get("perspective"), CLAIM_PERSPECTIVES):
            errors.append(f"{where}.perspective is invalid")
        if not _member(claim.get("status"), CLAIM_STATUSES):
            errors.append(f"{where}.status is invalid")
        _require_ref_list(claim, "evidence_ids", evidence_ids, where, "evidence", errors)
        _require_ref_list(claim, "depends_on", claim_ids, where, "claim", errors)
        if claim.get("status") == "not_applicable" and not claim.get("evidence_ids"):
            errors.append(f"{where} is not_applicable but has no evidence")

    for index, evidence in enumerate(records["evidence"]):
        where = f"evidence[{index}]"
        for field in ("id", "path", "lineage", "source", "locator", "captured_at"):
            _require_nonblank(evidence, field, where, errors)
        if not _member(evidence.get("kind"), EVIDENCE_KINDS):
            errors.append(f"{where}.kind is invalid")
        if not isinstance(evidence.get("sha256"), str) or not SHA256_RE.fullmatch(evidence["sha256"]):
            errors.append(f"{where}.sha256 must be a lowercase 64-character hex digest")
        path_value = evidence.get("path")
        if isinstance(path_value, str) and not safe_relative_posix(path_value):
            errors.append(f"{where}.path must be a relative POSIX path beneath the model directory")
        if _nonblank(evidence.get("captured_at")) and not timezone_timestamp(evidence["captured_at"]):
            errors.append(f"{where}.captured_at must be an ISO timestamp with a timezone")

    for index, item in enumerate(records["inventory"]):
        where = f"inventory[{index}]"
        for field in ("id", "kind", "description"):
            _require_nonblank(item, field, where, errors)
        if not _member(item.get("disposition"), {"mapped", "unresolved", "excluded"}):
            errors.append(f"{where}.disposition is invalid")
        _require_ref_list(item, "concept_ids", concept_ids, where, "concept", errors)
        _require_ref_list(item, "evidence_ids", evidence_ids, where, "evidence", errors)
        if not isinstance(item.get("rationale"), str):
            errors.append(f"{where}.rationale must be a string")
        if item.get("disposition") == "excluded" and not _nonblank(item.get("rationale")):
            errors.append(f"{where}.rationale must explain an exclusion")

    for index, scenario in enumerate(records["scenarios"]):
        where = f"scenarios[{index}]"
        for field in ("id", "name", "given", "when", "then"):
            _require_nonblank(scenario, field, where, errors)
        _require_ref_list(scenario, "claim_ids", claim_ids, where, "claim", errors, nonempty=True)
        _require_ref_list(
            scenario,
            "oracle_evidence_ids",
            evidence_ids,
            where,
            "evidence",
            errors,
            nonempty=True,
        )

    evidence_by_id = {item.get("id"): item for item in records["evidence"] if _nonblank(item.get("id"))}
    for index, run in enumerate(records["runs"]):
        where = f"runs[{index}]"
        _require_nonblank(run, "id", where, errors)
        _require_ref(run, "scenario_id", scenario_ids, where, "scenario", errors)
        if not _member(run.get("result"), RUN_RESULTS):
            errors.append(f"{where}.result is invalid")
        _require_sha(run, "basis", where, errors)
        _require_ref_list(run, "evidence_ids", evidence_ids, where, "evidence", errors, nonempty=True)
        _require_nonblank(run, "recorded_at", where, errors)
        if _nonblank(run.get("recorded_at")) and not timezone_timestamp(run["recorded_at"]):
            errors.append(f"{where}.recorded_at must be an ISO timestamp with a timezone")
        _require_evidence_kind(run, evidence_by_id, "verification", where, errors)

    for index, review in enumerate(records["reviews"]):
        where = f"reviews[{index}]"
        _require_nonblank(review, "id", where, errors)
        if not _member(review.get("kind"), REVIEW_KINDS):
            errors.append(f"{where}.kind is invalid")
        if not _member(review.get("result"), RUN_RESULTS):
            errors.append(f"{where}.result is invalid")
        _require_sha(review, "basis", where, errors)
        _require_ref_list(review, "evidence_ids", evidence_ids, where, "evidence", errors, nonempty=True)
        _require_nonblank(review, "recorded_at", where, errors)
        if _nonblank(review.get("recorded_at")) and not timezone_timestamp(review["recorded_at"]):
            errors.append(f"{where}.recorded_at must be an ISO timestamp with a timezone")
        _require_evidence_kind(review, evidence_by_id, "review", where, errors)
    return errors


def safe_relative_posix(value: str) -> bool:
    if not value or "\\" in value or WINDOWS_DRIVE_RE.match(value):
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and value != "."


def timezone_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _member(value: Any, allowed: set[str]) -> bool:
    return isinstance(value, str) and value in allowed


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _id_set(records: list[dict[str, Any]]) -> set[str]:
    return {item["id"] for item in records if _nonblank(item.get("id"))}


def _require_nonblank(record: dict[str, Any], field: str, where: str, errors: list[str]) -> None:
    if not _nonblank(record.get(field)):
        errors.append(f"{where}.{field} must be a nonblank string")


def _require_string_list(record: dict[str, Any], field: str, where: str, errors: list[str]) -> None:
    value = record.get(field)
    if not isinstance(value, list) or any(not _nonblank(item) for item in value):
        errors.append(f"{where}.{field} must be an array of nonblank strings")


def _require_ref(
    record: dict[str, Any], field: str, allowed: set[str], where: str, kind: str, errors: list[str]
) -> None:
    value = record.get(field)
    if not _nonblank(value):
        errors.append(f"{where}.{field} must be a nonblank {kind} id")
    elif value not in allowed:
        errors.append(f"{where}.{field} references unknown {kind} {value!r}")


def _require_ref_list(
    record: dict[str, Any],
    field: str,
    allowed: set[str],
    where: str,
    kind: str,
    errors: list[str],
    *,
    nonempty: bool = False,
) -> None:
    value = record.get(field)
    if not isinstance(value, list) or any(not _nonblank(item) for item in value):
        errors.append(f"{where}.{field} must be an array of {kind} ids")
        return
    if nonempty and not value:
        errors.append(f"{where}.{field} must not be empty")
    if len(set(value)) != len(value):
        errors.append(f"{where}.{field} must not contain duplicates")
    for ref in value:
        if ref not in allowed:
            errors.append(f"{where}.{field} references unknown {kind} {ref!r}")


def _require_sha(record: dict[str, Any], field: str, where: str, errors: list[str]) -> None:
    value = record.get(field)
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        errors.append(f"{where}.{field} must be a lowercase 64-character hex digest")


def _require_evidence_kind(
    record: dict[str, Any], evidence: dict[str, dict[str, Any]], kind: str, where: str, errors: list[str]
) -> None:
    refs = record.get("evidence_ids")
    if not isinstance(refs, list):
        return
    for ref in refs:
        if not isinstance(ref, str):
            continue
        item = evidence.get(ref)
        if item is not None and item.get("kind") != kind:
            errors.append(f"{where}.evidence_ids must reference only {kind} evidence")
