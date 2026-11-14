#!/usr/bin/env python3
"""Register and test on-demand local LangSmith in the existing AI workflow runtime."""
import argparse, hashlib, json, sys, uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'lib')]
from recipes.ai_workflows import Runtime, STATE
from transaction import Transaction, copy, fingerprint, same
import install as profile_install

def check(state):
    runtime = Runtime(state)
    runtime.verify()
    out = runtime.root / 'runs' / uuid.uuid4().hex
    out.mkdir(mode=0o700)
    source = ROOT / 'integrations/ai-workflows/langsmith/local_example.py'
    result = runtime.execute(['-c', source.read_text()], out)
    (out / 'execution.json').write_text(json.dumps(result, indent=2) + '\n')
    if result['exit_code'] != 0:
        raise ValueError('Local LangSmith check failed; inspect ' + str(out))
    artifact = json.loads((out / 'langsmith-local.json').read_text())
    assert artifact['result'] == {'value': 12} and artifact['evaluation']['wrong_answer_rejected']
    assert artifact['hosted_upload'] is False and artifact['trace']['children']
    return {'passed': True, 'output': str(out), 'network': 'none', 'provider_calls': 0}

def register(state):
    state = Path(state).absolute()
    index = state / 'native-tools/index.json'
    if state.resolve() != state or index.parent.resolve() != index.parent:
        raise ValueError('Linked runtime index path preserved')
    expected = fingerprint(index)
    if expected['kind'] not in ('absent', 'file'):
        raise ValueError('Runtime index must be a regular file or absent')
    rows = json.loads(index.read_bytes()) if expected['kind'] == 'file' else []
    same(index, expected)
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('Invalid runtime index; preserved')
    # The public AI-workflow recipe owns its verified runtime receipt. A private
    # deployment's optional discovery index is not an installation prerequisite.
    runtime = Runtime(state)
    runtime.verify()
    shared_runtime_id = 'nstack-ai-workflows-' + runtime.fingerprint
    bases = [row for row in rows if row.get('name') == 'LangChain / LangGraph']
    if len(bases) > 1 or (bases and (
            bases[0].get('shared_runtime_id') != shared_runtime_id
            or bases[0].get('runtime_root') != str(runtime.root))):
        raise ValueError('Existing shared runtime record differs; reconcile it before replacement')
    code = profile_install.stage(state)
    entry = code / 'recipes/langsmith.py'
    record = {'name': 'LangSmith', 'aliases': ['LangSmith tracing', 'LangSmith evaluation'],
              'description': 'Local LangGraph execution traces and deterministic evaluation; hosted LangSmith tracing, datasets and experiments are available only after explicit project commissioning.',
              'activation': 'on demand; local example ready; hosted account, key, approved data destination and spending scope are unconfigured',
              'version': '0.14.17', 'shared_runtime_id': shared_runtime_id,
              'runtime_root': str(runtime.root), 'entrypoint': str(entry),
              'invoke': [sys.executable, str(entry), '--state', str(state), 'check'],
              'documentation': str(code / 'integrations/ai-workflows/langsmith/README.md'),
              'source': 'https://github.com/langchain-ai/langsmith-sdk',
              'dependency_lock': str(code / 'integrations/ai-workflows/requirements.lock'),
              'hosted_tracing_enabled': False}
    base_record = {
        'name': 'LangChain / LangGraph',
        'shared_runtime_id': shared_runtime_id, 'runtime_root': str(runtime.root),
        'description': 'Build tool-using AI applications and durable branching state graphs in the explicitly commissioned offline Docker runtime.',
        'activation': 'on demand; explicitly selected application project only',
        'entrypoint': str(code / 'recipes/ai_workflows.py'),
        'documentation': str(code / 'integrations/ai-workflows/README.md'),
        'readiness': 'Installed runtime identity verified; run the AI-workflow check and project acceptance before claiming application behavior.'}
    existing = [r for r in rows if r.get('name') == 'LangSmith']
    if existing and existing != [record]:
        raise ValueError('Existing LangSmith record differs; reconcile it before replacement')
    additions = ([] if bases else [base_record]) + ([] if existing else [record])
    if not additions:
        return {'unchanged': True, 'entrypoint': str(entry)}
    proof = check(state)
    desired_rows = rows + additions
    desired = (json.dumps(desired_rows, indent=2) + '\n').encode()
    run = state / 'runs' / ('langsmith-' + uuid.uuid4().hex)
    tx = Transaction(run)
    with tx.lock():
        same(index, expected)
        # Rehearse restoration of the actual current bytes independently; an
        # absent index is journaled as absent and needs no invented backup.
        if expected['kind'] == 'file':
            copy(index, run / 'index-original.json')
            copy(run / 'index-original.json', run / 'restoration-rehearsal.json')
            same(run / 'restoration-rehearsal.json', expected)
        same(index, expected)
        tx.replace_file(index, desired, mode=0o600, expected=expected)
    assert json.loads(index.read_text()) == desired_rows
    return {'installed': True, 'entrypoint': str(entry), 'transaction': str(run), 'check': proof}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(STATE))
    parser.add_argument('command', choices=['install', 'check'])
    args = parser.parse_args()
    print(json.dumps(register(args.state) if args.command == 'install' else check(args.state), indent=2))
