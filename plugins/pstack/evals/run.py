#!/usr/bin/env python3
"""Prepare isolated pstack tasks and check their observable results."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = ('event-feed', 'lease-queue')


def tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(root.rglob('*')):
        if path.is_file():
            payload = path.read_bytes()
            digest.update(str(path.relative_to(root)).encode() + b'\0')
            digest.update(len(payload).to_bytes(8, 'big'))
            digest.update(payload)
    return digest.hexdigest()


def prepare(case, destination, plugin):
    source = ROOT / case / 'workspace'
    plugin = plugin.resolve()
    destination = destination.resolve()
    if not (plugin / 'skills/poteto-mode/SKILL.md').is_file():
        raise ValueError('plugin must contain skills/poteto-mode/SKILL.md')
    if destination.is_relative_to(plugin) or destination.is_relative_to(ROOT.parent):
        raise ValueError('destination must be outside the plugin')
    if destination.exists():
        raise ValueError('destination must not already exist')
    shutil.copytree(source, destination)
    shutil.copytree(
        plugin, destination / 'guide',
        ignore=shutil.ignore_patterns('evals', '__pycache__', '*.pyc', '.git', 'node_modules'),
    )
    request = (ROOT / case / 'request.txt').read_text().strip()
    prompt = (
        f'Work in {destination.resolve()}. Use the supplied guide/skills/poteto-mode/SKILL.md '
        f'as the pstack guidance for this project.\n\n{request}\n\n'
        'Work directly without delegating. Keep changes inside this project, leave guide/ unchanged, '
        'and do not read other projects or personal configuration. Do not commit, open a PR, '
        'or contact external services. Finish with the result, brief design notes, and checks run.'
    )
    return {
        'workspace': str(destination.resolve()), 'prompt': prompt,
        'instruction_sha256': tree_digest(destination / 'guide'),
        'case_sha256': tree_digest(ROOT / case),
    }


def verify(case, workspace, timeout):
    environment = dict(os.environ, PYTHONPATH=str(workspace.resolve()), PYTHONDONTWRITEBYTECODE='1')
    command = [sys.executable, '-B', str(ROOT / case / 'heldout.py')]
    try:
        result = subprocess.run(
            command, cwd=workspace, env=environment, text=True, capture_output=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        return {'passed': False, 'reason': 'timeout', 'seconds': timeout, 'output': str(error)}
    return {
        'passed': result.returncode == 0, 'exit_code': result.returncode,
        'stdout': result.stdout, 'stderr': result.stderr,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    create = sub.add_parser('prepare')
    create.add_argument('case', choices=CASES)
    create.add_argument('destination', type=Path)
    create.add_argument('--plugin', type=Path, required=True)
    check = sub.add_parser('verify')
    check.add_argument('case', choices=CASES)
    check.add_argument('workspace', type=Path)
    check.add_argument('--timeout', type=float, default=30)
    args = parser.parse_args()
    if args.operation == 'prepare':
        result = prepare(args.case, args.destination, args.plugin)
    else:
        if args.timeout <= 0:
            parser.error('--timeout must be positive')
        result = verify(args.case, args.workspace, args.timeout)
    print(json.dumps(result, indent=2))
    return 0 if result.get('passed', True) else 1


if __name__ == '__main__':
    raise SystemExit(main())
