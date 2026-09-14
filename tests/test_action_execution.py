"""Execute the advertised CLI contract, including cwd, without guessed flags."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def cli(argv, cwd):
    return subprocess.run(
        [sys.executable, '-m', 'kahn', *argv[1:]], cwd=cwd,
        env={**os.environ, 'PYTHONPATH': str(ROOT), 'KAHN_HUMAN_OUTPUT': 'false'},
        capture_output=True, text=True, timeout=30,
    )


def next_action(project, cwd):
    result = cli(['kahn', 'next', '--project-dir', str(project)], cwd)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload['status'] == 'ok'
    action = payload['data']['action']
    assert shlex.split(payload['data']['next_command']) == action['argv']
    return action


def execute(action, values):
    argv = list(action['argv'])
    for key, field in action['input_schema'].items():
        if key in values:
            argv.extend([field['flag'], values[key]])
    return cli(argv, action['cwd'])


@pytest.mark.parametrize('existing', [False, True])
def test_initialization_and_force_actions_execute_from_returned_cwd(tmp_path, existing):
    project = tmp_path / "client's study" / 'nested project'
    if existing:
        project.mkdir(parents=True)
    action = next_action(project, tmp_path)
    assert Path(action['cwd']).is_dir()
    assert project.exists() is existing  # next must not create the missing tree.
    result = execute(action, {'question': 'How should we enter?', 'domain': 'energy', 'horizon': '2030'})
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['status'] == 'ok'
    action = next_action(project, tmp_path)
    assert action['cwd'] == str(project.resolve())
    assert action['input_schema']['impact']['required'] is True
    values = dict(name='Storage costs', domain='technological', type='trend', impact='high', predictability='high', direction='falling')
    before = {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()}
    failed = execute(action, {key: value for key, value in values.items() if key != 'impact'})
    assert failed.returncode != 0
    assert before == {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()}
    # Do not decode failed CLI output. Recover by asking the package for its action.
    recovered = next_action(project, tmp_path)
    assert recovered == action
    success = execute(recovered, values)
    assert success.returncode == 0, success.stderr
    assert json.loads(success.stdout)['status'] == 'ok'
    assert next_action(project, tmp_path)['cwd'] == str(project.resolve())


def test_missing_project_beneath_symlink_targets_canonical_directory(tmp_path):
    actual = tmp_path / 'actual'
    actual.mkdir()
    alias = tmp_path / 'alias'
    alias.symlink_to(actual, target_is_directory=True)
    project = alias / 'new' / 'study'
    action = next_action(project, tmp_path)
    assert action['cwd'] == str(actual.resolve())
    assert action['project_dir'] == str((actual / 'new' / 'study').resolve())
    result = execute(action, {'question': 'What changes?', 'domain': 'energy', 'horizon': '2030'})
    assert result.returncode == 0, result.stderr
    assert next_action(project, tmp_path)['cwd'] == str(project.resolve())
