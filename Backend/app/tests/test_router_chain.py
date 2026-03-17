import os
import re
import pytest
from dotenv import load_dotenv
from app.agents.utils.chains import get_router_chain


def normalize(text: str) -> str:
    """Lowercase, strip whitespace, remove trailing periods."""
    t = text.lower().strip()
    return re.sub(r"\.$", "", t)

# Map our high-level intent labels to the sub_task.type values your router produces
INTENT_TO_TYPE = {
    "create":      "schedule",
    "update":      "update",
    "delete":      "delete",
    "query":       "query",
    "conversation": None,   # no subtask produced for pure conversation
}

@pytest.mark.asyncio
@pytest.mark.parametrize("utterance,intent,expected_queries", [
    ("Schedule a dentist appointment next Tuesday at 3 PM.", "create",
     ["a dentist appointment next tuesday at 3 pm"]),
    ("Move that appointment to Friday morning.", "update",
     ["move the dentist appointment to friday morning"]),
    ("Cancel my lunch meeting tomorrow.", "update",
     ["cancel my lunch meeting tomorrow"]),
    ("What do I have on my calendar this afternoon?", "query",
     ["what events are on my calendar this afternoon"]),
    ("Thanks, that's all for now.", "conversation", []),
    ("Remind me to call mom every month on the 1st.", "create",
     ["remind me to call mom every month on the 1st"]),
    ("Change the title of my meeting with Sarah to 'Budget Review'.", "update",
     ["change the title of my meeting with sarah to 'budget review'"]),
    ("Delete everything on June 15th.", "update",
     ["delete everything on june 15th"]),
    ("Do I have any free slots next week?", "query",
     ["what free time slots do i have next week"]),
    ("Actually, push that to 5 PM instead.", "update",
     ["push the previous event to 5 pm instead"]),
    ("Set up a recurring stand-up meeting every weekday at 9 AM.", "create",
     ["set up a recurring stand-up meeting every weekday at 9 am"]),
    ("I'll be out of office June 20-22, block off my calendar.", "create",
     ["block off my calendar june 20-22 for out of office"]),
    ("What did I schedule last Friday?", "query",
     ["list events i scheduled last friday"]),
    ("Actually, never mind.", "conversation", []),
    ("Reschedule my doctor's appointment—no more afternoons, please.", "update",
     ["reschedule my doctor's appointment to a morning slot"]),
])
async def test_router_chain(utterance, intent, expected_queries):
    chain = get_router_chain(with_hil=False)

    # Supply exactly the two variables the PromptTemplate expects
    inputs = {
        "history_summary": "",
        "messages": [utterance],
    }

    result = await chain.ainvoke(inputs)
    sub_tasks = result.sub_tasks

    expected_type = INTENT_TO_TYPE[intent]
    if expected_type is None:
        # Pure conversation: no subtasks should be produced
        assert sub_tasks == []
    else:
        # Check each subtask's query and type
        assert len(sub_tasks) == len(expected_queries)
        for idx, expected_query in enumerate(expected_queries):
            assert sub_tasks[idx].type == expected_type
