#!/usr/bin/env python3
"""Produce a byte and instruction audit of the Cursor-to-Codex pstack translation."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RISK_PATTERNS = {
    "workflow structure": re.compile(r"\b(phase|step|playbook|output|outcome|deliverable)\b", re.I),
    "requirement strength": re.compile(r"\b(must|never|required|only|blocked|inconclusive|do not)\b", re.I),
    "delegation": re.compile(r"\b(agent|subagent|delegate|spawn|model|parallel|wait|interrupt)\b", re.I),
    "side effects": re.compile(r"\b(write|edit|delete|commit|push|merge|deploy|ship|branch|worktree)\b", re.I),
    "verification": re.compile(r"\b(verify|verification|test|proof|evidence|pass|fail)\b", re.I),
}


@dataclass(frozen=True)
class FileAudit:
    source_path: str | None
    target_path: str
    classification: str
    source_sha: str | None
    target_sha: str
    source_bytes: int | None
    target_bytes: int
    source_lines: int | None
    target_lines: int
    binary: bool
    risk_categories: tuple[str, ...]
    instruction_diff: tuple[str, ...]
    unified_diff: tuple[str, ...]
    target_text: tuple[str, ...]


def load_parity_module(repo_root: Path):
    path = repo_root / "scripts" / "check_pstack_cursor_parity.py"
    spec = importlib.util.spec_from_file_location("pstack_parity", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_parity_checker(repo_root: Path, upstream_root: Path, codex_root: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            repo_root / "scripts/check_pstack_cursor_parity.py",
            upstream_root,
            "--codex-pstack",
            codex_root,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise ValueError("cannot audit an invalid tree:\n" + result.stdout + result.stderr)


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def text_lines(payload: bytes) -> list[str]:
    return payload.decode("utf-8", errors="replace").splitlines()


def is_binary(payload: bytes) -> bool:
    return b"\0" in payload


def prose_lines(lines: list[str]) -> list[str]:
    result: list[str] = []
    in_fence = False
    in_frontmatter = bool(lines and lines[0].strip() == "---")
    for index, line in enumerate(lines):
        stripped = line.strip()
        if index and in_frontmatter and stripped == "---":
            in_frontmatter = False
            continue
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_frontmatter or in_fence or not stripped or stripped.startswith("#"):
            continue
        result.append(stripped)
    return result


def changed_instructions(source: list[str], target: list[str]) -> tuple[str, ...]:
    source_prose = prose_lines(source)
    target_prose = prose_lines(target)
    return tuple(
        line
        for line in difflib.ndiff(source_prose, target_prose)
        if line.startswith(("- ", "+ "))
    )


def risk_categories(lines: tuple[str, ...]) -> tuple[str, ...]:
    changed = "\n".join(lines)
    return tuple(name for name, pattern in RISK_PATTERNS.items() if pattern.search(changed))


def audit_pair(source_path: str, source: Path, target_path: str, target: Path) -> FileAudit:
    source_payload = source.read_bytes()
    target_payload = target.read_bytes()
    binary = is_binary(source_payload) or is_binary(target_payload)
    source_lines = [] if binary else text_lines(source_payload)
    target_lines = [] if binary else text_lines(target_payload)
    exact = source_payload == target_payload
    instruction_diff = () if exact or binary else changed_instructions(source_lines, target_lines)
    unified_diff = () if exact or binary else tuple(
        difflib.unified_diff(
            source_lines,
            target_lines,
            fromfile=source_path,
            tofile=target_path,
            lineterm="",
        )
    )
    return FileAudit(
        source_path=source_path,
        target_path=target_path,
        classification="exact" if exact else "translated",
        source_sha=sha256(source_payload),
        target_sha=sha256(target_payload),
        source_bytes=len(source_payload),
        target_bytes=len(target_payload),
        source_lines=len(source_lines),
        target_lines=len(target_lines),
        binary=binary,
        risk_categories=risk_categories(instruction_diff),
        instruction_diff=instruction_diff,
        unified_diff=unified_diff,
        target_text=(),
    )


def audit_codex_only(target_path: str, target: Path) -> FileAudit:
    payload = target.read_bytes()
    lines = text_lines(payload)
    return FileAudit(
        source_path=None,
        target_path=target_path,
        classification="Codex-only",
        source_sha=None,
        target_sha=sha256(payload),
        source_bytes=None,
        target_bytes=len(payload),
        source_lines=None,
        target_lines=len(lines),
        binary=is_binary(payload),
        risk_categories=risk_categories(tuple(lines)),
        instruction_diff=(),
        unified_diff=(),
        target_text=tuple(lines),
    )


def split_skill_diff(upstream_root: Path, codex_root: Path) -> tuple[str, ...]:
    source_path = upstream_root / "skills/poteto-mode/SKILL.md"
    loader_path = codex_root / "skills/poteto-mode/SKILL.md"
    body_path = codex_root / "skills/poteto-mode/references/full-mode.md"
    target_lines = [*text_lines(loader_path.read_bytes()), "", *text_lines(body_path.read_bytes())]
    return tuple(
        difflib.unified_diff(
            text_lines(source_path.read_bytes()),
            target_lines,
            fromfile="skills/poteto-mode/SKILL.md",
            tofile="skills/poteto-mode/SKILL.md + skills/poteto-mode/references/full-mode.md",
            lineterm="",
        )
    )


def validate_inputs(parity, upstream: dict[str, Path], local: dict[str, Path]) -> None:
    failures: list[str] = []
    translated_paths: set[str] = set()
    for source_path, source in upstream.items():
        target_path = parity.source_to_codex(source_path)
        target = local.get(target_path)
        if target is None:
            failures.append(f"missing upstream file: {source_path} -> {target_path}")
            continue
        if bool(source.stat().st_mode & 0o111) != bool(target.stat().st_mode & 0o111):
            failures.append(f"executable mode differs: {source_path} -> {target_path}")
        if source.read_bytes() != target.read_bytes():
            if parity.can_translate(source_path):
                translated_paths.add(source_path)
            else:
                failures.append(f"unlisted byte difference: {source_path} -> {target_path}")

    failures.extend(parity.mapping_collision_failures(set(upstream)))
    mapped = {parity.source_to_codex(path) for path in upstream}
    failures.extend(parity.codex_only_receipt_failures(local, set(local) - mapped))
    failures.extend(parity.translation_receipt_failures(upstream, local, translated_paths))

    if failures:
        raise ValueError("cannot audit an unvalidated tree:\n" + "\n".join(failures))


def render(
    audits: list[FileAudit],
    upstream_root: Path,
    codex_root: Path,
    poteto_split_diff: tuple[str, ...],
) -> str:
    exact = sum(audit.classification == "exact" for audit in audits)
    translated = sum(audit.classification == "translated" for audit in audits)
    codex_only = sum(audit.classification == "Codex-only" for audit in audits)
    lines = [
        "# Pstack Cursor-to-Codex audit",
        "",
        f"Cursor source: `{upstream_root}`",
        f"Codex target: `{codex_root}`",
        "",
        f"Files: {len(audits)}. Exact: {exact}. Translated: {translated}. Codex-only: {codex_only}.",
        "",
        "Risk labels are search aids, not verdicts. They mark changed instructions that contain workflow, authority, "
        "delegation, side-effect, or verification terms.",
        "",
        "## File inventory",
        "",
        "| Source | Target | Class | Source bytes | Target bytes | Source SHA-256 | Target SHA-256 | Risk labels |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for audit in audits:
        source_path = audit.source_path or "none"
        source_bytes = "none" if audit.source_bytes is None else str(audit.source_bytes)
        source_sha = audit.source_sha or "none"
        labels = ", ".join(audit.risk_categories) or "none"
        lines.append(
            f"| `{source_path}` | `{audit.target_path}` | {audit.classification} | {source_bytes} | "
            f"{audit.target_bytes} | `{source_sha}` | `{audit.target_sha}` | {labels} |"
        )

    lines.extend(["", "## Changed instructions", ""])
    for audit in audits:
        if audit.classification != "translated":
            continue
        lines.extend([f"### `{audit.source_path}` to `{audit.target_path}`", ""])
        if audit.binary:
            lines.extend(["Binary bytes differ. Use the SHA-256 values and byte counts in the inventory.", ""])
        elif audit.instruction_diff:
            lines.extend(["````````diff", *audit.instruction_diff, "````````", ""])
        else:
            lines.extend(["No prose instruction changed outside frontmatter, headings, or code fences.", ""])

    lines.extend(
        [
            "## Split skill coverage",
            "",
            "The Codex loader requires `skills/poteto-mode/references/full-mode.md`. This diff compares the original "
            "single file with the two target files in their instructed read order.",
            "",
            "````````diff",
            *poteto_split_diff,
            "````````",
            "",
            "## Codex-only file contents",
            "",
        ]
    )
    for audit in audits:
        if audit.classification != "Codex-only":
            continue
        lines.extend([f"### `{audit.target_path}`", ""])
        if audit.binary:
            lines.extend(["Binary file. Use the SHA-256 and byte count in the inventory.", ""])
        else:
            lines.extend(["````````", *audit.target_text, "````````", ""])

    lines.extend(["## Full line diffs", ""])
    for audit in audits:
        if audit.classification != "translated":
            continue
        if audit.binary:
            lines.extend(
                [
                    f"### `{audit.source_path}` to `{audit.target_path}`",
                    "",
                    "Binary bytes differ. Use the SHA-256 values and byte counts in the inventory.",
                    "",
                ]
            )
            continue
        lines.extend([f"### `{audit.source_path}` to `{audit.target_path}`", "", "````````diff"])
        lines.extend(audit.unified_diff)
        lines.extend(["````````", ""])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cursor_pstack", type=Path)
    parser.add_argument("--codex-pstack", type=Path, default=Path("plugins/pstack"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    parity = load_parity_module(repo_root)
    upstream_root = args.cursor_pstack.resolve()
    codex_root = args.codex_pstack.resolve()
    run_parity_checker(repo_root, upstream_root, codex_root)
    upstream = parity.files(upstream_root)
    local = parity.files(codex_root)
    validate_inputs(parity, upstream, local)
    audits = [
        audit_pair(source_path, source, parity.source_to_codex(source_path), local[parity.source_to_codex(source_path)])
        for source_path, source in sorted(upstream.items())
    ]
    mapped = {parity.source_to_codex(path) for path in upstream}
    audits.extend(audit_codex_only(path, local[path]) for path in sorted(set(local) - mapped))
    args.output.write_text(
        render(audits, upstream_root, codex_root, split_skill_diff(upstream_root, codex_root)),
        encoding="utf-8",
    )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
