# app/tests/test_delete_chain.py

import os
import pytest
from dotenv import load_dotenv

# Load env vars so Settings() doesn’t error; or rely on conftest.py
load_dotenv()

from app.agents.utils.chains import get_delete_subtask_chain, get_deleted_message_chain
from app.agents.utils.schemas import DeleteOutput

@pytest.mark.asyncio
@pytest.mark.parametrize("delete_request,expected_terms", [
    ("Delete my Zoom call scheduled tomorrow at 3 PM", ["zoom", "3 pm", "tomorrow"]),
    ("Cancel the dentist appointment on June 15", ["dentist", "june 15"]),
    ("Remove meeting with Sarah next Friday", ["meeting", "sarah", "next friday"]),
    ("Delete all events on July 1st", ["all events", "july 1st"]),
    ("Cancel my flight booking", ["flight", "booking"]),
])
async def test_delete_subtask_chain_reformulation(delete_request, expected_terms):
    """
    Ensure get_delete_subtask_chain turns a variety of delete requests
    into DeleteOutput.query containing key terms.
    """
    chain = get_delete_subtask_chain()
    result: DeleteOutput = await chain.ainvoke({"delete_request": delete_request})

    # It must be a DeleteOutput model
    assert isinstance(result, DeleteOutput)

    query_lower = result.query.lower()
    # Each expected term should appear in the reformulated query
    for term in expected_terms:
        assert term in query_lower

@pytest.mark.asyncio
@pytest.mark.parametrize("context_query", [
    "Delete my Zoom call scheduled tomorrow at 3 PM",
    "Cancel the dentist appointment on June 15"
])
async def test_deleted_message_chain_response(context_query):
    """
    Ensure get_deleted_message_chain returns a friendly deletion confirmation.
    """
    chain = get_deleted_message_chain()
    reply = await chain.ainvoke({"query": context_query})

    # Reply must be non-empty
    assert isinstance(reply, str) and reply.strip()

    # Should contain a deletion‐confirming term
    assert any(word in reply.lower() for word in ["deleted", "cancelled", "canceled", "successfully"])
