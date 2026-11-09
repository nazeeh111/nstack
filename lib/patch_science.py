"""P112's individually selected procedures and their scoped Codex adaptations."""
import pathlib,re
P=pathlib.Path
NAMES={'scientific-critical-thinking','uncertainty-and-units','experimental-design','statistical-analysis','literature-review','citation-management','scientific-visualization','lab-hardware-cad','scientific-writing','hypothesis-generation','statistical-power','peer-review','qiskit','qutip','pennylane'}

def remove_section(text,title,next_title):
 start=text.index(title);end=text.index(next_title,start);return text[:start]+text[end:]

def no_parallel(text):
 # Remove only the unadmitted provider's fenced examples, retaining all other search/data work.
 def fenced(match):
  if not re.search(r'parallel-cli|parallel-web-tools',match[0],re.I):return match[0]
  lines=match[0].splitlines();kept=[lines[0]];continuation=False
  for line in lines[1:-1]:
   if continuation:
    continuation=line.rstrip().endswith('\\');continue
   if re.search(r'parallel-cli|parallel-web-tools|PARALLEL_API_KEY',line,re.I):
    continuation=line.rstrip().endswith('\\');continue
   kept.append(line)
  kept.append(lines[-1]);return '\n'.join(kept)+'\n' if any(l.strip() and not l.lstrip().startswith('#') for l in kept[1:-1]) else ''
 text=re.sub(r'(?ms)^\s*```[^\n]*\n.*?^\s*```[^\n]*',fenced,text)
 text=re.sub(r'(?m)^.*(?:parallel-cli|parallel-web|PARALLEL_API_KEY|docs\.parallel\.ai).*(?:\n|$)','',text)
 return text

def patch(out,name):
 if name not in NAMES:raise ValueError('Scientific leaf still needs its explicit helper adaptation')
 for file in out.rglob('*.md'):
  text=file.read_text()
  if '## Citing Scientific Agent Skills' in text:text=text[:text.index('## Citing Scientific Agent Skills')].rstrip()+'\n'
  text=re.sub(r'(?m)^allowed-tools:.*\n','',text)
  file.write_text(text)
 p=out/'SKILL.md';text=p.read_text()
 if name=='scientific-critical-thinking':
  text=remove_section(text,'## Visual Aids (Optional)','## Core Capabilities')
  text=re.sub(r'(?m)^compatibility:.*$', 'compatibility: Analytical guidance is local and needs no credentials. Use the selected native/scoped figure route only when a figure serves the requested artifact.',text)
 elif name=='literature-review':
  text=remove_section(text,'Conceptual schematics are optional.','## Core Workflow')
  text=remove_section(text,'### Optional search CLI','### Python tooling')
  end=text.index('\n---',4);front=text[:end];body=text[end:]
  front=re.sub(r'(?ms)^  openclaw:.*?(?=^  [A-Za-z0-9_-]+:|\Z)','',front)
  front=re.sub(r'(?m)^compatibility:.*$', 'compatibility: Python 3.10+ with requests for the documented bibliography helpers; native primary-source retrieval for search. PDF export requires a separately commissioned local renderer. No image-generation API or third-party search account is required.',front)
  text=front.rstrip()+body
  for file in out.rglob('*.md'):
   doc=text if file==p else file.read_text()
   doc=re.sub(r'(?m)^Use discipline-appropriate bibliographic databases.*$', 'Use discipline-appropriate bibliographic databases for reproducible searches. Native web retrieval can support scoping and supplementary discovery, with source/date and extraction limits recorded separately. Ranked excerpts do not establish completeness or full-text assessment.',doc)
   doc=doc.replace('1. **Pilot the question**: Optionally use `parallel-cli search` for scoping, then test database queries against known eligible reports','1. **Pilot the question**: Use native retrieval for scoping and test database queries against known eligible reports').replace('4. **Document everything**: Search strings, dates, result counts for reproducibility — save all parallel-cli output to `sources/`','4. **Document everything**: Preserve query strings, dates, raw exports, source locators and result counts in `sources/`.')
   if file.name=='search_and_citation.md':
    begin=doc.index('## Supplementary web search');end=doc.index('## Citation chaining',begin);doc=doc[:begin]+'## Supplementary native retrieval\n\nUse existing native primary-source retrieval for scoped discovery. Preserve query, date, source locator, raw exports, extraction state and missing pages. Ranked or truncated results are not an exhaustive corpus or proof of full-text assessment.\n\n'+doc[end:]
   doc=no_parallel(doc);file.write_text(doc)
  text=p.read_text();text=text.replace('## Dependencies','Use native primary-source retrieval for scoping and supplementary discovery, preserving query, date, response state, source locator, raw exports and incomplete coverage. Ranked excerpts never establish full-text access or a complete corpus.\n\n## Dependencies')
  generator=out/'scripts/generate_schematic.py'
  if generator.exists():generator.unlink()  # Disposable staging copy; original pinned source remains intact.
 elif name=='uncertainty-and-units':
  text+='\n## Acceptance boundary for a GUM claim\n\nThe local helpers are bounded numerical/static checks. Preserve covariance, the input distributions, model validity and the unit frame. A GUM-validation claim additionally needs study-specific Monte Carlo/numerical convergence and model evidence; a passing helper alone is insufficient.\n'
 elif name in ('hypothesis-generation','experimental-design','statistical-power'):
  text+='\n## Scoped study handoff\n\nCarry the independent unit, estimand, rival predictions, outcome-exposure history, randomization and preregistration state into the next selected procedure. Choose a study-specific seed and archive the actual allocation/design, environment and accepted input hashes. Power simulation must retain failed-run denominators and a Monte Carlo interval; do not convert a completed helper into a finding or retention claim.\n'
 elif name=='citation-management':
  text+='\n## Separate citation checks\n\nTreat identifier registration, metadata agreement and support for the manuscript claim as three distinct checks. Reopen the primary source and cite the actual supporting passage/record; matching a DOI or title does not prove the claim.\n'
 elif name=='lab-hardware-cad':
  text+='\n## Target standards and fabrication evidence\n\nReverify dated standards and vendor drawings for the actual target. Preserve editable build123d source, dimensions/units, interfaces, clearance assumptions, part/export hashes and a reopened STEP/STL/DXF. A lookup or successful export alone does not establish physical fit or fabrication safety.\n'
 elif name=='scientific-writing':
  text+='\n## Accepted evidence revision\n\nBind every consequential claim/table/figure to the actual source row or field, units, producing revision and raw evidence hash. Verify current reporting requirements for the target; reject stale outputs after a correction and preserve editable source. This is the single general manuscript leaf, not a reason to activate unrelated writing or diagram collections.\n'
 elif name=='peer-review':
  text+='\n## Review boundary\n\nUse only the authorized manuscript and current venue policy. Keep confidential reviewer notes separate from author-facing comments. Do not send manuscript content to external services by default. Source-backed concerns, contrary evidence, uncertainty and an actionable remedy belong in the review.\n'
 elif name=='qiskit':
  text=text.replace('## IBM QPU Sampling','## IBM QPU Sampling (separately authorized target only)').replace('## IBM QPU Estimation','## IBM QPU Estimation (separately authorized target only)')
  text+='\n## Source-to-joint-result acceptance\n\nLocal simulation is the default. Remote jobs, sessions/batches and hardware access need a task-specific authorized backend/account, budget and scope before submission. Persist shot-aligned arrays, explicit register/bit order, circuit/layout and target/noise metadata. Test asymmetric mappings and joint probabilities against a local oracle; per-register marginals lose correlation. Apply layouts to observables before execution and keep shot uncertainty explicit.\n'
 elif name=='pennylane':
  text=text.replace('then select a current accessible hardware backend and execution budget.', 'then keep local results unless the task separately authorizes a named hardware backend and execution budget.')
  text+='\n## Backend and oracle boundary\n\nKeep the QNode separate from its backend. Compare against the appropriate classical sector/oracle, verify analytic gradients before finite-shot/noisy checks, and retain register/measurement conventions. Provider plugins and hardware require separate task-specific access, scope and acceptance.\n'
 # A scientific method does not authorize automatic sibling collection installation.
 text+='\nUse this leaf only for its concrete scientific deliverable. Other named skills/runtimes remain independently admitted and activated; a related-source mention is not installation authority.\n'
 p.write_text(text)
