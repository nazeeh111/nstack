"""P112 paper-lookup corrections, preserving bounded parsers and count reconciliation."""
import pathlib,re
P=pathlib.Path

def replace(text,old,new):
 if old not in text:raise ValueError('Paper-lookup source anchor missing: '+old[:70])
 return text.replace(old,new)

PREDICATE='''def has_substantive_body(body: ET.Element) -> bool:
    """Reading text, excluding headings/non-reading tags and the body's outer tail."""
    def content(node: ET.Element) -> str:
        if node.tag in SKIP_TAGS or node.tag == "title":
            return ""
        parts = [node.text or ""]
        for child in node:
            parts.extend((content(child), child.tail or ""))
        return "".join(parts)
    return any(char.isalnum() for char in content(body))


def audit_context(args: Any, digest: str, full: bool) -> dict[str, Any]:
    import urllib.parse
    locator = redact_url(args.source_locator) if args.source_locator else None
    query = urllib.parse.urlsplit(redact_url("https://query.invalid/?" + args.query)).query if args.query else None
    return {
        "input_sha256": digest,
        "access_level": "substantive_body_text_present_completeness_unverified" if full else "metadata_only",
        "retrieval": {"source_locator": locator, "query": query, "retrieved_at": args.retrieved_at,
                      "basis": "caller-supplied; not inferred from XML"},
        "source_span": {"article": "first article element", "body": "./body" if full else None,
                        "section_selectors": ["./body/sec[%d]" % i for i in getattr(args, "source_sections", [])],
                        "selector_basis": "structural paths relative to the first article; not byte offsets"},
    }


'''

def patch(out):
 scripts=out/'scripts';p=scripts/'_common.py';text=p.read_text();text=replace(text,'import json\n','import json\nimport hashlib\n')
 text=replace(text,'def read_input(source: str, *, max_bytes: int = MAX_INPUT_BYTES) -> str:', 'def read_input(source: str, *, max_bytes: int = MAX_INPUT_BYTES, with_sha256: bool = False) -> str | tuple[str, str]:')
 text=replace(text,'    return raw.decode("utf-8", errors="replace")','    decoded = raw.decode("utf-8", errors="replace")\n    return (decoded, hashlib.sha256(raw).hexdigest()) if with_sha256 else decoded')
 text=replace(text,'    stopped_at_limit: bool = False','    stopped_at_limit: bool = False\n    stopped_for_repetition: bool = False')
 text=replace(text,'        if self.stopped_at_limit:\n            return False','        if self.stopped_at_limit or self.stopped_for_repetition:\n            return False')
 text=replace(text,'return self.complete or self.stopped_at_limit','return not self.stopped_for_repetition and (self.complete or self.stopped_at_limit)')
 text=replace(text,'            "stopped_at_limit": self.stopped_at_limit,','            "stopped_at_limit": self.stopped_at_limit,\n            "stopped_for_repetition": self.stopped_for_repetition,')
 text=replace(text,'        if self.notes:\n            summary["notes"]', '        if self.stopped_for_repetition:\n            summary["incomplete_reason"] = "repeated cursor or nonempty page; duplicate page records were not counted"\n        if self.notes:\n            summary["notes"]')
 p.write_text(text)
 p=scripts/'jats_to_text.py';text=p.read_text();text=replace(text,'from _common import InputError, collapse_ws, emit, fail, read_input','from _common import InputError, collapse_ws, emit, fail, read_input, redact_url')
 text=replace(text,'def section_title(section: ET.Element) -> str:',PREDICATE+'def section_title(section: ET.Element) -> str:')
 text=replace(text,'    for section in top_level:\n        sections.append(', '    for section in top_level:\n        if not has_substantive_body(section):\n            continue\n        sections.append(')
 text=replace(text,'    return sections\n\n\n#: JATS', '    if not sections and has_substantive_body(body):\n        text = element_text(body)\n        return [{"title": "", "sec_type": None, "text": text}]\n    return sections\n\n\n#: JATS')
 text=replace(text,'        "abstract": None,','        "abstract": None,\n        "rights": {"status": "unknown", "licenses": []},')
 text=replace(text,'    if front is None:\n        return metadata', '''    if front is not None:
        for node in front.findall(".//permissions/license"):
            stated = collapse_ws("".join(node.itertext()))
            link = node.get("{http://www.w3.org/1999/xlink}href") or node.get("href")
            if not link:
                ext = node.find(".//ext-link")
                if ext is not None:
                    link = ext.get("{http://www.w3.org/1999/xlink}href") or ext.get("href")
            metadata["rights"]["licenses"].append({"text": stated, "url": redact_url(link) if link else None,
                                                        "type": node.get("license-type")})
            if stated or link:
                metadata["rights"]["status"] = "stated_not_independently_verified"
    if front is None:
        return metadata''')
 text=replace(text,'    return parser\n\n\ndef matches', '    parser.add_argument("--source-locator", help="caller-supplied source URL; sensitive query fields are redacted")\n    parser.add_argument("--query", help="caller-supplied API query parameters; sensitive fields are redacted")\n    parser.add_argument("--retrieved-at", help="caller-supplied retrieval time, never inferred from article dates")\n    return parser\n\n\ndef matches')
 text=replace(text,'        xml_text = read_input(args.source)', '        xml_text, input_digest = read_input(args.source, with_sha256=True)')
 text=replace(text,'    if body is None:\n        comments', '    if body is None or not has_substantive_body(body):\n        comments')
 text=replace(text,'"document has no <body> element and gave no stated reason"','"document has no substantive body reading text and gave no stated reason"')
 text=replace(text,'            "full_text_available": False,','            "full_text_available": False,\n            "provenance": audit_context(args, input_digest, False),')
 text=replace(text,'"no <body> element: this document is metadata only, not full text"','"no substantive body reading text: this document is metadata only, not full text"')
 text=replace(text,'    if args.text_only:\n        blocks', '    args.source_sections = [i for i, node in enumerate(body.findall("sec"), 1) if has_substantive_body(node) and (not args.sections or matches({"title": section_title(node), "sec_type": node.get("sec-type")}, wanted))]\n    if args.text_only:\n        blocks')
 text=replace(text,'            "full_text_available": True,','            "full_text_available": True,\n            "provenance": audit_context(args, input_digest, True),')
 text=text.replace('when there is no `<body>`','when there is no substantive body reading text').replace('carries no <body>,','carries no substantive body reading text,').replace('when there is no <body>.','when no substantive body reading text is present.')
 p.write_text(text)
 p=scripts/'paginate.py';text=p.read_text();text=replace(text,'import argparse\n','import argparse\nimport hashlib\n')
 text=replace(text,'    if key:\n        params["api_key"] = key\n    return base + urllib.parse.urlencode(params)', '    if not key or not key.strip():\n        raise RuntimeError("OpenAlex cursor pagination requires a nonblank OPENALEX_API_KEY supplied through the runtime environment; no keyless cursor request was made")\n    params["api_key"] = key.strip()\n    return base + urllib.parse.urlencode(params)')
 text=replace(text,'    seen_notes: set[str] = set()','    seen_notes: set[str] = set()\n    seen_states: set[str] = set()\n    seen_pages: set[str] = set()')
 text=replace(text,'        remaining = max_records - len(records)', '''        state_digest = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()
        if state_digest in seen_states:
            reconciliation.stopped_for_repetition = True
            reconciliation.note("repeated cursor/state; stopped INCOMPLETE before another fetch")
            break
        seen_states.add(state_digest)
        remaining = max_records - len(records)''')
 text=replace(text,'        records.extend(page.records)', '''        page_digest = hashlib.sha256(json.dumps(page.records, sort_keys=True).encode()).hexdigest()
        if page.records and page_digest in seen_pages:
            reconciliation.stopped_for_repetition = True
            reconciliation.note("repeated nonempty page; stopped INCOMPLETE without recounting duplicate page records")
            break
        if page.records:
            seen_pages.add(page_digest)
        records.extend(page.records)''')
 text=replace(text,'    if not reconciliation.ok:\n', '    if reconciliation.stopped_for_repetition:\n        fail("pagination stopped on a repeated cursor/page; retained records are incomplete and duplicate pages were not counted", code=4)\n    if not reconciliation.ok:\n')
 # Clarify the source's broad authentication claim without asserting live entitlement or pricing.
 text=replace(text,'Needs network access. No credentials required for bioRxiv, medRxiv, Europe PMC,\nCrossref, or OpenAlex; OPENALEX_API_KEY raises the OpenAlex daily budget.', 'Needs network access. OpenAlex cursor pagination requires a nonblank runtime key.\nOther endpoints have their own currently permitted access and cost prerequisites; no current entitlement or price is established by this source.')
 p.write_text(text)
 for file in out.rglob('*.md'):
  text=file.read_text()
  if '## Citing Scientific Agent Skills' in text:text=text[:text.index('## Citing Scientific Agent Skills')].rstrip()+'\n'
  text=re.sub(r'(?m)^allowed-tools:.*\n','',text)
  if file.name=='SKILL.md':
   text=re.sub(r'(?m)^compatibility:.*$', 'compatibility: Standard-library local parsers need Python 3.11+. API retrieval needs its current permitted access; OpenAlex cursor pagination requires a nonblank OPENALEX_API_KEY supplied through the runtime environment. Key presence does not establish free entitlement or publication rights.',text)
   text=text.replace('| OpenAlex | `OPENALEX_API_KEY` | Recommended |', '| OpenAlex | `OPENALEX_API_KEY` | Required for cursor pagination |')
   text=re.sub(r'(?m)^\*\*Loading keys:\*\*.*$', '**Runtime access:** Use only the supported task runtime environment or native account connection. Do not inspect credential stores or open .env files. OpenAlex cursor pagination requires its runtime key; missing-key fallback must use separately verified targeted access or another eligible source. No current paid or free entitlement is inferred.',text)
   text+='\n## Correct access and provenance\n\nOpenAlex cursor pagination requires the stated runtime key before any request. Missing-key fallback must use a separately verified targeted lookup or another eligible source; it must not silently run a keyless cursor walk. Repeated pages/cursors stop as incomplete without recounting their records. Verify current access and costs before commissioning an API lane.\n\nThe JATS parser requires substantive reading-order body text; absent, empty, heading-only and excluded-content-only bodies remain metadata-only even with HTTP200. `--allow-metadata-only` changes exit status, never the access label. A missing requested section is a distinct selection error. Preserve article license text/URL when supplied; missing rights remain unknown. Supply the actual query, redacted source locator and retrieval time with the optional provenance flags; the parser records input hash and structural source spans and does not invent retrieval history.\n'
  if file.name=='openalex.md':
   # Replace outdated keyless/general-key claims with a scoped, current-access boundary.
   text=re.sub(r'(?im)^.*(?:key.*(?:optional|recommended)|(?:no|without).*key).*(?:\n|$)', 'OpenAlex cursor pagination requires the supported runtime key; targeted lookup access must be verified separately.\n',text)
   text=text.replace('| `cursor` | -- | Use `*` for first page of deep pagination |','| `cursor` | -- | Requires the runtime API key; use `*` for the first cursor page |').replace('GET /works?filter=publication_year:2024&cursor=*&per_page=100','GET /works?filter=publication_year:2024&cursor=*&per_page=100&api_key=RUNTIME_KEY')
   text='Provider syntax, limits and price figures below are a dated source snapshot. Verify current primary terms and task access/cost authorization at commissioning; none is established by installing this guide.\n\n'+text
   text+='\n## nstack cursor prerequisite\n\nBefore a cursor walk, supply a nonblank OPENALEX_API_KEY through the runtime environment. No keyless cursor fallback is enabled. Do not infer current live entitlement, quota or pricing from an inspected source or key presence. Retain redacted URLs, page/record counts, repetition guards and explicit incomplete reasons.\n'
  file.write_text(text)
