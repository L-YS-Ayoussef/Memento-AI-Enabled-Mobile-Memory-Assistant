# app/tests/test_extract_event_details_chain.py

import os
from datetime import datetime, timedelta, timezone
import pytest
from dotenv import load_dotenv

# Load .env so Settings() doesn’t error; or rely on conftest.py
load_dotenv()

from app.agents.utils.chains import get_extract_event_details_chain

# Fixed “now” for all tests
CURRENT_DT = "2025-06-01T00:00:00Z"

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "utterance,exp_start,exp_end,exp_recurring",
    [
        # 1. Fully specified single time
        (
            "Schedule a dentist appointment on 2025-06-15 at 14:30",
            datetime(2025, 6, 15, 14, 30, tzinfo=timezone.utc),
            None,
            None
        ),
        # 2. Specified range with start and end times
        (
            "Schedule a meeting on 2025-06-20 from 09:00 to 10:00",
            datetime(2025, 6, 20, 9, 0, tzinfo=timezone.utc),
            datetime(2025, 6, 20, 10, 0, tzinfo=timezone.utc),
            None
        ),
        # 3. Date only, missing time
        (
            "Block off my calendar on 2025-07-01",
            datetime(2025, 7, 1, 0, 0, tzinfo=timezone.utc),
            datetime(2025, 7, 1, 23, 59, 59, tzinfo=timezone.utc),
            None
        ),
        # 4. Recurring every 2 days starting at a specific time
        (
            "Remind me every 2 days starting 2025-06-10 at 08:00",
            datetime(2025, 6, 10, 8, 0, tzinfo=timezone.utc),
            None,
            172800
        ),
        # 5. Weekly recurrence on a start date
        (
            "Set a periodic backup every week on Monday at 02:00 starting 2025-06-09",
            datetime(2025, 6, 9, 2, 0, tzinfo=timezone.utc),
            None,
            604800
        ),
        # 6. Remind me in 45 minutes
        (
                "Remind me in 45 minutes",
                datetime(2025, 6, 1, 0, 45, tzinfo=timezone.utc),
                None,
                None
        ),
        # 7. Schedule a meeting tomorrow at 09:00
        (
                "Schedule a meeting tomorrow at 09:00",
                datetime(2025, 6, 2, 9, 0, tzinfo=timezone.utc),
                None,
                None
        ),
        # 8. Book a call in two hours
        (
                "Book a call in two hours",
                datetime(2025, 6, 1, 2, 0, tzinfo=timezone.utc),
                None,
                None
        ),
        # 9. Schedule lunch today at 12:00
        (
                "Schedule lunch today at 12:00",
                datetime(2025, 6, 1, 12, 0, tzinfo=timezone.utc),
                None,
                None
        ),
        # 10. Set daily stand-up at 09:00
        (
                "Set daily stand-up at 09:00",
                datetime(2025, 6, 1, 9, 0, tzinfo=timezone.utc),
                None,
                86400,
        ),
    ],
)
async def test_extract_event_details_chain(utterance, exp_start, exp_end, exp_recurring):
    chain = get_extract_event_details_chain(existing_subtasks_count=0)

    # Pass both query & current_datetime to the chain
    result = await chain.ainvoke({
        "query": utterance,
        "current_datetime": CURRENT_DT
    })

    # 1) start_time
    if exp_start is None:
        assert result.event.start_time is None
    else:
        assert result.event.start_time == exp_start

    # 2) end_time
    if exp_end is None:
        assert result.event.end_time is None
    else:
        assert result.event.end_time == exp_end

    # 3) recurring pattern
    if exp_recurring is None:
        assert result.event.recurring is None
    else:
        assert result.event.recurring == exp_recurring

    # 4) reply must always be non-empty
    assert isinstance(result.reply, str) and result.reply.strip() != ""
