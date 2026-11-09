"""Scoped marketing/audit/career ports; no delivery authority is inferred."""
import pathlib,re,shutil
P=pathlib.Path

def change(s,old,new):
 if old not in s:raise ValueError('Missing business port anchor: '+old[:90])
 return s.replace(old,new)
def patch(id,name,source,out):
 p=out/'SKILL.md';s=p.read_text()
 if id=='P343':
  s=s.replace('Use this at the start of any new project before using other marketing skills','Use this when the requested task actually needs a product brief and none exists')
  s=s.replace('Gather this context (ask if not provided):','Reuse the existing product brief and task evidence. Ask only for material missing facts; do not repeat covered context:')
  s=s.replace('State the diagnosis in one line with the evidence ("B: the draft argues against agencies in the founder\'s voice, uses \'ship\' and \'stuff\'") before writing.','Apply the appropriate edit scope from the supplied draft and brief. Do not impose a diagnosis ceremony or redundant questions when the task is clear.')
  if name=='pricing':
   s=change(s,'your cheapest customers churn most and complain loudest','retention and support burden must be measured for each actual cohort; price alone does not establish either outcome')
   ref=out/'references/pricing-models.md';t=ref.read_text();start=t.index('## The Low-Price Retention Counterpoint')
   t=t[:start]+'''## Price and retention hypotheses

Low price, discount requests and retention may be associated in a particular
market. Treat the source's claims about churn and a roughly twofold discount
effect as unverified hypotheses, not universal facts or a causal estimate.
Before using a number, obtain the primary study, date, sampled product/cohort,
assignment mechanism, exposure, denominator, follow-up horizon, missingness,
support costs and confounders. Compare the actual segments and contrary data.
No retention conclusion or automatic price increase follows from price alone.
Choose a reviewable test only within the user's existing experiment authority.
''';ref.write_text(t)
   s=change(s,'### The $10 / $100 / $1,000 rule of thumb','### Illustrative elicitation bands, not market evidence\n\nThe bands below are weak discussion prompts. They are not measured willingness to pay, a universal SaaS default or authority to change a live price. Validate the actual market, value metric, denominators and experiment before a decision.')
   s=s.replace('Pick a number, ship it, and let real buyers tell you if it\'s wrong.','Propose a testable price hypothesis and an explicitly authorized experiment; do not silently change or publish a live price.')
  s+='\n## Scope and evidence\n\nUse one existing product brief. Preserve separate pricing, acquisition, recruiting/interview and synthesis evidence; P346/L014 own interviews/synthesis. Do not install partner skills, send campaigns, publish copy, change prices or launch experiments from this leaf. Keep actual measured assignment/exposure/denominator/horizon/outcomes and guardrails distinct from suggestions. Existing explicit user authority controls any separate outbound action.\n'
 elif id=='P347':
  s=s.replace('${CLAUDE_PLUGIN_ROOT}','${NSTACK_SEO_ROOT}')
  if name=='seo-audit':
   start=s.index('4. **Delegate to subagents**');end=s.index('5. **Score**',start)
   s=s[:start]+'''4. **Bounded evidence review:** Use only the actual requested site scope and available data. Native inline work covers one page; independent bounded workers are optional for genuinely separable site-wide evidence. Do not install unselected companion skills, probe credential stores or spawn every platform. Preserve the chosen technical leaf and source references; report missing data explicitly.
'''+s[end:]
  s=re.sub(r'(?m)^.*(?:[Oo]ffer.*PDF|PDF.*[Oo]ffer).*$','Deliver the requested format; do not force an unsolicited PDF offer.',s)
  s+='\n## Native scope and measured acceptance\n\nSet NSTACK_SEO_ROOT to the absolute source-verified private package runtime root; never assume a Claude plugin installation. Select seo-technical first and seo-audit only for full-site work. Use measured-only scores with their date, source, denominator and missing-data status. No one-page fanout, automatic provider credential discovery, paid data API or publication. Current search behavior claims must be checked against owning primary sources before being represented as current fact.\n'
 elif id=='P351':
  s=change(s,'6. Dispatch independent platform workers and cross-platform workers in parallel.','6. Use bounded native workers only for actual independent evidence. A missing/data-less platform stays missing, not a worker invitation. Preserve user-selected models/effort and prevent overlapping artifact writes.')
  s=change(s,'Use a dedicated worker for every selected platform:','The following are source role references for platforms with actual data, not registered agents or an all-platform requirement:')
  s+='\n## Account audit boundary\n\nMap source exports to the retained canonical schemas and scoring helpers; preserve lineage, currency/timezone/date windows, missingness and scoring version. ads-math and audit remain separate selected leaves. Do not infer live account authority from an export. An audit is read-only; account changes need their specific existing authority and native permissions. No automatic per-platform team, paid API, budget/bid change, tracking edit, pause or launch. Preserve prior task authority without a ritual reconfirmation.\n'
 elif id=='P357':
  from patch_resume import materialize
  s=materialize(source,out)
 elif id=='P354':
  from patch_career import materialize
  s=materialize(source,out)
 else:raise ValueError('Business leaf is not mapped')
 p.write_text(s)
