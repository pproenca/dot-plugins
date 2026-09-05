from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path


def load_parity_module():
    script = Path(__file__).resolve().parents[1] / "scripts" / "check_pstack_cursor_parity.py"
    spec = importlib.util.spec_from_file_location("check_pstack_cursor_parity", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_translation_receipt_rejects_changed_target(tmp_path: Path) -> None:
    parity = load_parity_module()
    source = tmp_path / "source.md"
    target = tmp_path / "target.md"
    source.write_text("Cursor source\n")
    target.write_text("Reviewed Codex translation\n")
    paths = frozenset({"skill.md"})
    source_digest = parity.translation_digest([("skill.md", source)])
    target_digest = parity.translation_digest([("skill.md", target)])

    target.write_text("Unreviewed replacement\n")

    assert parity.translation_receipt_failures(
        {"skill.md": source},
        {"skill.md": target},
        {"skill.md"},
        paths,
        source_digest,
        target_digest,
    ) == ["Codex translation digest differs from the reviewed migration"]


def test_translation_digest_binds_the_source_path(tmp_path: Path) -> None:
    parity = load_parity_module()
    payload = tmp_path / "payload.md"
    payload.write_text("same bytes\n")

    first = parity.translation_digest([("first.md", payload)])
    second = parity.translation_digest([("second.md", payload)])

    assert first != second
    assert first != hashlib.sha256(payload.read_bytes()).hexdigest()


def test_release_version_preserves_review_receipt_but_metadata_changes_do_not(tmp_path: Path) -> None:
    parity = load_parity_module()
    manifest = tmp_path / "plugin.json"
    payload = {"name": "example", "version": "1.0.0", "skills": "./skills/"}
    manifest.write_text(json.dumps(payload))
    entries = [(".codex-plugin/plugin.json", manifest)]
    reviewed = parity.translation_digest(entries)

    payload["version"] = "1.0.1"
    manifest.write_text(json.dumps(payload, indent=2))
    assert parity.translation_digest(entries) == reviewed

    payload["skills"] = "./other-skills/"
    manifest.write_text(json.dumps(payload))
    assert parity.translation_digest(entries) != reviewed


def test_codex_only_receipt_rejects_changed_policy(tmp_path: Path) -> None:
    parity = load_parity_module()
    policy = tmp_path / "openai.yaml"
    policy.write_text("policy:\n  allow_implicit_invocation: false\n")
    paths = frozenset({"skills/demo/agents/openai.yaml"})
    digest = parity.translation_digest([("skills/demo/agents/openai.yaml", policy)])

    policy.write_text("policy:\n  allow_implicit_invocation: true\n")

    assert parity.codex_only_receipt_failures(
        {"skills/demo/agents/openai.yaml": policy},
        set(paths),
        paths,
        digest,
    ) == ["Codex-only digest differs from the reviewed migration"]


def test_source_mapping_collisions_are_rejected() -> None:
    parity = load_parity_module()

    failures = parity.mapping_collision_failures(
        {"agents/comment-sicko.md", "com.cursor/agents/comment-sicko.md"}
    )

    assert failures == [
        "source mapping collision: ['agents/comment-sicko.md', "
        "'com.cursor/agents/comment-sicko.md'] -> com.cursor/agents/comment-sicko.md"
    ]


def test_codex_multi_phase_template_passes_its_checker(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    playbook = root / "plugins/pstack/skills/poteto-mode/playbooks/multi-phase-plan.md"
    checker = root / "plugins/pstack/skills/poteto-mode/scripts/check-plan.mjs"
    source = playbook.read_text()
    template = source.split("````markdown\n", 1)[1].split("\n````", 1)[0]
    plan = tmp_path / "plan.md"
    plan.write_text(template)

    result = subprocess.run(
        ["node", checker, plan],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
