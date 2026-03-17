"""
This module contains the State Definitions (the short-term memory) for the whole agentic system.
"""
from typing import TypedDict, List, Annotated, Literal
from langchain_core.messages import AnyMessage
from .utils.helpers import clearable_add
from operator import add

# ======================================================= #
#                     Active Agent                        #
# ======================================================= #

class SubtaskDetails(TypedDict):
    """Details of the sub-query in short-term memory."""
    id: int
    query: str      # the goal of the subtask
    progress: str   # progress of the subtask
    type: str       # type of the task to be performed
    # TODO: add the current datetime to the subtask details to consider the date time sent first
    current_datetime: str

class OverallState(TypedDict):
    """
    Overall state of the agentic system.
    """
    history_summary: Annotated[str, add]
    recent_messages: Annotated[List[AnyMessage], add]
    waiting_subtasks: Annotated[List[SubtaskDetails], add]          # for HIL interaction
    recent_id: Annotated[int, add]            # the last subtask id
    # pending_subtasks: SubtasksDict          # for other tasks (sequential flow)
    # ai_replies: Annotated[List[str], clearable_add]                       # not replied yet
    existing_subtasks_count: Annotated[int, add]
    tenant_id: str
    scheduled_event: dict
    current_datetime: str

class SubtaskState(TypedDict):
    """
    State of the subtask.
    """
    id: int
    query: str
    progress: str
    existing_subtasks_count: int
    tenant_id: str
    current_datetime: str

class ConversationSubState(TypedDict):
    """
    State of the conversation subtask.
    """
    ai_reply: str


# ======================================================= #
#                    Passive Agent                        #
# ======================================================= #

class PassiveState(TypedDict):
    """
    Overall state of the agentic system.
    """
    # stream
    router: Literal["stream", "clarification", "mail"]
    history_summary: Annotated[str, add]
    recent_messages: Annotated[List[AnyMessage], add]
    new_stream: str
    stream_summary: str
    tenant_id: str
    scheduled_event: dict
    current_datetime: str

    # clarification
    task_id: int
    clarification: str

    # mail
    mail: dict