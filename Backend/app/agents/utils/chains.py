from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from typing import Literal


from .prompts import (
    ROUTE_SUBTASKS_PROMPT,
    ROUTE_SUBTASKS_WITH_HIL_PROMPT,
    PARSE_RECURRENCE_PROMPT,
    SCHEDULE_SUBTASK_PROMPT,
    REFORMULATE_SCHEDULE_QUERY_PROMPT,
    FIRST_SUMMARY_PROMPT,
    EXTEND_SUMMARY_PROMPT,
    CONFLICT_SCHEDULE_PROMPT,
    REMINDER_MESSAGE_PROMPT,
    UPDATE_SUBTASK_PROMPT,
    DELETED_MESSAGE_PROMPT,
    EVENT_NOT_FOUND_MESSAGE_PROMPT,
    EVENT_UPDATED_MESSAGE_PROMPT,
    CONFLICT_UPDATE_PROMPT,
    DELETE_SUBTASK_PROMPT,
    FETCH_REQUEST_PROMPT,
    ALREADY_CANCELLED_MESSAGE_PROMPT,
    PASSIVE_STREAM_ROUTE_SUBTASKS_PROMPT,
    PASSIVE_EMAIL_ROUTE_SUBTASKS_PROMPT
)

from .helpers import (
    get_chat_model
)

from .schemas import (
    RouteOutputWithHIL,
    RouteOutput,
    TimeDeltaOutput,
    ScheduleOutput,
    ReformulateScheduleQueryOutput,
    Event,
    DeleteOutput,
    PassiveStreamRouteOutput,
    PassiveMailOutput
)

# ===================== General ==================== #
def get_parse_recurrence_chain():
    """
    Returns the chain for parsing recurrence.
    """
    prompt = PromptTemplate.from_template(template=PARSE_RECURRENCE_PROMPT)

    llm = get_chat_model(temperature=0.0).with_structured_output(TimeDeltaOutput)

    prompt = PromptTemplate.from_template(
        "Parse the recurrence from the following text: {text}"
    )

    return prompt | llm


# ======================================================= #
#                     Active Agent                        #
# ======================================================= #


# ==================== Decision (Router) Agent ==================== #

def get_router_chain(with_hil: bool = False):
    """
    Returns the router chain.
    Args:
        with_hil (bool): Whether to use the HIL prompt or not.
    """
    if with_hil:
        output_schema = RouteOutputWithHIL
        prompt_template = ROUTE_SUBTASKS_WITH_HIL_PROMPT
    else:
        output_schema = RouteOutput
        prompt_template = ROUTE_SUBTASKS_PROMPT

    llm = get_chat_model(temperature=0.0).with_structured_output(output_schema)
    prompt = PromptTemplate.from_template(
        prompt_template
    )

    return prompt | llm

# ==================== Schedule Agents ==================== #

def get_reformulate_schedule_query_chain():
    """
    Returns the chain for reformulating a schedule query.
    """
    prompt = PromptTemplate.from_template(
        REFORMULATE_SCHEDULE_QUERY_PROMPT
    )

    llm = get_chat_model(temperature=0.0).with_structured_output(ReformulateScheduleQueryOutput)

    return prompt | llm

def get_extract_event_details_chain(existing_subtasks_count):
    """
    Returns the chain for extracting event details.
    """
    prompt = PromptTemplate.from_template(
        SCHEDULE_SUBTASK_PROMPT if existing_subtasks_count <= 1 
        else SCHEDULE_SUBTASK_PROMPT + "\nIn reply: mention that you're talking this task (e.g. For the meeting with ...)"
    )
    llm = get_chat_model(temperature=0.0).with_structured_output(ScheduleOutput)

    return prompt | llm


def get_conflict_schedule_chain():
    """
    Returns the chain for successful scheduling.
    """
    prompt = PromptTemplate.from_template(
        CONFLICT_SCHEDULE_PROMPT
    )

    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)  # Extract the content from the response


def get_remider_message_chain():
    """
    Returns the chain for generating a reminder message.
    """
    prompt = PromptTemplate.from_template(
        REMINDER_MESSAGE_PROMPT
    )

    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)

# ==================== Conversation Agent ==================== #

def get_summarize_chat_chain(is_first_summary: bool = True, is_passive: bool = False):
    model = get_chat_model(temperature=0.0)
    if is_first_summary:
        prompt_template = FIRST_SUMMARY_PROMPT
    else:
        prompt_template = EXTEND_SUMMARY_PROMPT

    if is_passive:
        prompt_template += "\n\n* if the message has the role of 'user', it means that the assistant has generated this message from the context, so you should not include it in the summary."

    prompt = PromptTemplate.from_template(
        prompt_template,
    )
    parser = JsonOutputParser()
    return prompt | model | parser


# ==================== Update Agent ==================== #

def get_update_chain():
    """
    Returns the chain for updating a task.
    """
    prompt = PromptTemplate.from_template(
        UPDATE_SUBTASK_PROMPT
    )
    llm = get_chat_model(temperature=0.0).with_structured_output(Event)

    return prompt | llm


def get_fetch_request_chain():
    """
    Returns the chain for fetching a request.
    """
    prompt = PromptTemplate.from_template(
        FETCH_REQUEST_PROMPT
    )
    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)

def get_event_not_found_message_chain():
    """Returns the chain for generating an event not found message."""
    prompt = PromptTemplate.from_template(
        EVENT_NOT_FOUND_MESSAGE_PROMPT
    )
    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)

def get_event_updated_message_chain():
    """Returns the chain for generating an event updated message."""
    prompt = PromptTemplate.from_template(
        EVENT_UPDATED_MESSAGE_PROMPT
    )
    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)

def get_conflict_update_chain():
    """Returns the chain for generating a conflict update message."""
    prompt = PromptTemplate.from_template(
        CONFLICT_UPDATE_PROMPT
    )
    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)

def get_already_cancelled_message_chain():
    """Returns the chain for generating an already cancelled message."""
    prompt = PromptTemplate.from_template(
        ALREADY_CANCELLED_MESSAGE_PROMPT
    )
    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)

# ==================== Delete Agent ==================== #

def get_delete_subtask_chain():
    """Returns the delete subtask chain."""
    prompt = PromptTemplate.from_template(
        DELETE_SUBTASK_PROMPT
    )
    llm = get_chat_model(temperature=0.0).with_structured_output(DeleteOutput)

    return prompt | llm

def get_deleted_message_chain():
    """Returns the chain for generating a deleted message."""
    prompt = PromptTemplate.from_template(
        DELETED_MESSAGE_PROMPT
    )
    llm = get_chat_model(temperature=0.0)

    return prompt | llm | (lambda x: x.content)


# ======================================================= #
#                    Passive Agent                        #
# ======================================================= #

def get_passive_router_chain(type: Literal["stream", "clarification", "mail"] = "stream"):
    """
    Returns the chain for the passive stream router.
    """
    if type == "stream":
        prompt_template = PASSIVE_STREAM_ROUTE_SUBTASKS_PROMPT
        output_schema = PassiveStreamRouteOutput
    elif type == "clarification":
        raise ValueError("Unsupported passive router type")
    elif type == "mail":
        raise ValueError("Unsupported passive router type")
    else:
        raise ValueError(f"Unknown passive router type: {type}")
    prompt = PromptTemplate.from_template(
        prompt_template
    )

    llm = get_chat_model(temperature=0.0).with_structured_output(output_schema)

    return prompt | llm


def get_passive_mail_chain():
    """
    Returns the chain for the passive mail agent.
    """
    prompt = PromptTemplate.from_template(
        PASSIVE_EMAIL_ROUTE_SUBTASKS_PROMPT
    )

    llm = get_chat_model(temperature=0.0).with_structured_output(PassiveMailOutput)

    return prompt | llm