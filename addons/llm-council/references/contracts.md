# Offline review contracts

`prepare` accepts one JSON file, at most 1 MiB:

```json
{
  "question": "Which proposal meets the supplied requirements?",
  "rubric": ["Correct calculations", "Supported assumptions"],
  "evidence": ["Source/revision and the relevant facts or excerpt shared by every critic"],
  "candidates": [
    {"id": "option-a", "text": "First complete proposal", "origin": "actual model or unknown"},
    {"id": "option-b", "text": "Second complete proposal", "origin": "actual model or unknown"}
  ],
  "judges": [{"id": "critic", "origin": "actual model or unknown"}]
}
```

Use 2–8 candidates. The default `"review_order": "paired"` accepts 1–4 critics
and produces forward/reverse packets per critic, each requiring a fresh context.
Omitting `review_order` preserves this default and existing version-1 manifests.
Explicit `"review_order": "balanced"` accepts 1–5 critics and produces one
rotated-order packet per critic, using a version-2 manifest. Five candidates
and five critics give every candidate exactly one appearance in each position.
Other counts can leave unequal position coverage; inspect the actual counts.
These are packet-size bounds, not required team sizes. The five-lens route uses
all five drafts and five fresh critics. Origins are declarations, never verified model identity.
Evidence is an optional list of sourced snippets; an empty list supplies no
external evidence. No retrieval occurs. Include the source/revision with each
snippet. Unknown fields are refused rather than silently discarding sources.
The output directory must be new. Files are private to the local user. No
network request, environment variable lookup, key read or model call occurs.

The private manifest binds the input and packet hashes and maps opaque response
labels to candidate IDs. Share only individual `packets/*.json` files with
critics. Forward and reverse packets require separate fresh contexts to avoid anchoring.
Balanced critics each get only one packet. A critic is never a retained author
context. Withholding metadata does not prevent style from revealing authorship.
Each critic returns one object; collect those objects as a JSON array:

```json
[
  {
    "packet_id": "p001",
    "ranking": [["R2"], ["R1"]],
    "reasons": {"R1": "Specific rubric-linked reason", "R2": "Specific rubric-linked reason"},
    "evidence_gaps": []
  }
]
```

Ranking groups run from best to worst. `[["R1", "R2"]]` is a tie. For an
abstention, tie all responses and explain the missing evidence. Every label
must appear exactly once, and every response needs a nonempty reason.
Reasons may also be lists of text or named text categories, allowing a critic
to separate supported, contradicted and unresolved claims without rewriting
its judgment. Empty subcategories are allowed; each response still needs text.

`summarize` verifies packet bytes, labels and judgment structure. A missing
judgment produces `state: incomplete`; duplicate or malformed judgments fail.
It reports mean ranks, ties, reasons, evidence gaps and order disagreements.
`review_order` and `order_coverage` identify the actual control. Coverage includes
planned and received per-candidate position counts, whether those counts are
balanced, and completed reversal comparisons. Balanced mode always reports
`within_reviewer_reversal: not_performed`: an empty `order_disagreements` list
cannot mean that a reversal check passed. Missing judgments reduce received
coverage even when the planned panel is perfectly balanced.
Different forward/reverse preferences can reflect order or stochastic
variation; they do not alone prove its cause. More agreement is not external
validation. No candidate is automatically approved or promoted.

The helper blinds declared metadata, not identifying prose. It does not enforce
critic filesystem isolation, check factual truth, audit provider billing or
certify that critics were independent. Keep those observations in the task's
existing evidence record.

Version-1 manifests retain their original fields and packet shape. Version 2
requires `review_order: balanced`, one `balanced` round per critic, consecutive
packet IDs and cyclic rotations. Version/mode/round mismatches, duplicate JSON
fields, unknown critics, missing/duplicate assignments and changed packet bytes
are rejected. These checks catch inconsistent artifacts; local hashes are not
authentication against an actor who can coherently rewrite the whole directory.
Keep the private manifest under the lead's ownership. A missing result is an
incomplete review, not an endorsement or fabricated replacement.
