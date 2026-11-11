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

Use 2–8 candidates and 1–4 critics. These are packet-size bounds, not required
team sizes. Origins are caller declarations, never verified model identity.
Evidence is an optional list of sourced snippets; an empty list supplies no
external evidence. No retrieval occurs. Include the source/revision with each
snippet. Unknown fields are refused rather than silently discarding sources.
The output directory must be new. Files are private to the local user. No
network request, environment variable lookup, key read or model call occurs.

The private manifest binds the input and packet hashes and maps opaque response
labels to candidate IDs. Share only individual `packets/*.json` files with
critics. Forward and reverse packets require fresh contexts to avoid anchoring.
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
Different forward/reverse preferences can reflect order or stochastic
variation; they do not alone prove its cause. More agreement is not external
validation. No candidate is automatically approved or promoted.

The helper blinds declared metadata, not identifying prose. It does not enforce
critic filesystem isolation, check factual truth, audit provider billing or
certify that critics were independent. Keep those observations in the task's
existing evidence record.
