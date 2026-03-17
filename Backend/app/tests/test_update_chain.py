# app/tests/test_update_chain.py

import pytest
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load .env so Settings() doesn’t error; or rely on conftest.py
load_dotenv()

from app.agents.utils.chains import get_update_chain
from app.agents.utils.schemas import Event

# A base “existing” event to update
BASE_EVENT_JSON = {
    "title": "Team Sync",
    "trigger": "time",
    "start_time": "2025-06-15T14:00:00Z",
    "end_time":   "2025-06-15T15:00:00Z",
    "min_start_time": None,
    "max_end_time": None,
    "can_overlap": False,
    "is_recurring": False,
    "place": None,
    "people": [],
    "details": None
}

# Fixed “now” for all tests
CURRENT_DT = "2025-06-01T00:00:00Z"

@pytest.mark.asyncio
@pytest.mark.parametrize("update_request,assert_fn", [
    # 1) Title change only
    (
        "Change the title to Budget Review",
        lambda evt: (
            evt.title == "Budget Review" and
            evt.start_time == datetime(2025,6,15,14,0,tzinfo=timezone.utc) and
            evt.end_time   == datetime(2025,6,15,15,0,tzinfo=timezone.utc)
        )
    ),
    # 2) Time‐of‐day change only
    (
        "Move to 16:00",
        lambda evt: (
            evt.title == "Team Sync" and
            evt.start_time == datetime(2025,6,15,16,0,tzinfo=timezone.utc) and
            # end_time shifts by the same duration (+1h)
            evt.end_time   == datetime(2025,6,15,17,0,tzinfo=timezone.utc)
        )
    ),
    # 3) Date change only
    (
        "Reschedule to June 20, 2025",
        lambda evt: (
            evt.title == "Team Sync" and
            evt.start_time == datetime(2025,6,20,14,0,tzinfo=timezone.utc) and
            evt.end_time   == datetime(2025,6,20,15,0,tzinfo=timezone.utc)
        )
    ),
    # 4) Relative delay
    (
        "Delay by 2 hours",
        lambda evt: (
            evt.start_time == datetime(2025,6,15,16,0,tzinfo=timezone.utc) and
            evt.end_time   == datetime(2025,6,15,17,0,tzinfo=timezone.utc)
        )
    ),
    # 5) Turn into a daily recurring event
    (
        "Make this a daily event",
        lambda evt: (
            evt.is_recurring is True
        )
    ),
])
async def test_update_chain_various(update_request, assert_fn):
    chain = get_update_chain()
    result: Event = await chain.ainvoke({
        "update_request":  update_request,
        "event_details":   BASE_EVENT_JSON,
        "current_datetime": CURRENT_DT
    })

    # Should be an Event model
    assert isinstance(result, Event)

    # Custom assertion per case
    assert assert_fn(result)
