# Original LLM Council application

Reviewed source: [karpathy/llm-council at 92e1fcc](https://github.com/karpathy/llm-council/tree/92e1fccb1bdcf1bab7221aa9ed90f9dc72529131).
Its three stages collect answers, rank anonymously labeled answers and ask a
chair model to synthesize. This authored nstack method adds evidence checking,
reversed order, tie handling and explicit uncertainty about model diversity.

The reviewed upstream tree has no license file. Do not copy its implementation
into public nstack. A verified private source cache is inspection material, not
an activated model service.

The original app requires OpenRouter. Its first normal request can make four
proposal calls, four review calls, one synthesis call and one title call.
It supplies no total-spend ceiling. Its default model identifiers are older
than this review; availability must be checked before a live run. Existing
OpenCode OpenAI access is not an OpenRouter connection or spending authority.

Do not start its development server as a default integration. At this revision
it binds all interfaces, lacks application authentication, joins conversation
IDs into file paths without UUID validation and prints provider exceptions.
It writes conversation JSON in the current working directory. A real app
request needs scoped loopback/authentication/path/storage/error hardening,
private credentials outside the checkout and a bounded provider plan first.
Do not inspect credential stores or inherit keys into tests.

Upstream review uses the same candidate order for every judge, includes each
model's own answer, accepts incomplete/duplicate labels and reveals model
identities to the chair. Anonymized labels alone do not establish fair judging.
See [FairEval](https://arxiv.org/abs/2305.17926v2) and the
[position-bias study](https://arxiv.org/abs/2406.07791v9).
