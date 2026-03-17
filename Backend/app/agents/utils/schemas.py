"""
Pydantic schemas for llm structured outputs.
"""

from pydantic import BaseModel, Field, PlainValidator
from typing_extensions import Literal, List, Optional, Annotated
from datetime import datetime, timedelta

# ==================== General ==================== #
class TimeDeltaOutput(BaseModel):
    weeks: Optional[int] = 0
    days: Optional[int] = 0
    hours: Optional[int] = 0
    minutes: Optional[int] = 0
    seconds: Optional[int] = 0


# ======================================================= #
#                     Active Agent                        #
# ======================================================= #

# ==================== Decision (Router) Agent ==================== #

class SubTask(BaseModel):
    query: str = Field(..., description="A concise and reformulated version of the user's request, optimized for agent processing.")
    type: Literal["schedule", "query", "update", "delete", "conversation"] = Field(..., description="Type of the task.")

class Clarification(BaseModel):
    clarification: str = Field(..., description="User's verbatim answer.")
    task_id: Optional[int] = Field(None, description="Matching ID from existing tasks, or null if undetermined.")


class RouteOutputWithHIL(BaseModel):
    """Output of the Decision Router agent in case of waiting tasks."""
    sub_tasks: List[SubTask] = Field(default_factory=list, description="List of new subtasks.")
    clarifications: List[Clarification] = Field(default_factory=list, 
                                                description=("List of clarifications."
                                                "If user clarifications are vague, irrelevant, or ambiguous, in case of multiple waiting tasks, so that you cannot decide which task he replies to, don't consider them.")
                                                )
    cancels: List[int] = Field(default_factory=list, description="List of subtask IDs to be canceled.")
    reply: Optional[str] = Field(None)

class RouteOutput(BaseModel):
    """Output of the Decision Router agent in case of no waiting tasks."""
    sub_tasks: List[SubTask] = Field(default_factory=list, description="List of new subtasks.")
    reply: Optional[str] = Field(None)


# ==================== Schedule Agents ==================== #

class Event(BaseModel):
    from .helpers import parse_recurrence

    title: str = Field(
        ..., 
        description="Short descriptive, concise and action-oriented title of the event."
    )

    trigger: Literal["time", "location"] = Field(
        ..., 
        description=(
            "What triggers the event, considering potential for time or location-based reminders."
            "You must educe the trigger with carefull and proper reasoning after analyzing the user query and the event's nature.")
    )
    
    start_time: Optional[datetime] = Field(
        None, 
        description="Exact event start time if explicitly mentioned or clearly inferable for an exact point in time."
                    "It must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or None if not specified."
    )
    
    end_time: Optional[datetime] = Field(
        None, 
        description="Exact event end time if explicitly mentioned or clearly inferable (e.g., from a duration)."
                    "It must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or None if not specified."
    )
    
    min_start_time: Optional[datetime] = Field(
        None, 
        description=(
            "Earliest possible start time if the user mentions a vague timeframe (e.g., 'tomorrow morning', 'next week', 'sometime today'). "
            "For 'today' or any other day without specific time, this could be the current time or a conventional start like 07:00 at that day."
            "For 'next week', use Monday 00:00:00 of the next calendar week, and so on."
            "It must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or None if not specified."
        )
    )
    
    max_end_time: Optional[datetime] = Field(
        None, 
        description=(
            "Latest possible end time for vague timeframes. "
            "If min_start_time is set for a specific day (e.g., from 'tomorrow' or 'today'), max_end_time should typically be the end of that day. "
            "For 'next week', it's Sunday 23:59:59 of that week, and so on."
            "It must be in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) or None if not specified."
        )
    )

    can_overlap: bool = Field(
        False, 
        description=(
            "Whether this event is allowed to overlap with other scheduled items. Infer this: "
            "Most meetings, appointments, or focused tasks CANNOT overlap (False). "
            "Personal tasks might be more flexible (True). "
            "Default to False if unsure, especially for interactive events or appointments."
        )
    )
    
    # recurring: Optional[Annotated[timedelta, PlainValidator(parse_recurrence)]] = Field(
    #     None, 
    #     description="Recurrence pattern if only mentioned. Consider the min_start_time and the max_end_time as the bounds of the recurrence. "
    # )

    is_recurring: bool = Field(
        False,
        description=(
            "true if the task is logically or explicitly recurring, even if not clearly stated as recurring."
        )
    )
    
    place: Optional[str] = Field(
        None, 
        description=(
            "Location of the event. Can be a physical address, a type of place, "
            "or a virtual location (e.g., 'Zoom call', 'online', 'Microsoft Teams', 'Google Meet'). "
            "If virtual, ensure `trigger` is set to 'time'."
            "If the place not mentioned, and can be inferred from the task, use a generic type (e.g., 'home', 'office', 'grocery store'). "
            "But if the event depends on a specific place, and not mentioned, set to None. And ask the user for it in the `reply`, but set `ready` to False. "
        )
    )
    
    people: List[str] = Field(
        default_factory=list, 
        description="Names of people involved or invited to the event, extracted directly from the query."
    )
    
    details: Optional[str] = Field(
        None, 
        description=(
            "Important additional details, context, or the primary subject/object of the task if not adequately captured in the title. "
            "Avoid redundant information already clearly present in the title or other specific fields."
        )
    )


class ScheduleEvent(BaseModel):
    title: str = Field(
        ..., 
        description="Short descriptive, concise and action-oriented title of the event."
    )

    trigger: Literal["time", "location"] = Field(
        ..., 
        description=(
            "What triggers the event. You must educe the trigger with carefull and proper reasoning after analyzing the user query and the event's nature.")
    )
    
    start_time: Optional[datetime] = Field(
        None, 
        description="Exact event start time if explicitly mentioned or clearly inferable for an exact point in time. "
                    "It must be in ISO 8601 format."
    )
    
    end_time: Optional[datetime] = Field(
        None, 
        description="Exact event end time if explicitly mentioned or clearly inferable (e.g., from a duration). "
                    "It must be in ISO 8601 format."
    )
    
    min_start_time: Optional[datetime] = Field(
        None, 
        description=(
            "Earliest possible start time if the user mentions a vague timeframe (e.g., 'tomorrow morning', 'next week', 'sometime today'). "
            "For 'today', 'next week' or any other day without specific time, use proper conventional start."
            "It must be in ISO 8601 format."
        )
    )
    
    max_end_time: Optional[datetime] = Field(
        None, 
        description=(
            "Latest possible end time for vague timeframes. "
            "If min_start_time is set for a specific day (e.g., from 'tomorrow' or 'today'), max_end_time should typically be the end of that day. "
            "It must be in ISO 8601 format."
        )
    )

    can_overlap: bool = Field(
        False, 
        description=(
            "Most meetings, appointments, or focused tasks CANNOT overlap (False). "
            "Personal tasks might be more flexible (True). "
        )
    )
    
    recurring: Optional[int] = Field(
        None,
        description=(
            "Recurrence interval in total seconds, parsed from natural-language input (e.g., “every 3 days”). "
            "When no explicit start/end is given but a recurrence is mentioned, it"
            "defines the spacing between successive occurrences."
        )
    )

    # is_recurring: bool = Field(
    #     False,
    #     description=(
    #         "true if the task is logically or explicitly recurring, even if not clearly stated as recurring."
    #     )
    # )
    
    place: Optional[str] = Field(
        None, 
        description=(
            "Location of the event. Can be a physical address, a type of place, "
            "or a virtual location (e.g., 'Zoom call', 'online', 'Microsoft Teams', 'Google Meet'). "
            "If virtual, ensure `trigger` is set to 'time'."
            "If the place not mentioned, and can be inferred from the task, use a generic type (e.g., 'home', 'office', 'grocery store'). "
            "But if the event depends on a specific place, and not mentioned, set to None. And ask the user for it in the `reply`, but set `ready` to False. "
        )
    )
    
    people: List[str] = Field(
        default_factory=list, 
        description="Names of people involved or invited to the event, extracted directly from the query."
    )
    
    details: Optional[str] = Field(
        None, 
        description=(
            "Important additional details, context, or the primary subject/object of the task if not adequately captured in the title. "
            "Avoid redundant information already clearly present in the title or other specific fields."
        )
    )


class ScheduleOutput(BaseModel):
    event: ScheduleEvent = Field(
        ..., 
        description="Event object parsed from the user query."
    )
    
    ready: bool = Field(
        False, 
        description=(
            "Set to True ONLY if all ESSENTIAL information for scheduling this specific type of event "
            "has been provided and there are NO outstanding critical ambiguities that prevent scheduling. Otherwise, False."
            "If the event is location-triggered, ensure the `place` field is set. "
            "Never set to True if you still need to ask the user for any critical information."
        )
    )
    
    reply: str = Field(
        ..., 
        description=(
            "Agent's natural language response. This must be conversational, empathetic, and context-aware. "
            "If `ready` is False, this field must explain what information is missing and ask clear, polite questions, prioritizing the most crucial missing information according to the nature of the event. "
            "If `ready` is True, this field should confirm that you have scheduled the event successfully (mention the details that matters the user). "
            "If the event is item-centered that needs to specify the type and the type is not mentioned, ask the user to provide it, and the `ready` field must be False in this case. "
            "Avoid robotic phrasing like directly quoting the event title in an unnatural way; paraphrase naturally."
            "If the recurring field is None, and the even is intuitively recurring, ask if to repeat in specific times. "
        )
    )

class ReformulateScheduleQueryOutput(BaseModel):
    """
    Output of the chain for reformulating a schedule query.
    """
    query: str = Field(
        ...,
        # description=(
        #     "Reformulated query that is concise, clear, and suitable for scheduling tasks. "
        #     "It should be a direct and actionable request that can be processed by the scheduling agent."
        # )
    )


# ==================== Update Agent ==================== #

# class UpdateEvent(BaseModel):
#     from .helpers import parse_datetime, parse_recurrence
#     """Pydantic model for updating an event. This model is used to represent the details of an event that needs to be updated."""

#     # TODO: id optional for the events detected from the interaction history

#     title: Optional[str] = Field(
#         None, 
#         description="Short descriptive, concise and action-oriented title of the event."
#     )

#     trigger: Literal["time", "location"] = Field(
#         None, 
#         description=(
#             "What triggers the event, considering potential for time or location-based reminders."
#             "You must educe the trigger with carefull and proper reasoning after analyzing the user query and the event's nature.")
#     )
    
#     start_time: Annotated[datetime, PlainValidator(parse_datetime)] = Field(
#         None, 
#         description="Exact event start time if explicitly mentioned or clearly inferable for an exact point in time."
#     )
    
#     end_time: Annotated[datetime, PlainValidator(parse_datetime)] = Field(
#         None, 
#         description="Exact event end time if explicitly mentioned or clearly inferable (e.g., from a duration)."
#     )
    
#     min_start_time: Annotated[datetime, PlainValidator(parse_datetime)] = Field(
#         None, 
#         description=(
#             "Earliest possible start time if the user mentions a vague timeframe (e.g., 'tomorrow morning', 'next week', 'sometime today'). "
#             "For 'today' or any other day without specific time, this could be the current time or a conventional start like 07:00 at that day."
#             "For 'next week', use Monday 00:00:00 of the next calendar week, and so on."
#         )
#     )
    
#     max_end_time: Annotated[datetime, PlainValidator(parse_datetime)] = Field(
#         None, 
#         description=(
#             "Latest possible end time for vague timeframes. "
#             "If min_start_time is set for a specific day (e.g., from 'tomorrow' or 'today'), max_end_time should typically be the end of that day. "
#             "For 'next week', it's Sunday 23:59:59 of that week, and so on."
#         )
#     )

#     can_overlap: bool = Field(
#         False, 
#         description=(
#             "Whether this event is allowed to overlap with other scheduled items. Infer this: "
#             "Most meetings, appointments, or focused tasks CANNOT overlap (False). "
#             "Personal tasks might be more flexible (True). "
#             "Default to False if unsure, especially for interactive events or appointments."
#         )
#     )
    
#     recurring: Optional[Annotated[timedelta, PlainValidator(parse_recurrence)]] = Field(
#         None, 
#         description="Recurrence pattern if only mentioned. Consider the min_start_time and the max_end_time as the bounds of the recurrence. "
#     )

#     is_recurring: bool = Field(
#         False,
#         description=(
#             "true if the task is logically or explicitly recurring, even if not clearly stated as recurring."
#         )
#     )
    
#     place: Optional[str] = Field(
#         None, 
#         description=(
#             "Location of the event. Can be a physical address, a type of place, "
#             "or a virtual location (e.g., 'Zoom call', 'online', 'Microsoft Teams', 'Google Meet'). "
#             "If virtual, ensure `trigger` is set to 'time'."
#             "If the place not mentioned, and can be inferred from the task, use a generic type (e.g., 'home', 'office', 'grocery store'). "
#             "But if the event depends on a specific place, and not mentioned, set to None. And ask the user for it in the `reply`, but set `ready` to False. "
#         )
#     )
    
#     people: List[str] = Field(
#         default_factory=list, 
#         description="Names of people involved or invited to the event, extracted directly from the query."
#     )
    
#     details: Optional[str] = Field(
#         None, 
#         description=(
#             "Important additional details, context, or the primary subject/object of the task if not adequately captured in the title. "
#             "Avoid redundant information already clearly present in the title or other specific fields."
#         )
#     )


# class UpdateOutput(BaseModel):
#     """
#     Output of the Update Agent (update).
#     """

#     query: str = Field(
#         ...,
#         description=(
#             "Reformulated fetch query to get the targeted scheduled event."
#         )
#     )
#     new_details: UpdateEvent = Field(
#         ...,
#         description=(
#             "New details of the event to be updated. "
#         )
#     )


# ==================== Delete Agent ==================== #

class DeleteOutput(BaseModel):
    reformulated_query: str = Field(..., description="The reformulated fetch event query.")


# ======================================================= #
#                    Passive Agent                        #
# ======================================================= #

# ==================== Router Agent ==================== #

# 1. Stream Router Agent

class PassiveSubTask(BaseModel):
    query: str = Field(..., description="Reformulated instruction for the scheduler agent.")
    type: Literal["schedule", "update", "delete"] = Field(
        ..., description="Type of task to perform."
    )

class PassiveStreamRouteOutput(BaseModel):
    """
    - sub_tasks: newly detected scheduling subtasks (inferred from conversation)
    - new_stream_summary: updated rolling summary of the user's spoken streams
    """
    sub_tasks: List[PassiveSubTask] = Field(default_factory=list)
    new_stream_summary: str = Field(...,
        description="Updated summary of all past streams plus the new one.")


class PassiveMailOutput(BaseModel):
    """
    Output of the Passive Mail Router Agent.
    """
    sub_tasks: List[PassiveSubTask] = Field(default_factory=list, description="List of new subtasks.")