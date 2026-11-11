"""Synthetic offline checks. No model, provider, host data or network required."""
import argparse
import json
import importlib.metadata
import os
from pathlib import Path
import socket
import sqlite3
import sys
from typing import TypedDict
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import tool
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


@tool
def double(value: int) -> int:
    """Double a synthetic integer."""
    return value * 2


class FixedToolModel(BaseChatModel):
    """A scripted local function, never an inference provider."""
    @property
    def _llm_type(self):
        return "nstack-synthetic-fixed-tool"

    def bind_tools(self, tools, **kwargs):
        return self

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        if isinstance(messages[-1], ToolMessage):
            assert json.loads(messages[-1].content) == 12
            answer = AIMessage(content="synthetic-result=12")
        else:
            answer = AIMessage(content="", tool_calls=[{"name": "double", "args": {"value": 6}, "id": "synthetic-call", "type": "tool_call"}])
        return ChatResult(generations=[ChatGeneration(message=answer)])


def controls():
    assert os.environ.get("LANGSMITH_TRACING") == "false"
    assert os.environ.get("LANGCHAIN_TRACING_V2") == "false"
    assert not any(k.endswith(("API_KEY", "TOKEN")) or k in {"AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"} for k in os.environ)
    assert not Path("/Users").exists()
    assert sys.version_info[:3] == (3, 12, 16)
    for name, version in {"langchain": "1.5.0", "langchain-core": "1.8.0", "langgraph": "1.2.20", "langgraph-checkpoint-sqlite": "3.1.3"}.items():
        assert importlib.metadata.version(name) == version
    # An IP avoids a DNS failure being confused with actual network isolation.
    try:
        socket.create_connection(("1.1.1.1", 443), timeout=1).close()
    except OSError:
        pass
    else:
        raise AssertionError("Runtime has unexpected network access")
    agent = create_agent(FixedToolModel(), tools=[double])
    result = agent.invoke({"messages": [{"role": "user", "content": "synthetic: double six"}]})
    assert result["messages"][-1].content == "synthetic-result=12"
    assert sum(isinstance(m, ToolMessage) for m in result["messages"]) == 1
    from pydantic import ValidationError
    try:
        double.invoke({"value": "invalid synthetic integer"})
    except ValidationError:
        pass
    else:
        raise AssertionError("Tool accepted invalid typed input")
    return {"network_denied": True, "tool_calls": 1, "tool_result": 12, "invalid_tool_input_rejected": True}


class State(TypedDict):
    value: int
    approved: bool
    result: int


def graph(connection):
    def review(state):
        assert state["value"] == 6
        decision = interrupt({"kind": "synthetic-review", "value": state["value"]})
        if decision is not True:
            raise ValueError("Synthetic approval required")
        return {"approved": True}

    def effect(state):
        assert state["approved"] is True
        # The ledger and synthetic effect commit together. The node may replay.
        with sqlite3.connect("/work/effects.sqlite") as ledger:
            ledger.execute("CREATE TABLE IF NOT EXISTS effects(id TEXT PRIMARY KEY, value INTEGER)")
            ledger.execute("INSERT OR IGNORE INTO effects VALUES ('synthetic-once', ?)", (state["value"] * 2,))
            ledger.commit()
        marker = Path("/work/crashed-once")
        if not marker.exists():
            marker.write_text("synthetic crash after effect commit before graph checkpoint\n")
            os._exit(23)
        return {"result": state["value"] * 2}

    builder = StateGraph(State)
    builder.add_node("review", review)
    builder.add_node("effect", effect)
    builder.add_edge(START, "review")
    builder.add_edge("review", "effect")
    builder.add_edge("effect", END)
    return builder.compile(checkpointer=SqliteSaver(connection))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("phase", choices=["pause", "crash", "resume", "wrong-result"])
    args = parser.parse_args()
    checks = controls()
    config = {"configurable": {"thread_id": "nstack-synthetic-thread"}}
    with sqlite3.connect("/work/checkpoints.sqlite", check_same_thread=False) as connection:
        app = graph(connection)
        if args.phase == "pause":
            result = app.invoke({"value": 6, "approved": False, "result": 0}, config)
            assert result["__interrupt__"][0].value == {"kind": "synthetic-review", "value": 6}
            assert not Path("/work/effects.sqlite").exists()
            checks["paused_before_effect"] = True
        elif args.phase == "crash":
            app.invoke(Command(resume=True), config)
            raise AssertionError("Injected crash did not happen")
        else:
            result = app.invoke(None, config)
            assert result["result"] == (13 if args.phase == "wrong-result" else 12)
            assert not app.get_state(config).next
            with sqlite3.connect("/work/effects.sqlite") as ledger:
                rows = ledger.execute("SELECT id, value FROM effects").fetchall()
            assert rows == [("synthetic-once", 12)]
            checks.update(result=12, effect_rows=len(rows), complete=True, survived_fresh_process=True)
    print(json.dumps({"phase": args.phase, **checks}, sort_keys=True))


if __name__ == "__main__":
    main()
