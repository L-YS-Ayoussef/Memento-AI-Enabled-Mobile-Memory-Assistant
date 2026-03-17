from .defs import (
    BaseLevelTasks,
)

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from app.settings import settings
from typing_extensions import List, Any, Optional, Dict, Literal
from operator import add
from langchain_core.messages import AnyMessage
from datetime import datetime, timedelta
import parsedatetime as pdt
from zoneinfo import ZoneInfo
from langchain_core.messages import AIMessage
from uuid import uuid4
# ==================== General Helper Methods ==================== #

def base_tasks_description_to_str() -> str:
    """Returns the base level tasks description."""
    return "\n".join(f"- {task}: {task.value}" for task in BaseLevelTasks)


def parse_recurrence(input: str) -> Optional[timedelta]:
    """
    Converts a natural language recurrence phrase into a Python timedelta object.

    Returns:
        Optional[timedelta]: Corresponding timedelta object, or None if parsing fails.
    """
    from .chains import get_parse_recurrence_chain
    if not input.strip():
        return None

    try:
        output = get_parse_recurrence_chain.invoke({"input": input})
        # print("Parsed output:", output)
        return timedelta(**output.model_dump())
    except Exception as e:
        # print(f"Failed to parse recurrence from input '{input}': {e}")
        return None
    
def is_passive_agent(state: Dict[str, Any]) -> bool:
    return bool(state.get("router", ""))

# TODO: consider timezone support
# def parse_datetime(input_datetime: str, tz_str: str) -> datetime | None:
#     """
#     Parse human-readable datetime and convert it to UTC using user's timezone.
    
#     Parameters:
#         input_datetime (str): e.g., "tomorrow at 9pm"
#         tz_str (str): IANA timezone, e.g., "Africa/Cairo"
    
#     Returns:
#         datetime: UTC-aware datetime or None
#     """
#     if not isinstance(input_datetime, str):
#         return None

#     # Parse using parsedatetime (returns time_struct)
#     calendar = pdt.Calendar()
#     time_struct, status = calendar.parse(input_datetime)
#     if not status:
#         return None

#     local_naive = datetime(*time_struct[:6])

#     # Attach timezone to make it timezone-aware
#     try:
#         local_zone = ZoneInfo(tz_str)
#     except Exception:
#         return None

#     local_aware = local_naive.replace(tzinfo=local_zone)

#     # # Convert to UTC for storage or scheduling
#     # utc_dt = local_aware.astimezone(ZoneInfo("UTC"))

#     return local_aware, utc_dt 


def parse_datetime(input_datetime: str) -> Optional[datetime]:
    """
    Parse datetime string returned from LLM assuming input is interpreted in UTC.
    """
    if not isinstance(input_datetime, str):
        return None

    calendar = pdt.Calendar()
    time_struct, status = calendar.parse(input_datetime)
    if not status:
        return None

    # Build naive datetime from parsed time struct
    naive_dt = datetime(*time_struct[:6])

    # Treat it as UTC time (LLM assumed base)
    utc_dt = naive_dt.replace(tzinfo=ZoneInfo("UTC"))
    return utc_dt


def convert_utc_to_client_tz(utc_dt: datetime, tz_str: str) -> datetime:
    try:
        return utc_dt.astimezone(ZoneInfo(tz_str))
    except Exception:
        return utc_dt  # fallback to UTC


# def parse_datetime(input_datetime) -> datetime:
#     """Parses human-redable datetime"""
#     if not isinstance(input_datetime, str):
#         return None

#     calendar = pdt.Calendar()

#     time_struct, status = calendar.parse(input_datetime)
#     if not status:
#         return None
    
#     return datetime(*time_struct[:6])


# ==================== State (Short-term Memory) ==================== #

def clearable_add(old: List[Any], new: List[Any]) -> List[Any]:
    """For updating the list of messages in short-term memory."""
    if not new:     # If the node returned an empty list, reset to empty
        return []
    return add(old, new)

def waiting_subtasks_to_str(waiting_subtasks) -> str:
    """Returns the waiting subtasks in a string format."""
    return "\n".join(
        f"**Subtask ID: {task["id"]}**:\n\t- Goal: {task['query']}\n\t-Progress: {task['progress']}"
        for task in waiting_subtasks
    )

def recent_messages_to_str(recent_messages: List[AnyMessage]) -> str:
    """Returns the recent messages in a string format."""
    return "\n".join(
        f"{msg.type}: {msg.content}" for msg in recent_messages
    ) 


def prepare_new_subtasks(state, new_subtasks, agent_type: Literal["passive", "active"]="active"):
    """Process the new sbtask list into SubtaskDetails list.
    Returns:
        - List of new subtasks.
    """
    if agent_type == "active":
        id = state.get("recent_id", 0)
    elif agent_type == "passive":
        id = uuid4().int  # Use a unique ID for passive agents            
    
    prepared_subtasks = []

    for subtask in new_subtasks:
        if agent_type == "active": id += 1  # Increment the ID for each new subtask
        task_details = {
            "id": id,
            "query": subtask.query,
            "type": subtask.type,
            "progress": "",
            "current_datetime": state.get("current_datetime", datetime.now().isoformat())
        }
        prepared_subtasks.append(task_details)

    return prepared_subtasks


def add_clarifications(state, clarifications):
    """
    Adds a new clarification to the state, change status to running, remove them from waiting subtasks.

    Returns:
        - List of clarified tasks.
    """
    clarifications_dict = {clarification.task_id: clarification.clarification for clarification in clarifications}
    clarified_tasks = []

    for task in state.get("waiting_subtasks",[]):
        if task["id"] in clarifications_dict.keys():
            task["progress"] += f"\nUser: {clarifications_dict[task['id']]}"
            clarified_tasks.append(task)
            state["waiting_subtasks"].remove(task)
    
    return clarified_tasks


def cancel_subtasks(state, task_ids: List[int]) -> List[int]:
    """Cancels a subtask in the state."""
    # cancelled_ids = []
    for task in state.get("waiting_subtasks", []):
        if task["id"] in task_ids:
            state["waiting_subtasks"].remove(task)
            # cancelled_ids.append(task["id"])

    #return cancelled_ids


# ==================== LLMs ==================== #

def get_chat_model(temperature: float = 0.0) -> BaseChatModel:
    """Returns the LLM instance."""
    return ChatGoogleGenerativeAI(
        model=settings.CHAT_MODEL,
        api_key=settings.GOOGLE_API_KEY,
        temperature=temperature
    )


# ==================== Decision (Router) Agent ==================== #

def get_router_chain_inputs(state) -> dict:
    """
    Returns the inputs for the router chain.
    """
    base_tasks_description = base_tasks_description_to_str()
    history_summary = state.get("history_summary", "")
    recent_messages = recent_messages_to_str(state.get("recent_messages", []))
    
    router_chain_input = {
        "base_tasks_description": base_tasks_description,
        "history_summary": history_summary,
        "messages": recent_messages,
    } 
    if state["waiting_subtasks"]:
        router_chain_input.update({
            "existing_subtasks": waiting_subtasks_to_str(state.get("waiting_subtasks", []))
        })

    return router_chain_input


# ==================== Schedule Agent ==================== #

def event_details_to_str(event_details: Dict, include_trigger: bool=False) -> str:
    included_keys = {"title", "start_time", "end_time", "min_start_time", "max_end_time", "people", "location", "description"} | ({"trigger"} if include_trigger else set())
    return "\n".join([f"{k}: {v}" for k, v in event_details.items() if k in included_keys and v])


def serialize_event_details(event, event_id) -> dict:
    """Serializes event details."""
    from .chains import get_remider_message_chain

    datetime_keys = {"start_time", "end_time", "min_start_time", "max_end_time"}
    excluded_keys = {"is_recurring"}

    details = {}
    for key, value in event.model_dump().items():
        if not value or key in excluded_keys:
            continue

        if key in datetime_keys:
            details[key] = value.isoformat()
        # elif key == "recurring":
        #     details[key] = value.total_seconds()
        else:
            details[key] = value

    details["id"] = str(event_id)
    details["reminder_message"] = get_remider_message_chain().invoke({
        "event_details": event_details_to_str(event.model_dump(), True)
    })

    return details


def prepare_schedule_update(state: Dict[str, Any], query:str, event, reply, vector_store, task_type, ready=True, event_id=None, email={}) -> Dict[str, Any]:
    """
    Prepares the update dictionary based on whether the event is ready to be scheduled.
    If ready, attempts to add to the vector store and updates accordingly.
    If not ready, logs the reply in 'waiting_subtasks'.
    """
    from .chains import get_conflict_schedule_chain, get_event_updated_message_chain

    update_dict = {}

    if ready:
        event_details_dict = event.model_dump()
        event_details_dict = {k: v for k, v in event_details_dict.items() if v is not None and k != "is_recurring"}
        # for key in ["start_time", "end_time", "min_start_time", "max_end_time"]:
        #     value = event_details_dict.get(key, None)
        #     if value:
        #         event_details_dict[key] = convert_utc_to_client_tz(value, timezone)
        if email: event_details_dict.update({"email": email})
        if task_type == "schedule":
            is_successful, result = vector_store.add_event(
                state.get("tenant_id"),
                event_details_dict
            )
        elif task_type == "update":
            is_successful, result = vector_store.update_task_info(
                state.get("tenant_id"),
                event_id,
                event_details_dict
            )

        if is_successful:
            id = str(result) if result else event_id
            serialized_event = serialize_event_details(event, id)
            if not reply:
                reply = get_event_updated_message_chain().invoke({
                    "query": query,
                })

            update_dict.update({
                "scheduled_event": serialized_event,
                "recent_messages": [AIMessage(content=reply)],
                "existing_subtasks_count": -1
            })

        else:
            conflict_event_str = event_details_to_str(result, False)       # result: conflict event details
            if result:        # result = dict of conlict event
                ai_reply = get_conflict_schedule_chain().invoke({
                    "requested_event": query,
                    "existing_event": conflict_event_str
                })
            else:
                ai_reply = f"Something went wrong; couldn't {task_type} the event." 
                # TODO: loop until resolved
            
            update_dict.update({
            "waiting_subtasks": [{
                "id": state["id"],
                "query": state["query"],
                "type": task_type,
                "progress": f"{state['progress']}\nAI: {ai_reply}"
            }],
            "recent_messages": [AIMessage(content=ai_reply)]
        })
    
    else:
        update_dict.update({
            "waiting_subtasks": [{
                "id": state["id"],
                "query": state["query"],
                "type": task_type,
                "progress": f"{state['progress']}\nAI: {reply}"
            }],
            "recent_messages": [AIMessage(content=reply)]
        })

    return update_dict


# ==================== Vctor Store ==================== #


def add_timezone_to_datetime(dt, tz: str = "UTC") -> str:
    """Ensure datetime has timezone and convert to RFC3339."""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            raise ValueError(f"Invalid ISO datetime string: {dt}")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz))
    return dt.isoformat()



def reformulate_query(state: dict) -> str:
    from .chains import get_reformulate_schedule_query_chain
    """
    Determines the effective query from the given state, potentially reformulating it
    based on interaction progress.
    """
    progress = state.get("progress", "")
    base_query = state.get("query", "")
    
    if progress:
        reformulate_query_chain = get_reformulate_schedule_query_chain()
        result = reformulate_query_chain.invoke({
            "query": base_query,
            "interactions": progress
        })
        return result.query or base_query
    
    return base_query
