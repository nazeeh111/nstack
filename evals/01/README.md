# Reproduce 01 behavior checks

These synthetic fixtures and independent checkers are optional authoring tests,
not part of01's runtime or a new agent framework. They use standard-library
Python. No model is called by the control check:

```sh
python3 evals/01/selftest.py
```

It accepts six correct artifacts and rejects six plausible wrong artifacts,
including fabricated live telemetry and a verifier that always prints PASS.

For an actual native trial, materialize a case in an empty disposable directory:

```sh
trial_dir="$(mktemp -d)"
python3 evals/01/fixtures.py specialist "$trial_dir"
```

Start a fresh ordinary Codex conversation in that directory. Supply only the
case's `turns` strings from `cases.json` and its generated fixture files. Do not
give the worker the whole case object: `behavior`, `trace_review`, checker code,
controls, previous outputs and held-out inputs belong to the evaluator. Keep
native event logs and checker outputs outside the worker directory. Use existing
authorized access and the same model/effort for compared variants.

Grade the finished artifacts from this checkout:

```sh
python3 evals/01/checks.py specialist "$trial_dir"
```

`late_need` uses three turns in one conversation: Markdown, a later Canvas need
without another01 invocation, then explicit disabling. Its checker accepts
`--turn 0`, `--turn 1` and `--turn 2`. The simple and disable cases also require
`--response-file` with the actual assistant response. Preserve the first
Markdown's hash through the second turn.

Review actual successful tool requests/results separately from artifact checks.
Require complete relevant skill/reference reads before format decisions and
verify how the method was applied. Report advertised, installed, callable and
demonstrated capabilities distinctly. Protected delegation messages do not
prove their plaintext contents; use a supported observable input when auditing
briefs instead of seeking decryption material.

The Base checker interprets a bounded native-expression subset over seven notes
and four formula holdouts. It is offline format/semantic evidence, not native
Obsidian rendering. An unsupported equivalent expression needs manual or native
review, not an automatic claim of incorrectness. Canvas checks cover structural
and geometric contracts, not a visual design review.

The false-success checker runs the project's supplied scripts on four datasets
and rejects nine damaged/malformed outputs. Run it only against the owned,
reviewed disposable fixtures. It is an ordinary native project check, not OS
containment or an ECC execution gate. No broad reliability or universal
superiority follows from these six small cases.
