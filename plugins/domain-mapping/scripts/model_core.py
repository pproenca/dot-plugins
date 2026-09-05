"""Validation, fingerprinting, and conservative closure checks for domain maps."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from schema_check import ARRAY_KEYS, REVIEW_KINDS, decode_json, safe_relative_posix, timezone_timestamp

SCHEMA_VERSION = 1
SORTED_STRING_LIST_KEYS = {
    "conditions",
    "exclusions",
    "claim_ids",
    "evidence_ids",
    "depends_on",
    "concept_ids",
    "oracle_evidence_ids",
}
DISCLAIMER = (
    "This audit reports recorded, scope-specific checks. It does not prove universal "
    "completeness, domain truth, participant expertise, or behavior outside the declared scope."
)


def load_obligations() -> dict[str, list[str]]:
    """Load the versioned concept-kind obligation table shipped with the plugin."""
    path = Path(__file__).with_name("obligations.json")
    try:
        raw = decode_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load obligations from {path}: {exc}") from exc
    if not isinstance(raw, dict) or not raw:
        raise ValueError("obligations.json must contain a non-empty object")
    obligations: dict[str, list[str]] = {}
    for kind, aspects in raw.items():
        if not _nonblank(kind) or not isinstance(aspects, list) or not aspects:
            raise ValueError("each obligation kind must have a non-empty aspect list")
        if any(not _nonblank(aspect) for aspect in aspects):
            raise ValueError(f"obligation aspects for {kind!r} must be nonblank strings")
        if len(set(aspects)) != len(aspects):
            raise ValueError(f"obligation aspects for {kind!r} must be unique")
        obligations[kind] = list(aspects)
    return obligations


def validate(model: Any) -> list[str]:
    """Return all structural errors that can be found without touching evidence files."""
    try:
        obligations = load_obligations()
    except ValueError as exc:
        return [str(exc)]
    from schema_check import validate as validate_schema

    return validate_schema(model, obligations)


def fingerprint(model: Any) -> str:
    """Return the stable basis used to invalidate recorded runs and reviews."""
    if isinstance(model, dict):
        payload = {key: value for key, value in model.items() if key not in {"runs", "reviews"}}
        referenced = _referenced_evidence_ids(model)
        evidence = payload.get("evidence")
        if isinstance(evidence, list):
            payload["evidence"] = [
                item
                for item in evidence
                if not isinstance(item, dict) or (isinstance(item.get("id"), str) and item["id"] in referenced)
            ]
    else:
        payload = model
    try:
        obligations: Any = load_obligations()
    except ValueError as exc:
        obligations = {"load_error": str(exc)}
    plugin_root = Path(__file__).resolve().parent.parent
    method_files = [
        plugin_root / ".codex-plugin" / "plugin.json",
        *sorted((plugin_root / "scripts").glob("*.py")),
        *sorted((plugin_root / "skills").rglob("*.md")),
    ]
    method = {str(path.relative_to(plugin_root).as_posix()): _file_sha256(path) for path in method_files}
    canonical = _normalise({"model": payload, "obligations": obligations, "method": method})
    encoded = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def audit(model: Any, root: Path, *, as_of: datetime | None = None) -> dict[str, Any]:
    """Audit one declared scope without claiming universal truth or completeness."""
    structural_errors = validate(model)
    basis = fingerprint(model)
    issues: list[dict[str, str]] = []
    frontier: list[dict[str, str]] = []

    def issue(code: str, subject: str, message: str) -> None:
        candidate = {"code": code, "subject": subject, "message": message}
        if candidate not in issues:
            issues.append(candidate)

    def gap(gap_id: str, subject: str, aspect: str, reason: str) -> None:
        candidate = {"id": gap_id, "subject": subject, "aspect": aspect, "reason": reason}
        if not any(item["id"] == gap_id for item in frontier):
            frontier.append(candidate)

    if not isinstance(model, dict):
        issue("invalid_model", "$", "The model is not structurally auditable.")
        return _audit_result(basis, structural_errors, issues, frontier, {})

    if structural_errors:
        issue("structural_errors", "$", "Structural errors prevent a satisfied audit.")
        safe_metrics = {
            "concepts": len(model.get("concepts", [])) if isinstance(model.get("concepts"), list) else 0,
            "inventory_total": len(model.get("inventory", [])) if isinstance(model.get("inventory"), list) else 0,
            "scenarios_total": len(model.get("scenarios", [])) if isinstance(model.get("scenarios"), list) else 0,
        }
        return _audit_result(basis, structural_errors, issues, frontier, safe_metrics)

    collections = {
        key: [item for item in model.get(key, []) if isinstance(item, dict)] if isinstance(model.get(key), list) else []
        for key in ARRAY_KEYS
    }
    concepts = collections["concepts"]
    claims = collections["claims"]
    evidence = collections["evidence"]
    inventory = collections["inventory"]
    scenarios = collections["scenarios"]
    runs = collections["runs"]
    reviews = collections["reviews"]
    scope = model.get("scope") if isinstance(model.get("scope"), dict) else {}
    scope_perspective = scope.get("perspective")

    checked_at = as_of if as_of is not None else datetime.now(timezone.utc)
    if checked_at.tzinfo is None or checked_at.utcoffset() is None:
        raise ValueError("as_of must have an explicit timezone")
    future_ids = set()
    for record in [*runs, *reviews]:
        recorded = datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00"))
        if recorded > checked_at + timedelta(minutes=5):
            future_ids.add(record["id"])
            issue(
                "future_result",
                record["id"],
                "Result timestamp is more than five minutes in the future; reconcile the clock or record.",
            )
            gap(
                f"result:{record['id']}",
                record["id"],
                "timestamp",
                "Reconcile the future-dated result without discarding failures.",
            )
    future_scenarios = {record["scenario_id"] for record in runs if record["id"] in future_ids}
    runs = [record for record in runs if record["id"] not in future_ids]
    reviews = [record for record in reviews if record["id"] not in future_ids]

    if not concepts:
        issue("no_concepts", "concepts", "The model contains no concepts.")
        gap("model:concepts", "model", "concepts", "Discover and record at least one in-scope concept.")
    if not inventory:
        issue("no_inventory", "inventory", "The discovery inventory is empty.")
        gap("model:inventory", "model", "inventory", "Create an independent discovery inventory.")
    if not scenarios:
        issue("no_scenarios", "scenarios", "The model contains no behavioral scenarios.")
        gap("model:scenarios", "model", "scenarios", "Record scenarios with independent oracles.")
    if scope.get("system_version") == "unresolved":
        gap(
            "scope:system_version",
            str(scope.get("id", "scope")),
            "system_version",
            "Resolve the mapped system version.",
        )

    evidence_by_id = {item.get("id"): item for item in evidence if _nonblank(item.get("id"))}
    current_evidence: set[str] = set()
    evidence_failures: dict[str, str] = {}
    root_path = Path(root).resolve(strict=False)
    for evidence_id, item in evidence_by_id.items():
        path_value = item.get("path")
        if not isinstance(path_value, str) or not safe_relative_posix(path_value):
            evidence_failures[evidence_id] = "invalid path"
            continue
        candidate = root_path.joinpath(*PurePosixPath(path_value).parts)
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(root_path)
        except (OSError, RuntimeError, ValueError):
            evidence_failures[evidence_id] = "path escapes the model directory"
            issue("evidence_path_escape", evidence_id, f"Evidence path {path_value!r} escapes the model directory.")
            continue
        if not resolved.is_file():
            evidence_failures[evidence_id] = "file is missing"
            issue("evidence_missing", evidence_id, f"Evidence file {path_value!r} is missing.")
            continue
        try:
            actual = _file_sha256(resolved)
        except OSError as exc:
            evidence_failures[evidence_id] = "file cannot be read"
            issue("evidence_unreadable", evidence_id, f"Evidence file {path_value!r} cannot be read: {exc}.")
            continue
        if actual != item.get("sha256"):
            evidence_failures[evidence_id] = "content hash changed"
            issue(
                "evidence_hash_mismatch",
                evidence_id,
                f"Evidence file {path_value!r} no longer matches its recorded hash.",
            )
            continue
        current_evidence.add(evidence_id)

    claims_by_id = {item.get("id"): item for item in claims if _nonblank(item.get("id"))}
    base_failures: dict[str, set[str]] = {}
    for claim_id, claim in claims_by_id.items():
        failures: set[str] = set()
        if claim.get("perspective") != scope_perspective:
            failures.add(f"perspective {claim.get('perspective')!r} does not match scope")
        if claim.get("status") not in {"supported", "not_applicable"}:
            failures.add(f"status is {claim.get('status')!r}")
        evidence_ids = claim.get("evidence_ids") if isinstance(claim.get("evidence_ids"), list) else []
        if not evidence_ids:
            failures.add("claim has no evidence")
        for evidence_id in evidence_ids:
            if evidence_id not in current_evidence:
                failures.add(
                    f"evidence {evidence_id!r} is not current "
                    f"({evidence_failures.get(evidence_id, 'invalid reference')})"
                )
        base_failures[claim_id] = failures

    # Propagate root failures to a fixed point. This treats cycles as strongly
    # connected support groups: they close only when every member has independent,
    # current evidence and a matching status/perspective.
    failure_roots: dict[str, set[tuple[str, str]]] = {
        claim_id: {(claim_id, cause) for cause in failures} for claim_id, failures in base_failures.items()
    }
    changed = True
    while changed:
        changed = False
        for claim_id, claim in claims_by_id.items():
            dependencies = claim.get("depends_on") if isinstance(claim.get("depends_on"), list) else []
            propagated: set[tuple[str, str]] = set()
            for dependency in dependencies:
                if dependency in failure_roots:
                    propagated.update(failure_roots[dependency])
                elif dependency not in claims_by_id:
                    propagated.add((dependency, "dependency is missing"))
            if not propagated.issubset(failure_roots[claim_id]):
                failure_roots[claim_id].update(propagated)
                changed = True

    current_claims: set[str] = set()
    for claim_id in claims_by_id:
        roots = failure_roots[claim_id]
        if roots:
            claim = claims_by_id[claim_id]
            failures = [
                cause if root_id == claim_id else f"dependency {root_id!r}: {cause}" for root_id, cause in sorted(roots)
            ]
            issue("claim_not_current", claim_id, "; ".join(failures))
            gap(
                f"claim:{claim_id}:support",
                claim_id,
                str(claim.get("aspect", "support")),
                "Resolve the claim's evidence, status, perspective, and dependency failures.",
            )
        else:
            current_claims.add(claim_id)

    for relation in collections["relations"]:
        relation_id = str(relation.get("id", "relation"))
        relation_claims = relation.get("claim_ids") if isinstance(relation.get("claim_ids"), list) else []
        if not relation_claims:
            gap(
                f"relation:{relation_id}:support",
                relation_id,
                "support",
                "Support this pending relationship with an evidence-backed claim.",
            )
        elif not any(claim_id in current_claims for claim_id in relation_claims):
            issue("relation_not_current", relation_id, "No linked relation claim is current in this scope.")
            gap(
                f"relation:{relation_id}:support",
                relation_id,
                "support",
                "Resolve at least one linked relation claim.",
            )

    contradicted_aspects = {
        (str(claim.get("concept")), str(claim.get("aspect")))
        for claim in claims
        if claim.get("status") == "contradicted" and claim.get("perspective") == scope_perspective
    }
    for concept_id, aspect in sorted(contradicted_aspects):
        issue("aspect_contradicted", concept_id, f"Aspect {aspect!r} has a contradictory in-scope claim.")
        gap(
            f"{concept_id}:{aspect}",
            concept_id,
            aspect,
            "Resolve the explicit contradiction before treating this aspect as closed.",
        )

    try:
        obligations = load_obligations()
    except ValueError:
        obligations = {}
    obligations_total = 0
    obligations_supported = 0
    for concept in concepts:
        concept_id = concept.get("id")
        if not _nonblank(concept_id):
            continue
        for aspect in obligations.get(concept.get("kind"), []):
            obligations_total += 1
            matching = [
                claim
                for claim in claims
                if claim.get("concept") == concept_id
                and claim.get("aspect") == aspect
                and claim.get("perspective") == scope_perspective
            ]
            contradicted = [claim for claim in matching if claim.get("status") == "contradicted"]
            supported = [claim for claim in matching if claim.get("id") in current_claims]
            if supported and not contradicted:
                obligations_supported += 1
            else:
                reason = (
                    "A matching claim is explicitly contradicted."
                    if contradicted
                    else "No current supported or evidenced not-applicable claim closes this obligation."
                )
                gap(f"{concept_id}:{aspect}", concept_id, aspect, reason)
                if contradicted:
                    issue("aspect_contradicted", concept_id, f"Aspect {aspect!r} has a contradictory in-scope claim.")

    inventory_mapped = 0
    inventory_excluded = 0
    for item in inventory:
        item_id = str(item.get("id", "inventory"))
        disposition = item.get("disposition")
        item_evidence = item.get("evidence_ids") if isinstance(item.get("evidence_ids"), list) else []
        evidence_ok = bool(item_evidence) and all(ref in current_evidence for ref in item_evidence)
        if disposition == "mapped":
            concepts_ok = bool(item.get("concept_ids"))
            if evidence_ok and concepts_ok:
                inventory_mapped += 1
            else:
                issue("inventory_not_accounted", item_id, "Mapped inventory needs concepts and current evidence.")
                gap(
                    f"inventory:{item_id}",
                    item_id,
                    "disposition",
                    "Complete the mapped inventory evidence and concept links.",
                )
        elif disposition == "excluded":
            if evidence_ok and _nonblank(item.get("rationale")):
                inventory_excluded += 1
            else:
                issue("exclusion_not_supported", item_id, "Excluded inventory needs a rationale and current evidence.")
                gap(
                    f"inventory:{item_id}",
                    item_id,
                    "exclusion",
                    "Support the exclusion with a rationale and current evidence.",
                )
        else:
            gap(
                f"inventory:{item_id}",
                item_id,
                "disposition",
                "Resolve, map, or explicitly exclude this inventory item.",
            )

    scenario_claims: set[str] = set()
    scenarios_current_passed = 0
    for scenario in scenarios:
        scenario_id = str(scenario.get("id", "scenario"))
        linked_claims = scenario.get("claim_ids") if isinstance(scenario.get("claim_ids"), list) else []
        scenario_claims.update(ref for ref in linked_claims if isinstance(ref, str))
        oracles = scenario.get("oracle_evidence_ids") if isinstance(scenario.get("oracle_evidence_ids"), list) else []
        claims_ok = bool(linked_claims) and all(ref in current_claims for ref in linked_claims)
        oracle_ok = bool(oracles) and all(ref in current_evidence for ref in oracles)
        independent = _oracle_is_independent(linked_claims, oracles, claims_by_id, evidence_by_id)
        if not independent:
            issue(
                "non_independent_oracle",
                scenario_id,
                "Scenario oracle lineage overlaps evidence supporting its claims.",
            )
        latest, conflicting = _latest_records([run for run in runs if run.get("scenario_id") == scenario.get("id")])
        run_ok = False
        if scenario_id in future_scenarios:
            issue("ambiguous_run_order", scenario_id, "A future-dated record prevents establishing the latest result.")
        elif conflicting:
            issue("conflicting_latest_runs", scenario_id, "Latest runs at the same timestamp have conflicting results.")
        elif latest is None:
            issue("missing_run", scenario_id, "The scenario has no recorded run.")
        else:
            run_evidence = latest.get("evidence_ids") if isinstance(latest.get("evidence_ids"), list) else []
            oracle_hashes = {evidence_by_id[ref]["sha256"] for ref in oracles}
            result_hashes = {evidence_by_id[ref]["sha256"] for ref in run_evidence}
            if set(oracles) & set(run_evidence) or oracle_hashes & result_hashes:
                independent = False
                issue(
                    "circular_run_oracle",
                    scenario_id,
                    "The observed run artifact cannot also be its own expected-result oracle.",
                )
            run_evidence_ok = bool(run_evidence) and all(
                ref in current_evidence and evidence_by_id.get(ref, {}).get("kind") == "verification"
                for ref in run_evidence
            )
            run_ok = latest.get("basis") == basis and latest.get("result") == "passed" and run_evidence_ok
            if latest.get("basis") != basis:
                issue(
                    "stale_run",
                    scenario_id,
                    "The latest scenario run was recorded against a different model fingerprint.",
                )
            elif latest.get("result") != "passed":
                issue("scenario_not_passed", scenario_id, f"The latest scenario result is {latest.get('result')!r}.")
            elif not run_evidence_ok:
                issue("run_evidence_not_current", scenario_id, "The latest run lacks current verification evidence.")
        if claims_ok and oracle_ok and independent and run_ok:
            scenarios_current_passed += 1
        else:
            gap(
                f"scenario:{scenario_id}",
                scenario_id,
                "verification",
                "Record a current passing run with current independent evidence after resolving linked claims.",
            )

    for claim_id, claim in claims_by_id.items():
        if (
            claim.get("status") == "supported"
            and claim.get("perspective") == scope_perspective
            and claim_id not in scenario_claims
        ):
            gap(
                f"claim:{claim_id}:scenario",
                claim_id,
                "scenario",
                "Cover this supported in-scope claim with a behavioral scenario.",
            )

    for review_kind in sorted(REVIEW_KINDS):
        latest, conflicting = _latest_records([review for review in reviews if review.get("kind") == review_kind])
        if conflicting:
            issue(
                "conflicting_latest_reviews",
                review_kind,
                "Latest reviews at the same timestamp have conflicting results.",
            )
            gap(f"review:{review_kind}", review_kind, "review", "Resolve conflicting latest review records.")
            continue
        if latest is None:
            issue("missing_review", review_kind, f"A current {review_kind} review is required.")
            gap(f"review:{review_kind}", review_kind, "review", f"Record a {review_kind} review.")
            continue
        refs = latest.get("evidence_ids") if isinstance(latest.get("evidence_ids"), list) else []
        evidence_ok = bool(refs) and all(
            ref in current_evidence and evidence_by_id.get(ref, {}).get("kind") == "review" for ref in refs
        )
        if latest.get("basis") != basis:
            issue("stale_review", review_kind, f"The latest {review_kind} review uses a different model fingerprint.")
        elif latest.get("result") != "passed":
            issue("review_not_passed", review_kind, f"The latest {review_kind} result is {latest.get('result')!r}.")
        elif not evidence_ok:
            issue(
                "review_evidence_not_current",
                review_kind,
                f"The latest {review_kind} review lacks current review evidence.",
            )
        else:
            continue
        gap(
            f"review:{review_kind}",
            review_kind,
            "review",
            f"Record a current passing {review_kind} review with current evidence.",
        )

    metrics = {
        "concepts": len(concepts),
        "obligations_total": obligations_total,
        "obligations_supported": obligations_supported,
        "inventory_total": len(inventory),
        "inventory_mapped": inventory_mapped,
        "inventory_excluded": inventory_excluded,
        "scenarios_total": len(scenarios),
        "scenarios_current_passed": scenarios_current_passed,
    }
    return _audit_result(basis, structural_errors, issues, frontier, metrics)


def _audit_result(
    basis: str,
    structural_errors: list[str],
    issues: list[dict[str, str]],
    frontier: list[dict[str, str]],
    metrics: dict[str, int],
) -> dict[str, Any]:
    defaults = {
        "concepts": 0,
        "obligations_total": 0,
        "obligations_supported": 0,
        "inventory_total": 0,
        "inventory_mapped": 0,
        "inventory_excluded": 0,
        "scenarios_total": 0,
        "scenarios_current_passed": 0,
    }
    defaults.update(metrics)
    issues.sort(key=lambda item: (item["code"], item["subject"], item["message"]))
    frontier.sort(key=lambda item: (item["id"], item["subject"], item["aspect"]))
    return {
        "schema_version": SCHEMA_VERSION,
        "basis": basis,
        "structural_errors": structural_errors,
        "issues": issues,
        "frontier": frontier,
        "metrics": defaults,
        "recorded_checks_satisfied": not structural_errors and not issues and not frontier,
        "disclaimer": DISCLAIMER,
    }


def _nonblank(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _referenced_evidence_ids(model: dict[str, Any]) -> set[str]:
    referenced: set[str] = set()
    mappings = (
        ("claims", "evidence_ids"),
        ("inventory", "evidence_ids"),
        ("scenarios", "oracle_evidence_ids"),
    )
    for collection, field in mappings:
        records = model.get(collection)
        if not isinstance(records, list):
            continue
        for record in records:
            refs = record.get(field) if isinstance(record, dict) else None
            if isinstance(refs, list):
                referenced.update(ref for ref in refs if isinstance(ref, str))
    return referenced


def _normalise(value: Any, key: str | None = None) -> Any:
    if isinstance(value, dict):
        return {
            str(item_key): _normalise(item_value, str(item_key))
            for item_key, item_value in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        items = [_normalise(item) for item in value]
        if items and all(isinstance(item, dict) and isinstance(item.get("id"), str) for item in items):
            return sorted(items, key=lambda item: item["id"])
        if key in SORTED_STRING_LIST_KEYS and all(isinstance(item, str) for item in items):
            return sorted(items)
        return items
    return value


def _oracle_is_independent(
    claim_ids: list[Any],
    oracle_ids: list[Any],
    claims: dict[str, dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
) -> bool:
    support_ids: set[str] = set()
    pending = [claim_id for claim_id in claim_ids if isinstance(claim_id, str)]
    seen: set[str] = set()
    while pending:
        claim_id = pending.pop()
        if claim_id in seen:
            continue
        seen.add(claim_id)
        claim = claims.get(claim_id, {})
        refs = claim.get("evidence_ids")
        if isinstance(refs, list):
            support_ids.update(ref for ref in refs if isinstance(ref, str))
        dependencies = claim.get("depends_on")
        if isinstance(dependencies, list):
            pending.extend(ref for ref in dependencies if isinstance(ref, str))
    support_lineages = {evidence[ref].get("lineage") for ref in support_ids if ref in evidence}
    oracle_lineages = {evidence[ref].get("lineage") for ref in oracle_ids if ref in evidence}
    support_hashes = {evidence[ref].get("sha256") for ref in support_ids if ref in evidence}
    oracle_hashes = {evidence[ref].get("sha256") for ref in oracle_ids if ref in evidence}
    return not bool(support_lineages & oracle_lineages or support_hashes & oracle_hashes)


def _latest_records(records: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, bool]:
    valid = [
        record
        for record in records
        if _nonblank(record.get("recorded_at")) and timezone_timestamp(record["recorded_at"])
    ]
    if not valid:
        return None, False
    latest_time = max(datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00")) for record in valid)
    latest = [
        record
        for record in valid
        if datetime.fromisoformat(record["recorded_at"].replace("Z", "+00:00")) == latest_time
    ]
    outcomes = {(record.get("result"), record.get("basis")) for record in latest}
    conflicting = len(outcomes) > 1
    # Deterministic and pessimistic when duplicate stamps have the same outcome.
    rank = {"failed": 0, "blocked": 1, "passed": 2}
    selected = min(latest, key=lambda record: (rank.get(record.get("result"), -1), str(record.get("id", ""))))
    return selected, conflicting
