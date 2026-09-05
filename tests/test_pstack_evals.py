from __future__ import annotations

import importlib.util
import shutil
from pathlib import Path

import pytest

SUITE = Path(__file__).resolve().parents[1] / 'plugins/pstack/evals'


def runner():
    spec = importlib.util.spec_from_file_location('pstack_evals', SUITE / 'run.py')
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_prepare_isolates_inputs_and_refuses_overwrite(tmp_path):
    module = runner()
    plugin = tmp_path / 'plugin'
    skill = plugin / 'skills/poteto-mode/SKILL.md'
    skill.parent.mkdir(parents=True)
    skill.write_text('Local instructions\n')
    private = plugin / 'evals/private.txt'
    private.parent.mkdir()
    private.write_text('Coordinator-only material\n')
    target = tmp_path / 'project'

    result = module.prepare('event-feed', target, plugin)

    assert Path(result['workspace']) == target
    assert (target / 'events.py').is_file()
    assert (target / 'guide/skills/poteto-mode/SKILL.md').read_text() == skill.read_text()
    assert not (target / 'guide/evals').exists()
    assert not (target / 'heldout.py').exists()
    (target / 'events.py').write_text('Retained user work\n')
    with pytest.raises(ValueError, match='already exist'):
        module.prepare('event-feed', target, plugin)
    assert (target / 'events.py').read_text() == 'Retained user work\n'
    with pytest.raises(ValueError, match='outside the plugin'):
        module.prepare('event-feed', plugin / 'project', plugin)
    repeated = module.prepare('event-feed', tmp_path / 'second', plugin)
    assert result['instruction_sha256'] == repeated['instruction_sha256']
    skill.write_text('Changed local instructions\n')
    changed = module.prepare('event-feed', tmp_path / 'third', plugin)
    assert result['instruction_sha256'] != changed['instruction_sha256']
    assert result['case_sha256'] == changed['case_sha256']


@pytest.mark.parametrize('case', ['event-feed', 'lease-queue', 'inventory-holds'])
def test_behavior_checks_reject_unfinished_seed(tmp_path, case):
    module = runner()
    workspace = tmp_path / 'project'
    shutil.copytree(SUITE / case / 'workspace', workspace)

    result = module.verify(case, workspace, 10)

    assert not result['passed']
    assert result['exit_code'] != 0


def test_verifier_accepts_behavior_and_reports_timeout(tmp_path):
    module = runner()
    suite = tmp_path / 'suite'
    case = suite / 'local-case'
    case.mkdir(parents=True)
    (case / 'heldout.py').write_text('from product import answer\nassert answer() == 42\n')
    workspace = tmp_path / 'project'
    workspace.mkdir()
    product = workspace / 'product.py'
    product.write_text('def answer():\n    return 42\n')
    module.ROOT = suite

    assert module.verify('local-case', workspace, 5)['passed']

    product.write_text('def answer():\n    return 41\n')
    assert not module.verify('local-case', workspace, 5)['passed']

    product.write_text('while True:\n    pass\n')
    timed_out = module.verify('local-case', workspace, 0.1)
    assert not timed_out['passed']
    assert timed_out['reason'] == 'timeout'
