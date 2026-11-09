# Synthetic clap workflow

This original fixture needs no recording, model, API or private data. It uses
the registered P318 estimator and independently recomputes the backward energy
and fit for an editable SVG, PDF, PNG and full CSV. The expected values are
0.8 seconds and 1.1 seconds, within 4 milliseconds. These are synthetic tone
decays, not calibrated room measurements.

From this repository, with `nstack` on PATH:

```sh
nstack search room clap decay
nstack show P318
nstack show P112
nstack commission P318 rt60
nstack check P318 rt60
python3 examples/clap/scripts/make_input.py --decay 0.8 --output /absolute/task/clap.wav
sh examples/clap/regenerate.sh /absolute/task/clap.wav /absolute/task/baseline
python3 examples/clap/scripts/check_known.py /absolute/task/clap.wav /absolute/task/baseline/result.json --expected 0.8
python3 examples/clap/scripts/make_input.py --decay 1.1 --output /absolute/task/changed.wav
```

Use the commissioned environment to reject the obsolete handoff, then rebuild:

```sh
"${NSTACK_STATE:-$HOME/Library/Application Support/nstack}/runtimes/P318/rt60/venv/bin/python" \
  examples/clap/scripts/verify.py /absolute/task/baseline --current-input /absolute/task/changed.wav
# The previous command must fail: Stale accepted input.
sh examples/clap/regenerate.sh /absolute/task/changed.wav /absolute/task/corrected
python3 examples/clap/scripts/check_known.py /absolute/task/changed.wav /absolute/task/corrected/result.json --expected 1.1
```

Inspect the current PNG and reopen the PDF. Poppler's `pdftoppm` is an optional
free renderer for that PDF check. The verifier audits every CSV row and SVG
curve vertex, editable text, image dimensions and dependency hashes; it only
checks the PDF header. A numeric or hash pass does not replace visual review.
Original accepted outputs remain unchanged. Keep deployment receipts and
path-bearing manifests private; the repository contains source and synthetic
generators only.

For an actual unfamiliar-task test, start a fresh Codex project with no P112
shelf, configure its project publisher, and give the objective without naming
tools. Observe real discovery, activation and execution. These scripted commands
alone do not prove autonomous model routing.
