# app/tests/test_parse_recurrence_chain.py

import pytest
from app.agents.utils.chains import get_parse_recurrence_chain

@pytest.mark.asyncio
@pytest.mark.parametrize("text,exp_weeks,exp_days,exp_hours,exp_minutes", [
    ("every day",  0,  1, 0,  0),
    ("in 2 hours",       0, 0, 2,  0),
    ("every week",       1, 0, 0,  0),
    ("every minute",     0, 0, 0,  1),
])
async def test_parse_recurrence_chain(text, exp_days, exp_hours, exp_minutes,exp_weeks):
    chain = get_parse_recurrence_chain()
    out = await chain.ainvoke({"text": text})
    print(out)
    # TimeDeltaOutput has days, hours, minutes, seconds, weeks
    assert out.days    == exp_days
    assert out.hours   == exp_hours
    assert out.minutes == exp_minutes
    # and ensure no unexpected fields are nonzero
    assert out.weeks   == exp_weeks
    assert out.seconds == 0
