#!/usr/bin/env python3
"""Check that the Codex pstack package accounts for the Cursor source tree."""

import argparse
import hashlib
from pathlib import Path

CODEX_ONLY = {
    ".codex-plugin/plugin.json",
    "plugin.json",
    "docs/codex-adaptation.md",
    "skills/poteto-mode/references/full-mode.md",
    "skills/poteto-mode/references/codex-tools.md",
}

CODEX_POLICY_SKILLS = frozenset(
    """architect
arena
automate-me
blast-radius
bro
create-verification-skill
figure-it-out
interrogate
maintain-verification-skill
no-comments
poteto-mode
principle-boundary-discipline
principle-build-the-lever
principle-encode-lessons-in-structure
principle-exhaust-the-design-space
principle-experience-first
principle-fix-root-causes
principle-foundational-thinking
principle-guard-the-context-window
principle-laziness-protocol
principle-make-operations-idempotent
principle-migrate-callers-then-delete-legacy-apis
principle-minimize-reader-load
principle-model-the-domain
principle-never-block-on-the-human
principle-outcome-oriented-execution
principle-prove-it-works
principle-redesign-from-first-principles
principle-separate-before-serializing-shared-state
principle-sequence-verifiable-units
principle-subtract-before-you-add
principle-type-system-discipline
recall
reflect
show-me-your-work
swarm
tdd
teach
technical-writing""".splitlines()
)

TRANSLATABLE = frozenset(
    """.cursor-plugin/plugin.json
README.md
assets/logo.png
docs/guide/01-setup.md
docs/guide/02-poteto-mode.md
docs/guide/03-understand.md
docs/guide/04-design.md
docs/guide/05-build-and-clean.md
docs/guide/06-verify-and-ship.md
docs/guide/07-overnight.md
docs/guide/08-principles.md
docs/guide/09-make-it-yours.md
docs/guide/10-recipes-and-pitfalls.md
docs/guide/README.md
skills/architect/SKILL.md
skills/arena/SKILL.md
skills/automate-me/SKILL.md
skills/blast-radius/SKILL.md
skills/bro/SKILL.md
skills/create-verification-skill/SKILL.md
skills/figure-it-out/SKILL.md
skills/how/SKILL.md
skills/how/references/explainer-prompt.md
skills/how/references/explorer-prompt.md
skills/interrogate/SKILL.md
skills/interrogate/references/rubric.md
skills/maintain-verification-skill/SKILL.md
skills/make-bot-ui/SKILL.md
skills/no-comments/SKILL.md
skills/poteto-mode/SKILL.md
skills/poteto-mode/playbooks/authoring-a-skill.md
skills/poteto-mode/playbooks/autonomous-run.md
skills/poteto-mode/playbooks/autopilot-full.md
skills/poteto-mode/playbooks/autopilot-stack.md
skills/poteto-mode/playbooks/babysit.md
skills/poteto-mode/playbooks/bug-fix.md
skills/poteto-mode/playbooks/eval.md
skills/poteto-mode/playbooks/feature.md
skills/poteto-mode/playbooks/hillclimb.md
skills/poteto-mode/playbooks/multi-phase-plan.md
skills/poteto-mode/playbooks/opening-a-pr.md
skills/poteto-mode/playbooks/orchestrate.md
skills/poteto-mode/playbooks/pause-safely.md
skills/poteto-mode/playbooks/perf-issue.md
skills/poteto-mode/playbooks/refactoring.md
skills/poteto-mode/playbooks/session-pickup.md
skills/poteto-mode/playbooks/shipping.md
skills/poteto-mode/playbooks/visual-parity.md
skills/poteto-mode/playbooks/worktree-cleanup.md
skills/poteto-mode/scripts/check-plan.mjs
skills/poteto-mode/scripts/worktree-audit.sh
skills/principle-boundary-discipline/SKILL.md
skills/principle-build-the-lever/SKILL.md
skills/principle-encode-lessons-in-structure/SKILL.md
skills/principle-exhaust-the-design-space/SKILL.md
skills/principle-experience-first/SKILL.md
skills/principle-fix-root-causes/SKILL.md
skills/principle-foundational-thinking/SKILL.md
skills/principle-guard-the-context-window/SKILL.md
skills/principle-laziness-protocol/SKILL.md
skills/principle-make-operations-idempotent/SKILL.md
skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md
skills/principle-minimize-reader-load/SKILL.md
skills/principle-model-the-domain/SKILL.md
skills/principle-never-block-on-the-human/SKILL.md
skills/principle-outcome-oriented-execution/SKILL.md
skills/principle-prove-it-works/SKILL.md
skills/principle-redesign-from-first-principles/SKILL.md
skills/principle-separate-before-serializing-shared-state/SKILL.md
skills/principle-sequence-verifiable-units/SKILL.md
skills/principle-subtract-before-you-add/SKILL.md
skills/principle-type-system-discipline/SKILL.md
skills/recall/SKILL.md
skills/reflect/SKILL.md
skills/reflect/references/divergent-reviewer.md
skills/reflect/references/judgment-reviewer.md
skills/reflect/references/synthesizer.md
skills/reflect/references/tooling-reviewer.md
skills/setup-pstack/SKILL.md
skills/show-me-your-work/SKILL.md
skills/swarm/SKILL.md
skills/tdd/SKILL.md
skills/teach/SKILL.md
skills/technical-writing/SKILL.md
skills/typescript-best-practices/SKILL.md
skills/unslop/SKILL.md
skills/why/SKILL.md""".splitlines()
)

EXPECTED_TRANSLATION_SOURCE_DIGEST = "81d73a4f15ee2e567542875b243742c66864f163493fb6cefecda754e713431f"
EXPECTED_TRANSLATION_TARGET_DIGEST = "2d66bfd12ad2d0da2b5d329d0d4d64eb30fcaeee899cb9c4e4f1a34146dd278a"
EXPECTED_CODEX_ONLY_DIGEST = "b55b328c40dba4799cbf01b0c9c05fe858e68a25592caee356a13164f6bf2833"

DEAD_CODEX_REFERENCES = {
    "~/.cursor/": "Cursor home path",
    ".cursor/skills": "Cursor skill path",
    "AskQuestion": "Cursor question tool",
    "Task tool": "Cursor delegation tool",
    "Task call": "Cursor delegation tool",
    "subagent_type": "Cursor delegation field",
    "generalPurpose": "Cursor agent type",
    "run_in_background": "Cursor delegation field",
    "cursor-team-kit": "Cursor-only plugin",
    "Cursor's built-in": "Cursor-only built-in",
    "Cursor cloud": "Cursor-only agent environment",
    "Cursor restart": "Cursor-only restart wording",
    "/loop": "Cursor wake command",
    "/goal": "Cursor goal command",
    "claude-fable-": "Cursor model slug",
    "grok-4.6-": "Cursor model slug",
    "gpt-5.6-sol-max": "Cursor model slug",
    "`create-skill`": "Cursor skill-authoring name",
    "control-ui": "unavailable control skill",
    "/deslop": "Cursor prose command",
    "git reset --hard": "destructive worktree recovery",
    "allow_multiple": "unsupported question-tool field",
    "Use Read, Grep, and Glob": "Cursor file-search tools",
    "Use Glob": "Cursor file-search tool",
    "isolated collaboration agent": "false implicit-worktree claim",
    "`Task` response": "Cursor delegation response",
    "Multiple `Task`": "Cursor delegation call",
}


def source_to_codex(path: str) -> str:
    if path == ".cursor-plugin/plugin.json":
        return "com.cursor/plugin.json"
    if path == "assets/logo.png":
        return "assets/icon.png"
    if path.startswith(("agents/", "automations/")):
        return f"com.cursor/{path}"
    return path


def can_translate(path: str) -> bool:
    return path in TRANSLATABLE


def is_codex_only(path: str) -> bool:
    return path in expected_codex_only_paths()


def expected_codex_only_paths() -> frozenset[str]:
    policy_paths = {f"skills/{skill}/agents/openai.yaml" for skill in CODEX_POLICY_SKILLS}
    return frozenset(CODEX_ONLY | policy_paths)


def files(root: Path) -> dict[str, Path]:
    return {str(path.relative_to(root)): path for path in root.rglob("*") if path.is_file()}


def translation_digest(entries: list[tuple[str, Path]]) -> str:
    digest = hashlib.sha256()
    for source_path, path in sorted(entries):
        payload = path.read_bytes()
        digest.update(source_path.encode())
        digest.update(b"\0")
        digest.update(len(payload).to_bytes(8, "big"))
        digest.update(payload)
    return digest.hexdigest()


def mapping_collision_failures(source_paths: set[str]) -> list[str]:
    mapped_sources: dict[str, list[str]] = {}
    for source_path in source_paths:
        mapped_sources.setdefault(source_to_codex(source_path), []).append(source_path)
    return [
        f"source mapping collision: {sorted(source_paths)} -> {target_path}"
        for target_path, source_paths in sorted(mapped_sources.items())
        if len(source_paths) > 1
    ]


def codex_only_receipt_failures(
    local: dict[str, Path],
    actual_paths: set[str],
    expected_paths: frozenset[str] | None = None,
    expected_digest: str = EXPECTED_CODEX_ONLY_DIGEST,
) -> list[str]:
    expected = expected_paths or expected_codex_only_paths()
    failures = [f"unexpected Codex-only file: {path}" for path in sorted(actual_paths - expected)]
    failures.extend(f"missing required Codex-only file: {path}" for path in sorted(expected - actual_paths))
    if not (expected - actual_paths) and (
        translation_digest([(path, local[path]) for path in expected]) != expected_digest
    ):
        failures.append("Codex-only digest differs from the reviewed migration")
    return failures


def translation_receipt_failures(
    upstream: dict[str, Path],
    local: dict[str, Path],
    translated_paths: set[str],
    expected_paths: frozenset[str] = TRANSLATABLE,
    expected_source_digest: str = EXPECTED_TRANSLATION_SOURCE_DIGEST,
    expected_target_digest: str = EXPECTED_TRANSLATION_TARGET_DIGEST,
) -> list[str]:
    if translated_paths != expected_paths:
        return [
            "translation receipt paths differ: "
            f"missing={sorted(expected_paths - translated_paths)} "
            f"unexpected={sorted(translated_paths - expected_paths)}"
        ]
    if translation_digest([(path, upstream[path]) for path in expected_paths]) != expected_source_digest:
        return ["upstream translation digest differs from the reviewed oracle"]
    if (
        translation_digest([(path, local[source_to_codex(path)]) for path in expected_paths])
        != expected_target_digest
    ):
        return ["Codex translation digest differs from the reviewed migration"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("cursor_pstack", type=Path)
    parser.add_argument(
        "--codex-pstack",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "plugins" / "pstack",
    )
    args = parser.parse_args()

    upstream = files(args.cursor_pstack.resolve())
    codex_root = args.codex_pstack.resolve()
    local = files(codex_root)
    failures = mapping_collision_failures(set(upstream))
    mapped = {source_to_codex(path) for path in upstream}
    exact = 0
    translated = 0
    translated_paths: set[str] = set()

    for source_path, source in sorted(upstream.items()):
        target_path = source_to_codex(source_path)
        target = local.get(target_path)
        if target is None:
            failures.append(f"missing upstream file: {source_path} -> {target_path}")
            continue
        if bool(source.stat().st_mode & 0o111) != bool(target.stat().st_mode & 0o111):
            failures.append(f"executable mode differs: {source_path} -> {target_path}")
        if source.read_bytes() == target.read_bytes():
            exact += 1
        elif can_translate(source_path):
            translated += 1
            translated_paths.add(source_path)
        else:
            failures.append(f"unlisted byte difference: {source_path} -> {target_path}")

    extras = set(local) - mapped
    failures.extend(codex_only_receipt_failures(local, extras))

    failures.extend(translation_receipt_failures(upstream, local, translated_paths))

    scan_roots = [codex_root / "README.md", codex_root / "docs", codex_root / "skills"]
    for root in scan_roots:
        candidates = [root] if root.is_file() else sorted(root.rglob("*.md"))
        for path in candidates:
            text = path.read_text(errors="replace")
            relative = path.relative_to(codex_root)
            for token, meaning in DEAD_CODEX_REFERENCES.items():
                if token in text:
                    failures.append(f"dead Codex reference ({meaning}): {relative}: {token}")

    upstream_skills = {
        path.split("/")[1]
        for path in upstream
        if path.startswith("skills/") and path.count("/") == 2 and path.endswith("/SKILL.md")
    }
    local_skills = {path.parent.name for path in (codex_root / "skills").glob("*/SKILL.md")}
    if upstream_skills != local_skills:
        failures.append(
            "skill entrypoints differ: "
            f"missing={sorted(upstream_skills - local_skills)} extra={sorted(local_skills - upstream_skills)}"
        )

    print(
        f"upstream={len(upstream)} local={len(local)} exact={exact} "
        f"translated={translated} codex_only={len(extras)} skills={len(local_skills)} failures={len(failures)}"
    )
    for failure in failures:
        print(f"FAIL: {failure}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
