"""Synthetic local LangGraph trace and deterministic evaluation; no hosted calls."""
import json
from pathlib import Path
from typing import TypedDict
from langsmith import traceable, tracing_context
from langgraph.graph import StateGraph, START, END

class State(TypedDict):
    value: int

@traceable
def double(state: State):
    return {"value": state["value"] * 2}

builder = StateGraph(State)
builder.add_node("double", double)
builder.add_edge(START, "double")
builder.add_edge("double", END)
graph = builder.compile()

@traceable
def workflow(value: int):
    return graph.invoke({"value": value})

def exact(actual, expected):
    return actual == expected

completed = []
with tracing_context(enabled="local"):
    result = workflow(6, langsmith_extra={"on_end": completed.append})
assert result == {"value": 12}
assert len(completed) == 1
root = completed[0]
assert root.outputs == {"value": 12} and root.child_runs
assert exact(result["value"], 12) and not exact(11, 12)

def render(run):
    return {"name": run.name, "inputs": run.inputs, "outputs": run.outputs,
            "children": [render(child) for child in run.child_runs]}

artifact = {"trace": render(root), "evaluation": {"correct": True, "wrong_answer_rejected": True},
            "result": result, "mode": "local", "hosted_upload": False}
Path("/work/langsmith-local.json").write_text(json.dumps(artifact, indent=2) + "\n")
print(json.dumps({"passed": True, "result": result, "child_runs": len(root.child_runs),
                  "wrong_answer_rejected": True, "artifact": "langsmith-local.json"}))
