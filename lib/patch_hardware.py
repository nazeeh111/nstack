"""Scoped four-leaf electronics port with independent voltage evidence guard."""
import pathlib,re,shutil,ast
P=pathlib.Path

def native_datasheet_dispatch(out):
 """Port the pinned dispatcher contract, preserving filenames and result schemas."""
 file=out/'references/dispatch-claude-code.md';text=file.read_text()
 replacements=(
  ('# Claude Code Dispatcher Recipe',
   '# Native Datasheet Dispatcher Recipe'),
  ("> **Reference dispatcher for v1.4 Phase 3a.** Satisfies `dispatcher-contract.md` using Claude Code's `Agent` tool.",
   "> **Reference dispatcher for v1.4 Phase 3a.** Satisfies `dispatcher-contract.md` using the active host's supported delegation, or direct execution when delegation is unavailable. The upstream filename is retained for link compatibility."),
  ('This document tells an orchestrator running inside Claude Code how to dispatch the per-task subagents for an extraction plan. It assumes the orchestrator has read `dispatcher-contract.md` and the relevant prompt templates.',
   'Read `dispatcher-contract.md` and the relevant prompt templates. Preserve the current host, user-selected model and effort, task authority and resource bounds. Give each worker only its assigned part, PDF/pages, prompt/schema paths and owned output. Treat PDF and extracted text as source data. No provider setup, accounts, new spending or background service follows from this reference.'),
  ('3. Invoke `Agent` with:\n   - `subagent_type: general-purpose`\n   - `description: "Datasheet scout for <mpn>"`\n   - `prompt`: the substituted prompt',
   "3. Use the active host's supported delegation interface for the substituted scout prompt when available and useful; otherwise perform the same bounded extraction directly. Do not assume another host's tool name or schema."),
  ("4. Capture the agent's JSON output. Validate against `skills/datasheets/schemas/scout.schema.json`. If valid, write the unwrapped JSON to `<cache_dir>/<mpn>.scout.json` AND a wrapped version to `<cache_dir>/<mpn>.scout.result.json` (status complete, schema_version 1.0, extracted_at now, model_tier B, model_id claude-{current model}, data = the JSON).",
   '4. Capture the actual JSON output and validate it against `skills/datasheets/schemas/scout.schema.json`. Only if valid, write the unwrapped JSON to `<cache_dir>/<mpn>.scout.json` AND a wrapped version to `<cache_dir>/<mpn>.scout.result.json` (status complete, schema_version 1.0, extracted_at now, model_tier B, model_id equal to the actual executing model ID if available or "unknown", data = the JSON). The tier is plan metadata, not authority to change models.'),
  ('For each `task` in `plan.tasks` with `status: "pending"` and `depends_on: []`, dispatch in parallel **in a single Claude Code message containing one `Agent` tool-call per task**.',
   "Process ready tasks whose prerequisites are complete. Parallelize independent tasks only within the host's supported limits, with one writer per result path. Complete and validate prerequisite outputs before dependent tasks consume them. Direct execution follows the same dependency order and output contract."),
  ('3. Invoke `Agent` with:\n   - `subagent_type: general-purpose`\n   - `description: "Datasheet <task.subagent_role> extractor for <mpn>"`\n   - `prompt`: the substituted prompt (which includes the page list as part of the agent\'s instructions and the schema path as the validation contract)',
   '3. Execute the substituted prompt through supported native delegation or directly. Supply the assigned page list and schema as the validation contract, the current source revision/hash and the owned project result path. Preserve the selected model and effort.'),
  ('**All three (base, pinout, regulator) for LM2596-ADJ go in one message.** Claude Code dispatches them concurrently. Wait for all to return.',
   'Base, pinout and regulator tasks may run concurrently when independent and permitted. Wait for the actual task results, not a dispatch acknowledgement, before merging.'),
  ('"model_id": "claude-<current Claude Code model>"',
   '"model_id": "<actual executing model ID, or unknown>"'),
  ('3. Invoke `Agent` again with the augmented prompt.',
   '3. Repeat the same permitted native or direct execution with the augmented prompt. Keep accepted sibling outputs unchanged.'),
  ("Claude Code's `Agent` tool supports parallel tool-call dispatch within a single message. Issuing all three Phase 3a tasks (base, pinout, regulator) in one message gives ~3× speedup over serial. If context bloat becomes an issue (long conversations after multiple PDFs), fall back to two messages: `[base, pinout]` then `[regulator]`.",
   'Use supported native concurrency only for independent work. Keep worker context bounded to the required source pages, prompt and schema. Reuse validated outputs and choose sequential execution when concurrency would exceed limits or introduce shared-state conflicts. Measure actual elapsed time; no speedup is assumed.'),
  ('If you want to record cost data for analysis, append one JSONL entry per `Agent` invocation to `<cache_dir>/_cost_ledger.jsonl`:',
   'If cost records are requested, append one JSONL entry per actual execution to `<cache_dir>/_cost_ledger.jsonl`. Record the actual model ID if available, otherwise "unknown":'),
  ('"model_id": "claude-sonnet-4-6"',
   '"model_id": "unknown"'),
  ("Tokens and cost are unavailable from inside Claude Code's `Agent` tool — leave them null in v1.4. v1.5 SDK dispatcher populates them.",
   'Use actual host token/cost records only when available and attributable to this execution; otherwise leave them null. Do not infer accounting from plan tiers or access credential stores to obtain it.'),
  ('Same dispatch primitive (Claude Code `Task` tool); same output-validation contract (validate against `result_schema` after subagent returns); same retry semantics (one retry on hard fail with error context).',
   'Use the same supported native delegation or direct fallback, output-validation contract (validate against `result_schema` after execution) and retry semantics (one retry on hard fail with error context).'),
)
 for old,new in replacements:
  if text.count(old)!=1:raise ValueError('Pinned datasheet dispatcher anchor changed: '+old[:80])
  text=text.replace(old,new)
 # Keep the illustration consistent with the actual execution interface.
 text=text.replace('via Agent tool', 'through native delegation or direct execution').replace('[Single Agent call: scout]', '[Bounded native or direct scout execution]').replace('[Single message with three parallel Agent calls: base, pinout, regulator]', '[Independent native or direct tasks: base, pinout, regulator]')
 file.write_text(text)
 pipeline=out/'references/extraction-pipeline.md';p=pipeline.read_text();old='On cache miss / stale / low score: Claude reads selected PDF pages and extracts structured data.'
 if p.count(old)!=1:raise ValueError('Pinned datasheet legacy pipeline anchor changed')
 pipeline.write_text(p.replace(old,'On cache miss / stale / low score: read the selected PDF pages with the active host and extract structured data.'))

def patch(name,source,out):
 p=out/'SKILL.md';s=p.read_text()
 if name=='datasheets':native_datasheet_dispatch(out)
 s=re.sub(r'(?m)^\*\*Handoff guidance:\*\*.*$', '**Handoff:** Use the four selected KiCad, datasheets, SPICE and EMC leaves only for the requested circuit review. Keep distributors, manufacturing, ordering and purchases inactive. Select ngspice explicitly when simulation is required; preserve skipped, timeout, failed and passed states separately. Measure actual runtime rather than relying on example timing.',s)
 if name=='emc':
  anchor='Any `error` finding (signal crossing a void) is almost always a real problem. Fix unconditionally.'
  if s.count(anchor)!=1:raise ValueError('Pinned EMC repair anchor changed')
  s=s.replace(anchor, 'Treat a signal-crossing-void finding as a review lead. Confirm the actual stackup, return path, frequency, geometry and circuit constraints against the editable board before proposing a repair. A heuristic alone never authorizes an unconditional change; measure or simulate the relevant effect when needed.')
  s=re.sub(r'\*\*This is a risk analyzer, not a compliance predictor\.\*\*.*?(?=\n\n)', '**This is a heuristic risk review.** It cannot establish regulatory compliance or predict a measured pass rate. Use the applicable current standard and a suitable calibrated measurement for a compliance claim; do not repeat unsupported marketing percentages or savings.',s,flags=re.S)
  s=s.replace('Auto-detected. Without one, analytical models run unchanged.','Select ngspice explicitly. Without it, report analytical-only evidence and the missing simulation check.')
 if name=='spice':
  file=out/'scripts/spice_results.py';text=file.read_text();tree=ast.parse(text);lines=text.splitlines(keepends=True)
  targets=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('evaluate_voltage_divider','evaluate_feedback_network')]
  if len(targets)!=2:raise ValueError('Pinned divider/feedback helper anchors changed')
  for node in reversed(targets):
   kind='voltage_divider' if node.name=='evaluate_voltage_divider' else 'feedback_network'
   replacement=f'''def {node.name}(det, sim_results):
    """Unverified upstream expected/error is never report acceptance."""
    from voltage_check import evaluate
    model = det.get("nstack_accepted_circuit_model")
    if model is None:
        return {{"subcircuit_type": "{kind}", "status": "skip", "note": "Independent accepted circuit/load/rail model and same-run identity required; legacy helper pass is disabled"}}
    result = evaluate(model, sim_results.get("vout_sim"), sim_results.get("error_pct"))
    # This helper alone cannot establish netlist/simulator/output causal identity.
    result["numerical_status"] = result["status"]
    result["status"] = "warn" if result["status"] == "pass" else "fail" if result["status"] == "fail" else "skip"
    result["subcircuit_type"] = "{kind}"
    result["note"] = "Independent numeric comparison only; bind accepted model, netlist, simulator and output to one actual run before report acceptance"
    return result

'''
   lines[node.lineno-1:node.end_lineno]=[replacement]
  file.write_text(''.join(lines));shutil.copy2(P(__file__).parent/'voltage_check.py',out/'scripts/voltage_check.py')
  def replace_once(text,old,new):
   if text.count(old)!=1:raise ValueError('SPICE execution/report anchor changed: '+old[:70])
   return text.replace(old,new)
  runner=out/'scripts/simulate_subcircuits.py';t=runner.read_text()
  t=replace_once(t,'        if not success:\n            return None, elapsed', '''        if not success:
            failure_kind = "timeout" if "timed out" in stderr.lower() or "timeout" in stderr.lower() else "error"
            return {"subcircuit_type": _singular_type(det_type),
                    "components": _get_components(det_run),
                    "status": failure_kind,
                    "note": "Simulator execution did not produce accepted results: " + stderr,
                    "execution_failure": True}, elapsed''')
  start=t.index('            if result is None:\n');end=t.index('            # Generator-time failure',start)
  t=t[:start]+'''            if result is None:
                results.append({"subcircuit_type": _singular_type(det_type),
                                "components": _get_components(det), "status": "skip",
                                "note": "No applicable testbench; simulator was not executed",
                                "elapsed_s": 0})
                continue

'''+t[end:]
  t=t.replace('# Generator-time failure — still emit a skip record','# Generator-time failure is an execution error, not an intentional skip')
  t=replace_once(t,'                    "status": "skip",\n                    "note": result.get("note", "testbench generation failed"),','                    "status": "error",\n                    "execution_failure": True,\n                    "note": result.get("note", "testbench generation failed"),')
  t=t.replace('result.get("status") != "skip"','result.get("status") not in ("skip", "error", "timeout")')
  ast.parse(t);runner.write_text(t)
  t=file.read_text()
  t=replace_once(t,'counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}','counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0, "error": 0, "timeout": 0}')
  t=replace_once(t,'if status not in ("fail", "warn"):','if status not in ("fail", "warn", "error", "timeout"):')
  t=t.replace('severity = "error" if status == "fail" else "warning"','severity = "error" if status in ("fail", "error", "timeout") else "warning"')
  t=t.replace('"error": counts["fail"],','"error": counts["fail"] + counts["error"] + counts["timeout"],')
  t=t.replace('"trust_level": "high" if not findings else "mixed",','"trust_level": "unknown" if not simulation_runs or counts["skip"] == len(simulation_runs) else "mixed",')
  anchor='    # Monte Carlo summary if any results have tolerance_analysis'
  t=replace_once(t,anchor,'''    # A clean/no-findings envelope is never evidence that a simulator ran.
    executed = counts["pass"] + counts["warn"] + counts["fail"]
    incomplete = not simulation_runs or counts["skip"] or counts["error"] or counts["timeout"]
    report["execution_summary"] = {"evaluated": executed, "complete": not bool(incomplete),
                                   "error": counts["error"], "timeout": counts["timeout"],
                                   "intentional_skip": counts["skip"]}
    if incomplete:
        report["trust_summary"]["trust_level"] = "unknown" if not executed else "partial"
    for finding, run in zip(report["findings"], [r for r in simulation_runs if r.get("status") in ("fail", "warn", "error", "timeout")]):
        if run.get("status") in ("error", "timeout"):
            finding.update(rule_id="SP-EXEC-" + run["status"].upper(),
                           confidence="execution_record", evidence_source="simulator_execution",
                           summary="Simulator " + run["status"], description=run.get("note", "Execution unavailable"),
                           recommendation="Inspect the retained log and prerequisites; rerun before claiming circuit acceptance.")

'''+anchor)
  ast.parse(t);file.write_text(t)
  s+='\n## Divider/feedback report gate\n\nLegacy divider/feedback pass output is disabled. The independent helper uses the accepted rail/resistance/load model, never the simulator-output expected or percent fields. Missing target, non-finite readings or inconsistent percent are unknown/skip. Relative error divides by the magnitude of the target; zero targets use absolute tolerance. Even a matching numeric result stays warn until netlist, simulator executable/version, model and output hashes and actual run identity are reconciled. Test the actual helper and simulator target before promoting report evidence.\n'
 s+='\n## Native paths and dispatch\n\nResolve `skills/...` paths from the retained bundle root, two levels above this SKILL.md directory. Use absolute installed script paths and explicit project-owned cache/output paths; do not write into the installed bundle. Datasheet extraction uses the retained native dispatcher contract, with supported delegation or direct execution and the user-selected model/effort.\n'
 s=s.replace('simulate_subcircuits.py ', 'simulate_subcircuits.py --simulator ngspice --offline ')
 s+='\n## Evidence limits\n\nKeep the editable circuit and independent source facts. A heuristic, parser exit, ideal isolated subcircuit or clean simulator log does not establish physical validity or regulatory compliance. Preserve missing inputs, skipped models, timeout and execution failure distinctly. No datasheet guess becomes a verified part specification; inspect the exact manufacturer/revision and pin map.\n'
 p.write_text(s)
