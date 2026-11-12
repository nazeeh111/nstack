# On-demand LangSmith

LangSmith SDK 0.14.17 is already hash-pinned in the shared LangChain/LangGraph runtime. No extra image, daemon or Python environment is needed. This integration registers a discoverable runtime entry for Codex and OpenCode and supplies a local example. It does not install a replacement host harness or copy upstream skills into custom versions.

After commissioning the existing AI workflow runtime:

```sh
python3 recipes/langsmith.py install
python3 recipes/langsmith.py check
```

The check executes a real LangGraph node inside a LangSmith `traceable` workflow using `tracing_context(enabled="local")`. It saves the nested trace and deterministic evaluation to `langsmith-local.json` in its unique private run directory. The correct result must pass and a wrong result must fail. The existing wrapper enforces no network, no credentials, a read-only root, bounded resources and no host-project mount for this check. It makes no inference calls and uploads nothing. Repeat installation preserves the same runtime entry without changing unrelated records.

Use the SDK in an explicitly selected application project when inspecting nested execution, comparing outputs or building evaluations will help. Keep the application's code and test data in that project. The normal AI-workflow `run --project ... --script ...` interface remains offline, with global hosted tracing disabled.

Hosted traces, remote datasets/experiments, model judges and deployment need a separately selected LangSmith account/workspace, approved data and destination, secure project-specific credentials and any required spending authority. Do not infer these from installing the SDK. Do not read credential stores, put keys on command lines, enable tracing globally or send product feedback without authorization. Select LangSmith or Langfuse according to the application rather than enabling both by default.

Primary sources: [SDK](https://github.com/langchain-ai/langsmith-sdk), [local tracing behavior](https://github.com/langchain-ai/langsmith-sdk/blob/main/python/tests/unit_tests/test_run_helpers.py), [evaluation](https://docs.langchain.com/langsmith/evaluation), [observability](https://docs.langchain.com/langsmith/observability). The executable example was tested against the pinned installed SDK; current upstream documentation may describe newer versions. Official [LangSmith skills](https://github.com/langchain-ai/langsmith-skills) additionally assume their CLI/account prerequisites and are not installed by this SDK integration.
