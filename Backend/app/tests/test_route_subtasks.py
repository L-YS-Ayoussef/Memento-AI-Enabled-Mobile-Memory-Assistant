# app/tests/test_route_subtasks.py

import pytest
from datetime import datetime
from langgraph.types import Command, Send

from app.agents.nodes import route_subtasks
from app.agents.utils.schemas import RouteOutput


class DummyChain:
    def __init__(self, output):
        self.output = output
    def invoke(self, inputs):
        return self.output

@pytest.mark.asyncio
async def test_route_subtasks_creates_schedule(monkeypatch):
    # 1) Prepare a fake state
    state = {
        "history_summary": "",
        "recent_messages": ["Schedule X at 5 PM"],  # will be ignored by our stub
        "waiting_subtasks": [],
        "recent_id": 0,
        "existing_subtasks_count": 0,
        "tenant_id": "t1",
        "current_datetime": str(datetime.utcnow()),
    }

    # 2) Stub get_router_chain_inputs to bypass message formatting
    monkeypatch.setattr(
        "app.agents.nodes.get_router_chain_inputs",
        lambda s: {"history_summary": s["history_summary"], "messages": s["recent_messages"]}
    )

    # 3) Stub get_router_chain to return our dummy RouteOutput
    dummy_output = RouteOutput(
        sub_tasks=[{"query": "X at 5 PM", "type": "schedule"}],
        reply="Sure, scheduling that now!"
    )
    monkeypatch.setattr(
        "app.agents.nodes.get_router_chain",
        lambda with_hil: DummyChain(dummy_output)
    )

    # 4) Run the node
    cmd: Command = await route_subtasks(state)

    # 5) Check the update payload
    assert cmd.update["recent_id"] == 1
    assert cmd.update["existing_subtasks_count"] == 1

    # 6) Verify the goto list:
    #    - We should first have a conversation_node for the reply
    #    - Then a schedule_node for the new subtask
    gotos = cmd.goto
    # First Send should be conversation_node
    first = gotos[0]
    assert isinstance(first, Send)
    assert first.node == "conversation_node"
    # It should carry the ai_reply in its payload
    assert first.payload["ai_reply"] == dummy_output.reply

    # There should be a Send to schedule_node with our subtask details
    assert any(
        isinstance(g, Send) and g.node == "schedule_node" and
        g.payload["query"] == "X at 5 PM" and
        g.payload["type"] == "schedule"
        for g in gotos
    )
