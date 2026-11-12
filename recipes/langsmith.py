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
    if not index.is_file():
        raise ValueError('Install/register the shared LangChain/LangGraph runtime first')
    before = index.read_bytes()
    rows = json.loads(before)
    base = next((r for r in rows if r.get('name') == 'LangChain / LangGraph'), None)
    if not base:
        raise ValueError('Existing LangChain / LangGraph runtime record required')
    code = profile_install.stage(state)
    entry = code / 'recipes/langsmith.py'
    record = {'name': 'LangSmith', 'aliases': ['LangSmith tracing', 'LangSmith evaluation'],
              'description': 'Local LangGraph execution traces and deterministic evaluation; hosted LangSmith tracing, datasets and experiments are available only after explicit project commissioning.',
              'activation': 'on demand; local example ready; hosted account, key, approved data destination and spending scope are unconfigured',
              'version': '0.14.17', 'shared_runtime_id': base['shared_runtime_id'],
              'runtime_root': base['runtime_root'], 'entrypoint': str(entry),
              'invoke': [sys.executable, str(entry), '--state', str(state), 'check'],
              'documentation': str(code / 'integrations/ai-workflows/langsmith/README.md'),
              'source': 'https://github.com/langchain-ai/langsmith-sdk',
              'dependency_lock': str(code / 'integrations/ai-workflows/requirements.lock'),
              'hosted_tracing_enabled': False}
    existing = [r for r in rows if r.get('name') == 'LangSmith']
    if existing == [record]:
        return {'unchanged': True, 'entrypoint': str(entry)}
    if existing:
        raise ValueError('Existing LangSmith record differs; reconcile it before replacement')
    proof = check(state)
    desired = (json.dumps(rows + [record], indent=2) + '\n').encode()
    run = state / 'runs' / ('langsmith-' + uuid.uuid4().hex)
    tx = Transaction(run)
    with tx.lock():
        expected = fingerprint(index)
        assert index.read_bytes() == before, 'Concurrent tool index update'
        # Rehearse restoration of the actual current bytes independently.
        copy(index, run / 'index-original.json')
        copy(run / 'index-original.json', run / 'restoration-rehearsal.json')
        assert (run / 'restoration-rehearsal.json').read_bytes() == before
        same(index, expected)
        tx.replace_file(index, desired, mode=0o600, expected=expected)
    assert json.loads(index.read_text()) == rows + [record]
    return {'installed': True, 'entrypoint': str(entry), 'transaction': str(run), 'check': proof}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', default=str(STATE))
    parser.add_argument('command', choices=['install', 'check'])
    args = parser.parse_args()
    print(json.dumps(register(args.state) if args.command == 'install' else check(args.state), indent=2))
