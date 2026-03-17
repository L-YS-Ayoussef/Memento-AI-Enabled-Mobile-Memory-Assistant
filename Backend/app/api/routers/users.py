# from typing import List
# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.orm import Session

# from app.db.business_db import get_db
# from app.models import models
# from app.schemas import schemas
# from app.core.security import get_current_user  # see note below
# from app.db.vector_store.vector_store import vector_store
# from datetime import datetime, timedelta, date, time


# router = APIRouter(
#     prefix="/users",
#     tags=["Users"],
# )

# @router.get("/me", response_model=schemas.UserWithEvents, status_code=status.HTTP_200_OK)
# def read_own_user(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
#     """
#     Fetch the current user's profile (from SQL DB) and their
#     associated events (from the vector store).
#     """
#     today = date.today()
#     day_ranges = [
#         (
#             datetime.combine(today + timedelta(days=i), time.min),
#             datetime.combine(today + timedelta(days=i), time.max)
#         )
#         for i in range(7)
#     ]

#     week_schedule = []
#     try:
#         for window_start, window_end in day_ranges:
#             events = vector_store.list_events_between(
#                 tenant_id=current_user.id,
#                 window_start=window_start,
#                 window_end=window_end
#             )
#             week_schedule.append({
#                 "date": window_start.date().isoformat(),
#                 "events": events
#             })
#     except Exception as e:
#         raise HTTPException(
#             status_code=status.HTTP_502_BAD_GATEWAY,
#             detail=f"Could not fetch events from vector store: {e}"
#         )

#     # raw_events should be a list of dicts matching your Event schema
#     return schemas.UserWithEvents(
#         id=current_user.id,
#         full_name=current_user.full_name,
#         email=current_user.email,
#         gender=current_user.gender,
#         age=current_user.age,
#         events=raw_events
#     )
