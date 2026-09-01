from __future__ import annotations

import hashlib
import importlib.util
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
