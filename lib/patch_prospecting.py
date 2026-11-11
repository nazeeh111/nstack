"""Source-preserving port of P343's selected eight-file research/draft closure."""
import difflib, hashlib, json, pathlib, re, shutil
P = pathlib.Path
FILES = ['skills/prospecting/SKILL.md','skills/cold-email/SKILL.md','skills/prospecting/references/demand-signals.md','skills/prospecting/references/account-research.md','skills/cold-email/references/personalization.md','skills/cold-email/references/reply-handling.md','skills/revops/references/lifecycle-definitions.md','skills/sales-enablement/references/win-loss-analysis.md']
BOUNDARY = '''## Native scope

Use existing project context and source-backed professional evidence. This selected port researches accounts and prepares only explicitly requested drafts or reply classifications. No provider setup, enrichment, sending, scheduling, booking or CRM write follows from this guide. A public signal or address grants no contact permission; any separate effect belongs to its authorized owner. Keep observations, inference, source/date, uncertainty and counterevidence separate. Neutral evidence rows are the default; scoring needs project-calibrated criteria. Reuse supplied context and ask only for material missing information.

'''

def cut(text, a, b=None, replacement=''):
    start = text.index(a); end = text.index(b, start + len(a)) if b else len(text)
    return text[:start] + replacement + text[end:]

def section(text, heading, replacement=''):
    start = text.index(heading); m = re.search(r'(?m)^## ', text[start + len(heading):])
    end = start + len(heading) + m.start() if m else len(text)
    return text[:start] + replacement.rstrip() + '\n\n' + text[end:]

def line(text, prefix, replacement):
    result, count = re.subn(r'(?m)^' + re.escape(prefix) + r'.*$', lambda _: replacement, text)
    if count != 1: raise ValueError('P343 source anchor changed: ' + prefix)
    return result

def port(rel, text):
    if rel == FILES[0]:
        text = re.sub(r'(?m)^description:.*$', 'description: Read-only shortlist of named accounts or first-customer demand evidence. No contact or enrichment action.', text, count=1)
        text = line(text, 'You are an expert', 'Use the source research phases below to turn an account profile or demand question into a source-backed research shortlist. Contact details are optional; research is not an outreach-ready recipient list.')
        text = cut(text, 'For the branch-specific deep dives:', '---', 'For demand evidence use [demand signals](references/demand-signals.md); for individual accounts use [account research](references/account-research.md).\n\n')
        text = line(text, 'If `.agents/product-marketing.md`', 'Use the existing project brief before asking for context.')
        text = line(text, '- **SaaS / B2B**: combine', '- **SaaS / B2B**: cross-check eligible professional company pages, job posts, filings and public announcements. Record source/date and uncertainties.')
        text = line(text, 'For LinkedIn audiences,', 'Use only already eligible sources within the task scope; no contact database, provider setup or enrichment step is required.')
        text = line(text, 'For email contacts (B2B / SaaS branches)', 'Contact information is optional in a research brief. Deliverability and recipient eligibility belong to a separately authorized delivery owner, not research qualification.')
        text = line(text, 'Apply this rubric for', 'The original Hot/Warm/Cold rubric below is a qualitative example, not a calibrated prediction. Use it only if the task supplies supported project criteria; otherwise report neutral fit evidence and uncertainty. Demand signals are assessed separately.')
        text = text.replace(' + verified contact |', ' |').replace(' + contact verifiable |', ' |').replace(' OR contact unverified |', ' |')
        text = line(text, 'Branch-specific signals refine', 'Keep the fit evidence and contrary evidence visible; no fixed Hot/Warm/Cold ratio is a target.')
        text = line(text, 'Then assign an **account tier**', 'Choose research depth using [account research](references/account-research.md): attributable account brief, segment plus account observation, or segment-only brief. Depth does not confer channel or cadence authority.')
        text = line(text, 'After the table, always add', 'After the table, identify the strongest evidence-backed accounts and the next research check; do not write openers unless requested.')
        text = line(text, '- score, business/company name', '- business/company identity, relevant observation, source/date, fit hypothesis, counterevidence, confidence and unknowns; contact fields only when supplied and eligible')
        text = section(text, '## Compliance Guardrails', '''## Source eligibility

Use eligible dated professional sources. Do not bypass access controls or use breached/unprovenanced data. Retain source lineage and source-use limits; a visible page or contact string does not establish database reuse or recipient permission. Exclude sensitive personal targeting. The route owner checks current primary provider terms and applicable permission before any separately requested use.''')
        text = section(text, '## Enrichment Workflows')
        text = section(text, '## Tool Selection Quick Picks')
        text = line(text, '- **Tools the user has access to**', '- **Available eligible sources** — use existing native tools; no provider registration or acquisition is required')
        text = line(text, '- **Target count**', '- **Target count** — use the requested scope; explain when evidence supports fewer matches')
        text = line(text, '- **Top outreach targets**', '- **Strongest evidence-backed accounts**: fit rationale, uncertainty and next research check')
        text = line(text, '- [ ] Every "Hot"', '- [ ] Every fit judgment has source-backed criteria and explicit unknowns')
        text = line(text, '- [ ] No lead has an email', '- [ ] Optional contact fields are attributed; missing addresses do not exclude otherwise useful research')
        text = line(text, '- [ ] No lead labeled "Hot"', '- [ ] Separate observed signals from inferred demand, budget or intent')
        text = line(text, '3. **Adding contacts without', '3. **Treating an address as research or sending permission.** Retain the source and leave recipient eligibility to the delivery owner.')
        text = line(text, '8. **Ignoring quiet hours', '8. **Converting research into an unrequested outreach plan.** Return evidence unless a draft was requested.')
        text = line(text, '4. What tools do you have access to', '4. Which eligible sources are already available?')
        text = cut(text, '## Tool Integrations', replacement='')
        text += '\nSupporting outcome references: [outbound stages](../revops/references/lifecycle-definitions.md) and [win/loss learning](../sales-enablement/references/win-loss-analysis.md).\n'
        # These branch labels describe source categories, not provider acquisition routes.
        text = text.replace('LinkedIn, BuiltWith, Crunchbase, Apollo, Clay, ProductHunt', 'Eligible company pages, job posts and public announcements').replace('Apollo, ZoomInfo, Clay, LinkedIn Sales Nav, industry directories', 'Eligible business pages, filings and industry directories').replace('(via last30days, social-fetch, scraping)', '(through existing native source-reading tools)')
    elif rel == FILES[1]:
        text = re.sub(r'(?m)^description:.*$', 'description: Prepare an explicitly requested reviewable email draft or reply classification from approved offer and proof. No sending or campaign actions.', text, count=1)
        text = cut(text, '**Check for product marketing context first:', '## Writing Principles', 'Use the existing project context, approved offer/proof and intended reader. Ask only for missing facts that materially affect the requested draft.\n\n')
        text = line(text, 'Interest-based CTAs', 'Use one low-friction question suited to this reader; the examples are copy choices, not evidence of a universal conversion advantage.')
        text = line(text, 'For the full catalog of frameworks', 'Choose among the source shapes above, or write freeform when it flows naturally. State only source-supported problems and proof; an observation is not evidence of pain.')
        text = line(text, 'See [subject-lines.md]', 'Treat these subject-line suggestions as starting points subordinate to the actual voice and context.')
        for heading in ['## Follow-Up Sequences','## Before You Send','## Beyond Email','## Data & Benchmarks','## Tool Integrations','## Related Skills']:
            text = section(text, heading)
        text = section(text, '## When They Reply', '## When They Reply\n\nClassify the actual reply and prepare the proposed owner response using [reply handling](references/reply-handling.md). No reply, booking or reminder is sent by this leaf.')
        text = text.replace('  - For the full blacklist, use the **copywriting** skill\'s AI-tells reference\n', '')
    elif rel == FILES[2]:
        text = text.replace('in SKILL.md', 'in [the account entry](../SKILL.md)').replace('(see SKILL.md)', '(see [the account entry](../SKILL.md))')
        text = line(text, 'Don\'t start broad collection', 'Use the existing approved project brief; clarify material gaps before collecting unrelated evidence.')
        text = line(text, 'Search several angles,', 'Search several angles rather than one query repeated; use the audience\'s own professional vocabulary from eligible source evidence.')
        text = cut(text, '**Use our live-recency edge.**', '## Step 3', 'Read original pages with existing native tools; snippets alone do not establish a match. Record the actual event and observation dates.\n\n')
        a = text.index('## Step 4'); b = text.index('### Prospect stages', a)
        dimensions = text[text.index('| **Pain strength**', a):text.index('\n\n```', a)]
        dimensions = re.sub(r'\| \d+% \|', '|', dimensions)
        text = text[:a] + '## Step 4 — Assess demand fit\n\nKeep these original evidence dimensions separate. Numeric scores or bands require project-calibrated criteria; neutral evidence is the default. Public reachability is an observed channel, not contact permission.\n\n| Dimension | What it measures |\n|---|---|\n' + dimensions + '\n\n' + text[b:]
        text = text.replace('score breakdown', 'dimension evidence and uncertainty').replace('An evidence report + manual outreach plan', 'An evidence report; draft only if requested').replace('None — reach them where they already posted', 'No contact operation; retain the original source')
        text = section(text, '## Step 5', '''## Step 5 — Requested draft handoff

Research alone ends with evidence. Only when a draft is requested, retain the source opener shape: (1) mention the actual public professional context, (2) connect it to the evidenced problem, (3) explain the approved product in one sentence, (4) ask one low-friction question. Do not fabricate familiarity, pain or personal details. Return the draft for review; never send it.''')
        text = text.replace('demand-fit score, stage, why-now, channel, opener', 'dimension evidence, stage, why-now, uncertainty; include an opener only if requested')
        text = line(text, '6. **Seven-day manual outreach plan**', '6. **Next research check** — what observation would discriminate a real match from speculative fit?')
        text = line(text, 'For a shareable standalone HTML version', 'Use the requested output format through the normal artifact owner.')
    elif rel == FILES[3]:
        text = text.replace('Dossiers on companies you compete with belong to the competitor-profiling skill.', 'Competitor dossiers are outside this selected account-research leaf.')
        text = line(text, 'Tiers are defined in', 'These tiers budget research depth only: an attributable account brief, a segment-plus-observation brief, or a segment-only brief. They confer no channel, cadence or contact permission.')
        text = text.replace('See [compliance.md](compliance.md).', 'The route owner checks current permissions and primary source terms before a separately requested use.')
        text = text.replace('**Likely priority:** [the problem the signal implies, in their words where possible]', '**Fit hypothesis:** [possible relevance, distinct from observed need/budget; include contrary evidence]')
    elif rel == FILES[4]:
        text = line(text, 'Personalization drives', 'The useful source principle: personalization must connect to the problem and approved offer; decorative personal facts are not relevance.')
        text = text.replace(' ~5% lift.', '').replace(' (gold standard)', '')
        text = text.replace('## The 3-Minute Personalization System', '## Reusable Personalization System')
        text = line(text, 'The personalization must logically', 'The personalization must logically connect to the evidenced problem. Reusable triggers reduce repeated drafting; no fixed research-time promise is established.')
        text = section(text, '## The Four -Graphic Principles', '''## Professional dimensions

Use relevant professional role, attributable firmographic facts and verified technology context. Exclude sensitive traits and psychographic/personal-life targeting. Do not infer team size, budget or pain from a sparse signal.''')
        text = text.replace('## Observation-Based Openers (highest performing)', '## Observation-Based Openers')
        text += '\nFor source/date, facts-before-angle and no-hook rules, read [account research](../../prospecting/references/account-research.md). The example claims above are placeholders: replace with attributable facts, omit unsupported implications and use only approved proof.\n'
    elif rel == FILES[5]:
        text = line(text, 'The sequence\'s job ends', 'Classify supplied replies and prepare a proposed owner response. The actions below are handoff options, not execution authority.')
        text = text.replace('| Action |', '| Proposed owner action |')
        text = text.replace('Thank them, set a reminder for the date they gave, stop the sequence', 'Record the requested date and local hold; owner reviews any acknowledgement or later contact')
        text = text.replace('Thank them; contact Sam citing the referral (with permission to use their name if unclear)', 'Record an unverified research lead; no inherited send authority; owner reviews any proposed draft')
        text = text.replace('Pause; resume after their return date. Note any named stand-in', 'Pause without automatic resumption; note the return date/stand-in for owner review')
        text = text.replace('Suppress on every channel immediately. Apologize briefly if you reply at all. Never argue', 'Suppress the recipient locally; authorized owner verifies remote suppression. Account-wide halt is separate; any reply needs authority')
        text = text.replace('Remove; check whether the contact moved companies (a possible job-change signal)', 'Mark the address invalid and stop retries; any further research uses an eligible source')
        text = text.replace('Record the event and hold pending work locally.', 'Record the event and hold pending work locally. Unknown provider outcomes remain held until reconciled; a local pause does not stop a remote campaign.')
        text = line(text, 'Every reply of any type', 'Record the event and hold pending work locally. Unknown provider outcomes remain held until reconciled; a local pause does not stop a remote campaign. The authorized effect owner must apply and read back remote suppression/pause; recipient opt-out and account-wide halt have distinct scope.')
        text = section(text, '## Speed', '## Ownership\n\nName the actual response owner and preserve the request\'s urgency. No fixed response SLA, notification or autonomous contact is created.')
        text = section(text, '## Booking', '## Booking handoff\n\nIf requested, prepare a proposal in the reader\'s time zone with a clear agenda. Sending invitations, reminders, follow-ups or rescheduling requires the actual owner\'s separate authority.')
        text = section(text, '## What an agent can handle', '## Agent handoff\n\nReturn classification, proposed draft, stop state and unknowns. No numerical reply-count threshold grants autonomous sending authority. Referrals do not inherit recipient permission; out-of-office dates do not automatically resume a sequence.')
        text = line(text, 'Record on the CRM contact:', 'Record in the existing project handoff: reply type/date, account/recipient and message identity, source sequence/step if supplied, channel, proposed owner action and actual outcome evidence. CRM changes are separate authorized effects; unknown outcomes remain held until reconciled.')
    elif rel == FILES[6]:
        text = text[text.index('## Outbound Stages'):]
        text = text.replace('Added to an outbound list: fit checked, email verified, tier assigned', 'Research evidence recorded; contact fields optional').replace('Enrolled in a sequence, or skipped', 'Separate authorized owner accepts handoff, or skipped').replace('Classified within one business day', 'Classified from the actual reply').replace('Meeting booked, or gone quiet for 14 days', 'Accepted booking, declined, or unknown').replace('Reminder date reached → back to Targeted', 'Owner reviews new permission and context; no automatic resumption')
        text = line(text, '**Handoff SLA:**', '**Outcome evidence:** Distinguish provider acceptance from delivery, genuine reply from automatic response, positive interest from accepted booking, held meeting from no-show, and opportunity from realized revenue. Stage labels and source history do not authorize effects.')
        text = text.replace('Qualified (same definition as inbound)', 'Qualified against the owning project’s explicit source-backed criteria; label alone is insufficient')
        text = text.replace('| **In sequence** | First touch sent |', '| **Contacted** | Authoritative receipt for a separately authorized first touch; delivery distinct |')
    elif rel == FILES[7]:
        text = line(text, 'Ask within 2-4 weeks', 'For separately authorized interviews, the source suggests asking soon after the decision and using someone other than the deal rep. Existing interview evidence can be analyzed without initiating contact.')
        text = line(text, '- **Under ~5 deals', '- **Small slices remain uncertain.** No fixed sample-size threshold validates a finding; preserve denominators and competing explanations.')
        text += '\nAsset destinations above are proposed owner handoffs, not permission to change product, CRM or sales materials. Preserve buyer-stated reasons separately from team inference.\n'
    else: raise ValueError('Unselected P343 file')
    # Native scope applies even when a supporting reference is loaded directly.
    if text.startswith('---\n'):
        end = text.index('\n---\n', 4) + 5
        text = text[:end] + '\n' + BOUNDARY + text[end:]
    else: text = BOUNDARY + text
    return text.rstrip() + '\n'

def materialize(source, out, s):
    if 'Copyright (c) 2025 Corey Haines' not in (source/'LICENSE').read_text(): raise ValueError('P343 required MIT notice changed')
    records=[]
    for rel in FILES:
        src=source/rel
        if not src.is_file(): raise ValueError('P343 scoped source missing: '+rel)
        raw=src.read_bytes();adapted=port(rel,raw.decode());dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(adapted)
        archive=out/'upstream'/P(rel).with_suffix('.reference.txt');archive.parent.mkdir(parents=True,exist_ok=True);archive.write_bytes(raw)
        diffpath=P('patches')/P(rel).with_suffix('.patch');diff=out/diffpath;diff.parent.mkdir(parents=True,exist_ok=True);diff.write_text(''.join(difflib.unified_diff(raw.decode().splitlines(True),adapted.splitlines(True),fromfile=rel,tofile=rel)))
        records.append({'source_path':rel,'source_sha256':hashlib.sha256(raw).hexdigest(),'archive':str(archive.relative_to(out)),'active_path':rel,'active_sha256':hashlib.sha256(adapted.encode()).hexdigest(),'diff':str(diffpath)})
    shutil.copy2(source/'LICENSE',out/'LICENSE')
    (out/'SOURCE-ADAPTATION.json').write_text(json.dumps({'repository':s['source_repository'],'revision':s['revision'],'scope':'Exactly the eight selected research/draft files; excluded provider/channel playbooks remain excluded. Source methods retained within that scope.','files':records},sort_keys=True,indent=2)+'\n')
    return str(P(s['source_path']).parent)
