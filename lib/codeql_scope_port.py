"""Keep CodeQL model generation task-local without changing its model algorithms."""
from pathlib import Path


MARKER = "## Task-local model application"


def _replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError("Missing or ambiguous CodeQL scope anchor: " + old[:80])
    return text.replace(old, new, 1)


LOCAL_APPLICATION = """## Task-local model application

Generate the source/sink/summary YAML using the format examples above, only under the
resolved task output directory. Ordinary scan or model-generation authority does not
authorize editing CodeQL's installed libraries, managed pack caches, existing project
models or user configuration. Do not copy models into a `<lang>-all/ext/` directory.

Use a task-local **model pack** when the installed CLI/language supports it. Inspect
`codeql resolve extensions --help` and `codeql database analyze --help` first; these
instructions do not prove that the local installation supports the route. Current
GitHub documentation describes model packs with `library: true`, no dependencies,
`extensionTargets` and `dataExtensions`:

- [Model-pack schema](https://docs.github.com/en/code-security/tutorials/customize-code-scanning/create-and-work-with-codeql-packs#creating-a-codeql-model-pack)
- [Extension resolution and pack flags](https://docs.github.com/en/code-security/reference/code-scanning/codeql/codeql-cli-manual/resolve-extensions)

Write `qlpack.yml` alongside the generated YAML in `$OUTPUT_DIR/extensions/`. Use
a task-owned name, include only files actually generated, and bind the target pack
and version range to the installed pack used by this analysis. This schematic example
needs the actual language/version and generated filenames before use:

```yaml
name: nstack-task/scoped-models
version: 0.0.0
library: true
extensionTargets:
  codeql/<language>-all: "<observed-compatible-version-range>"
dataExtensions:
  - sources.yml
```

Resolve the exact selected explicit query suite with **both** the task-local pack
location (`--additional-packs`) and its name (`--model-packs`). Record successful
resolution output showing the generated extension files, not merely pack discovery
or exit status. For example, after setting absolute `OUTPUT_DIR` and `SUITE_FILE`:

```bash
codeql resolve extensions \\
  --additional-packs="$OUTPUT_DIR/extensions" \\
  --model-packs=nstack-task/scoped-models \\
  -- "$SUITE_FILE"
```

Merge these pack selections with the existing analysis selections; preserve existing
authorized model packs, threat models and query suite. Pass the same resolved local
pack flags to the actual `codeql database analyze` invocation, capture loading diagnostics
and check its current outputs. `--additional-packs` supplies a search location; it is
not by itself evidence that model extensions were selected or applied.

If CLI support, language compatibility, extension resolution or loading cannot be
established, retain the generated task-local files and report **models generated;
application unavailable/unverified** with the exact cause. Continue unaffected work
where useful, but do not claim that these models ran or that model coverage is complete.
A precompiled-pack problem is not authority to mutate the shared cache. Any proposed
shared-cache change requires distinct user authority plus owned backup/recovery and
cross-project scope review; it is not a fallback executed by this workflow.
"""


LOCAL_VALIDATION = """### Step 5: Validate Task-Local Application

**Entry:** Generated task-local extension YAML and model-pack metadata exist.
**Exit:** Either exact extension resolution and actual analysis loading/output are
verified for this source/suite, or application is explicitly unavailable/unverified.

Follow [task-local model application](../references/extension-yaml-format.md#task-local-model-application).
Use the existing explicit-suite generation and quality guards. Preserve baseline
versus with-model analysis, diagnostics and finding comparison: hold source, suite,
existing models and threat flags constant, omit only the new model pack in the baseline,
then rerun with the resolved task-local pack flags. Keep both raw SARIF artifacts.

Record the finding delta as an observation. Equal counts do not prove failed loading;
neutral/sanitizer models may reduce findings. Pack discovery, a nondecreasing count or
an exit code alone does not establish application. Check the resolution output for
the actual generated files and the analysis loading diagnostics before claiming it.

When that evidence is missing, deliver the generated files with the precise application
limit and report any unaffected analysis separately. Do not label generated-only models
as applied, validated or complete, and never deploy into an installed pack to make the
phase appear to pass.

---

"""


FINAL_OUTPUT = """## Final Output

Report the database/source identity, language, output directory and generated model
files. Separate **generation** from **application**. For verified application, include
the actual CLI/pack versions, explicit suite, local pack flags, resolved extension
paths, loading evidence and baseline/with-model observations. Otherwise say
**models generated; application unavailable/unverified**, name the missing evidence
and preserve the files for continuation. Do not claim deployment to a library cache.

"""


def patch(out):
    """Port an already-patched pinned leaf; refuse unknown source structure."""
    out = Path(out)
    ref = out / "references/extension-yaml-format.md"
    workflow = out / "workflows/create-data-extensions.md"
    analysis = out / "workflows/run-analysis.md"
    r, w, a = ref.read_text(), workflow.read_text(), analysis.read_text()
    if MARKER in r:
        return

    deployment = r.index("## Deploying Extensions")
    validation = w.index("### Step 5: Validate with Re-Analysis")
    final = w.index("## Final Output", validation)
    references = w.index("## References", final)
    # Preserve original troubleshooting/validation as reference data, not an active
    # deployment route. Model-generation/schema algorithms above these cuts stay intact.
    archive = ("Historical upstream deployment/validation reference only. Not execution "
               "instructions or authority for shared-cache writes.\n\n" + r[deployment:] +
               "\n\n" + w[validation:references])
    archive_path = out / "references/upstream-model-application.reference.txt"
    if archive_path.exists() and archive_path.read_text() != archive:
        raise ValueError("Existing CodeQL deployment reference differs; preserved")

    r = r[:deployment] + LOCAL_APPLICATION
    w = _replace(w, "**Exit:** Either no gaps found (report adequate coverage and finish) OR user confirms which gaps to model (proceed to Step 4)",
                 "**Exit:** Source-backed gaps selected within existing scope, or no additional models identified. Report the observed coverage without claiming universal completeness.")
    w = _replace(w, "**Exit:** YAML extension files created in `$OUTPUT_DIR/extensions/` and deployed to `<lang>-all` ext/ directory",
                 "**Exit:** YAML extension files created in `$OUTPUT_DIR/extensions/`; application remains unverified until Step 5.")
    w = _replace(w, "and the deployment workaround for pre-compiled query packs.",
                 "and the task-local model-pack application boundary.")
    # Recalculate positions after the preceding scope replacements.
    validation = w.index("### Step 5: Validate with Re-Analysis")
    references = w.index("## References", validation)
    w = w[:validation] + LOCAL_VALIDATION + FINAL_OUTPUT + w[references:]

    start = a.index("## The one gate")
    end = a.index("## Steps", start)
    a = a[:start] + """## Existing authority and scoped choices

Record mode, query/model packs and threat model within existing scan authority.
Resolve unambiguous defaults from the task and source. Ask only for material missing
scope, access or a consequential unresolved choice; no fixed approval gate applies.

---

""" + a[end:]
    a = _replace(a, "# Fill these from the Step 3 answers. Empty means \"the user chose none\".",
                 "# Fill these from the resolved Step 3 scope, including verified task-local models.")
    start = a.index("**Model pack flags:**")
    end = a.index("\n---\n", start)
    a = a[:start] + """**Model pack flags:**
Use the installed CLI's supported interface. Select a task-local model pack with
both its location via `--additional-packs` and its name via `--model-packs`; verify
the exact extension files against the selected suite before analysis. Preserve
other authorized pack selections. A bare YAML search path is not model application.
See [task-local model application](../references/extension-yaml-format.md#task-local-model-application).
""" + a[end:]
    start = a.index("**Flag reference for model packs:**")
    end = a.index("### Performance", start)
    a = a[:start] + """**Model application evidence:** Use the same resolved model-pack and
additional-pack flags in extension resolution and actual analysis. If application
is unavailable, report it separately from generated files and unmodeled results.

""" + a[end:]

    for path, text in ((ref, r), (workflow, w), (analysis, a), (archive_path, archive)):
        path.write_text(text)
