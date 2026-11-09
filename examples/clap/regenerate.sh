#!/bin/sh
set -eu
task_root=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
task_state=${NSTACK_STATE:-"$HOME/Library/Application Support/nstack"}
task_python="$task_state/runtimes/P318/rt60/venv/bin/python"
task_input=${1:?absolute synthetic WAV path required}
task_output=${2:?new absolute output directory required}
if [ ! -x "$task_python" ]; then
  echo 'Run nstack commission P318 rt60 first.' >&2
  exit 1
fi
if [ -e "$task_output" ]; then
  echo 'Existing results retained; choose a new output directory.' >&2
  exit 1
fi
task_ref=$(mktemp "${TMPDIR:-/tmp}/nstack-clap-reference.XXXXXX")
trap 'rm -f "$task_ref"' EXIT HUP INT TERM
nstack run P318 rt60 -- "$task_input" "$task_ref"
export MPLCONFIGDIR="${TMPDIR:-/tmp}/nstack-clap-matplotlib"
"$task_python" "$task_root/scripts/analyze.py" --input "$task_input" --output "$task_output" --reference "$task_ref"
"$task_python" "$task_root/scripts/verify.py" "$task_output" --current-input "$task_input"
