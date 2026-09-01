#!/usr/bin/env python3
"""Check that the Codex pstack package accounts for the Cursor source tree."""

import argparse
from pathlib import Path

CODEX_ONLY = {
    ".codex-plugin/plugin.json",
    "assets/icon.png",
    "plugin.json",
    "skills/poteto-mode/references/full-mode.md",
}

TRANSLATABLE = {
    ".cursor-plugin/plugin.json",
    "README.md",
    "skills/poteto-mode/scripts/check-plan.mjs",
    "skills/poteto-mode/scripts/worktree-audit.sh",
}

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
}


def source_to_codex(path: str) -> str:
    if path == ".cursor-plugin/plugin.json":
        return "com.cursor/plugin.json"
    if path.startswith(("agents/", "automations/")):
        return f"com.cursor/{path}"
    return path


def can_translate(path: str) -> bool:
    return path in TRANSLATABLE or path == "README.md" or path.startswith(("docs/", "skills/")) and path.endswith(".md")


def files(root: Path) -> dict[str, Path]:
    return {str(path.relative_to(root)): path for path in root.rglob("*") if path.is_file()}


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
    mapped = {source_to_codex(path) for path in upstream}
    failures: list[str] = []
    exact = 0
    translated = 0

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
        else:
            failures.append(f"unlisted byte difference: {source_path} -> {target_path}")

    extras = set(local) - mapped
    unexpected_extras = extras - CODEX_ONLY
    for path in sorted(unexpected_extras):
        failures.append(f"unexpected Codex-only file: {path}")
    for path in sorted(CODEX_ONLY - extras):
        failures.append(f"missing required Codex-only file: {path}")

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
