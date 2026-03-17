from app.settings import settings
from .state import OverallState, SubtaskState, ConversationSubState, PassiveState
from langchain_core.messages import AIMessage, HumanMessage

from .utils.chains import (
# ================== Active Agent ================== #
    get_router_chain,
    get_reformulate_schedule_query_chain,
    get_extract_event_details_chain,
    get_summarize_chat_chain,
    get_update_chain,
    get_deleted_message_chain,
    get_event_not_found_message_chain,
    get_event_updated_message_chain,
    get_conflict_update_chain,
    get_delete_subtask_chain,
    get_fetch_request_chain,
    get_already_cancelled_message_chain,

# ================== Passive Agent ================== #
    get_passive_router_chain,
    get_passive_mail_chain
)
from .utils.helpers import (
    get_router_chain_inputs,
    add_clarifications,
    prepare_new_subtasks,
    cancel_subtasks,
    serialize_event_details,
    prepare_schedule_update,
    reformulate_query,
    event_details_to_str
)
from langgraph.types import Command, Send
from app.db.vector_store.vector_store import vector_store
from .utils.prompts import QUERY_SUBTASK_PROMPT
from datetime import datetime


# ======================================================= #
#                     Active Agent                        #
# ======================================================= #

# ==================== Decision (Router) Agent ==================== #

async def route_subtasks(state: OverallState):
    # [1] Decompose and classify the query into subtasks
    are_there_waiting_tasks = bool(state.get("waiting_subtasks", {}))
    router_chain = get_router_chain(with_hil=are_there_waiting_tasks)
    chain_inputs = get_router_chain_inputs(state)

    route_output = router_chain.invoke(chain_inputs)

    print("ROUTEEEEEEEEEEE OUTPUT")
    print(route_output)
    print("====================")

    ready_subtasks = []  # both new and waiting to be resumed

    # [2] Add clarification to the state
    if are_there_waiting_tasks and route_output.clarifications:
        clarified_subtasks = add_clarifications(state, route_output.clarifications)
        ready_subtasks.extend(clarified_subtasks)

    # [3] Add new subtasks to the state
    if route_output.sub_tasks:
        new_subtasks = prepare_new_subtasks(state, route_output.sub_tasks)
        ready_subtasks.extend(new_subtasks)

    # [4] handle cancels
    if are_there_waiting_tasks and route_output.cancels:
        cancel_subtasks(state, route_output.cancels)

    if ready_subtasks or route_output.reply:
        existing_task_count = len(ready_subtasks)
        gotos = [
            Send(
                task["type"] + "_node",
                {
                    "id": task["id"],
                    "query": task["query"],
                    "progress": task["progress"],
                    "existing_subtasks_count": existing_task_count,
                    "tenant_id": state.get("tenant_id", ""),
                    "current_datetime": task.get("current_datetime", "") or state.get("current_datetime", str(datetime.now()))
                }
            ) for task in ready_subtasks
        ]

        if route_output.reply:
            gotos.insert(0,  # at the beginning of the list
                         Send("conversation_node", {"ai_reply": route_output.reply})
                         )

        return Command(
            update={
                "recent_id": len(ready_subtasks),
                "existing_subtasks_count": existing_task_count,
            },
            goto=gotos
        )

    else:
        return Command(
            goto="__end__"
        )


# ===================== Schedule Agent ==================== #

async def schedule_node(state: SubtaskState):
    """
    Schedule task agent.
    """
    query = reformulate_query(state)

    extract_event_details_chain = get_extract_event_details_chain(state.get("existing_subtasks_count", 1))
    event_details = extract_event_details_chain.invoke({
        "query": query,
        "current_datetime": state.get("current_datetime", str(datetime.now()))
    })

    print("schedule task")
    print(event_details.ready)
    print(event_details.event)
    print(event_details.reply)

    print("EXTRACTED EVENT DETAILS")
    print(event_details)
    print("====================")

    email = state.get("email", None)

    update_dict = prepare_schedule_update(state, query, event_details.event, event_details.reply, vector_store,
                                          "schedule", event_details.ready, email)
    sched_event = update_dict.get("scheduled_event", {})
    if sched_event:
        reminder_msg = sched_event.get("reminder_message", "")
        if reminder_msg:
            print("Reminder message:")
            print(reminder_msg)
    print("====================")

    return Command(
        update=update_dict,
        goto="stream_reply_node"
    )


# ===================== Update Agent ==================== #

async def update_node(state: SubtaskState):
    """Update/Delete task agent."""

    query = reformulate_query(state)

    # [1] Get the targeted event from the vector store
    # TODO: handle the case of event in the interaction history
    # if update_details.event.id:
    #     # If the event ID is provided, use it directly
    #     targeted_event_id = update_details.event.id
    # else:
    # fetch_query = get_fetch_request_chain().invoke({
    #     "query": query
    # })
    fetch_query = ("You are currently given a prompt from the user to update an event, Find the targeted event that "
                   "corresponds to that user query"
                   f"user query: {query}"
                   "\nIn the final answer respond in a non-technical manner as I will send that answer to the user"
                   "\n * Consider the current datetime if you need it: "
                   f"{state.get('current_datetime', str(datetime.now()))}"
                   )
    print("========================================")
    print("update task")
    print("tenant_id:", state.get("tenant_id", ""))
    print("fetch_query:", fetch_query)
    print("====================")
    targeted_event_id, response = vector_store.get_task_uuid(
        state.get("tenant_id", ""),
        fetch_query
    )
    print("resposne:", response)
    targeted_event_id = str(targeted_event_id) if targeted_event_id else None

    print("Targeted event ID:")
    print(targeted_event_id)
    print("====================")

    # TODO: handle multiple events found 
    # for now we assume that the user has only one task with the same query

    if not targeted_event_id:
        # ai_reply = get_event_not_found_message_chain().invoke({
        #     "query": query
        # })

        return Command(
            update={
                "recent_messages": [AIMessage(content=response)], # ai_reply or "Task not found.")],
                "existing_subtasks_count": -1,
                "waiting_subtasks": [{
                    "id": state["id"],
                    "query": state["query"],
                    "type": "update",
                    "progress": f"{state['progress']}\nAI: {response}",    # ai_reply or "Task not found."}"
                    "current_datetime": state.get("current_datetime", str(datetime.now()))
                }]
            },
            goto="stream_reply_node"
        )

    # TODO: we must return the event details with the id, and check if it's a cancelled event -> return a message that the event is already cancelled
    # [2] Get the event details from the vector store
    is_cancelled = vector_store.get_event_details(state.get("tenant_id"), targeted_event_id).get("cancelled", False)
    if is_cancelled:
        ai_reply = get_already_cancelled_message_chain().invoke({
            "query": query
        })
        return Command(
            update={
                "recent_messages": [AIMessage(content=ai_reply or "Task already cancelled.")],
                "existing_subtasks_count": -1,
                "waiting_subtasks": [{
                    "id": state["id"],
                    "query": state["query"],
                    "type": "update",
                    "progress": f"{state['progress']}\nAI: {ai_reply or 'Task already cancelled.'}",
                    "current_datetime": state.get("current_datetime", str(datetime.now()))
                }]
            },
            goto="stream_reply_node"
        )

    event_dict = vector_store.get_event_details(state.get("tenant_id"), targeted_event_id)

    event = get_update_chain().invoke({
        "update_request": query,
        "event_details": event_details_to_str(event_dict, False),
        "current_datetime": state.get("current_datetime")
    })
    # we can pass the response directly to the update_dict instead of None
    update_dict = prepare_schedule_update(state, query, event, None, vector_store, "update", ready=True,
                                          event_id=targeted_event_id)

    return Command(
        update=update_dict,
        goto="stream_reply_node"
    )


# ===================== Delete Agent ==================== #

async def delete_node(state: SubtaskState):
    """Delete task agent."""
    query = reformulate_query(state)

    # [1] Get the targeted event from the vector store
    # fetch_query = get_fetch_request_chain().invoke({
    #     "query": query
    # })
    fetch_query = ("You are currently given a prompt from the user to delete an event, Find the targeted event that "
                   "corresponds to that user query"
                   f"user query: {query}"
                   "\nIn the final answer respond in a non-technical manner as I will send that answer to the user"
                   f"\n * Consider the current datetime if you need it: "
                   f"{state.get('current_datetime', str(datetime.now()))}"
                   )
    print("Fetch Query: ", fetch_query)
    targeted_event_id, response = vector_store.get_task_uuid(
        state.get("tenant_id", ""),
        fetch_query
    )
    print(targeted_event_id)
    print("response: ", response)
    targeted_event_id = str(targeted_event_id) if targeted_event_id else None
    print("Targeted event ID:")
    print(targeted_event_id)
    print("====================")

    if not targeted_event_id:
        # ai_reply = get_event_not_found_message_chain().invoke({
        #     "query": query,
        # })

        return Command(
            update={
                "recent_messages": [AIMessage(content= response)],     # ai_reply or "Task not found.")],
                "existing_subtasks_count": -1,
                "waiting_subtasks": [{
                    "id": state["id"],
                    "query": state["query"],
                    "type": "delete",
                    "progress": f"{state['progress']}\nAI: {response}",     # {ai_reply or 'Task not found.'}"
                    "current_datetime": state.get("current_datetime", str(datetime.now()))
                }]
            },
            goto="stream_reply_node"
        )
    
    # TODO: we must return the event details with the id, and check if it's a cancelled event -> return a message that the event is already cancelled

    # [2] Delete the task from the vector store
    deleted, _ = vector_store.update_task_info(
        state.get("tenant_id", ""),
        targeted_event_id,
        {"cancelled": True}
    )
    updates = {}
    if deleted:
        deleted_message = get_deleted_message_chain().invoke({
            "query": query,
        })
        updates.update({
            "scheduled_event": {"id": targeted_event_id}
        })
    else:
        deleted_message = f"Couldn't delete the task."  # TODO: retry to delete the task in the vector store

    updates.update({
            "recent_messages": [AIMessage(content=deleted_message)],
            "existing_subtasks_count": -1
        })
    return Command(
        update=updates,
        goto="stream_reply_node"
    )


# ===================== Query Agent ==================== #

async def query_node(state: SubtaskState):
    """
    Query task agent.
    """
    tenant_id = state.get("tenant_id", "")
    query = QUERY_SUBTASK_PROMPT.format(query=state.get("query", "")) + f"\n * Consider the current datetime if you need it: {state.get('current_datetime', str(datetime.now()))}"

    print("========================================")
    print("query task")
    print("tenant_id:", tenant_id)
    print("query:", query)

    reply = vector_store.run_tenant_query(tenant_id, query).final_answer

    return Command(
        update={"recent_messages": [AIMessage(content=reply)], "existing_subtasks_count": - 1},
        goto="stream_reply_node"
    )


# ===================== Conversation Agent ==================== #

async def conversation_node(state: ConversationSubState):
    """
    Conversation task agent.
    """
    print("conversation task")

    update_dict = {}
    ai_reply = state.get("ai_reply", None)

    print("AI reply:")
    print(ai_reply)

    if ai_reply:
        update_dict["recent_messages"] = [AIMessage(content=ai_reply)]

    return Command(
        update=update_dict,
        goto="stream_reply_node"
    )


async def stream_reply_node(state: OverallState):
    return Command(goto="summarize_conversation_node")


async def summarize_conversation_node(state: OverallState):
    """
    Summarize the conversation or end.
    """
    if len(state.get("recent_messages", [])) <= settings.MESSAGE_SUMMARY_TRIGGER:
        return Command(goto="__end__")

    summary = state.get("history_summary", "")

    old_messages = state["recent_messages"][:-settings.MAX_KEPT_MESSAGES]
    recent_messages = state["recent_messages"][-settings.MAX_KEPT_MESSAGES:]

    messages_text = "\n".join(f"{msg.type}: {msg.content}" for msg in old_messages)

    summary = get_summarize_chat_chain(
            is_first_summary=bool(summary), 
            is_passive=False
        ).invoke({
            "history_summary": state.get("history_summary", ""),
            "messages": messages_text
    })

    state["recent_messages"] = recent_messages
    state["history_summary"] = summary


# ======================================================= #
#                    Passive Agent                        #
# ======================================================= #

async def passive_router_node(state: PassiveState):
    """
    Passive router node.
    """
    print("Passive router node")
    print("Router:", state.get("router", ""))

    if state.get("router") == "stream":
        return Command(goto="passive_stream_node")
    elif state.get("router") == "clarification":
        return Command(goto="passive_clarification_node")
    elif state.get("router") == "mail":
        return Command(goto="passive_mail_node")

    return Command(goto="__end__")


async def passive_stream_router_node(state: PassiveState):
    """
    Passive stream router node.
    """
    print("Passive stream router node")
    print("Stream summary:", state.get("stream_summary", ""))

    if not state.get("stream_summary"):
        return Command(goto="__end__")

    chain = get_passive_router_chain(type="stream")

    recent_messages = "\n".join(
        f"{msg.type}: {msg.content}" for msg in state.get("recent_messages", [])
    )

    output = chain.invoke({
        "history_summary": state.get("history_summary", ""),
        "recent_messages": recent_messages,
        "stream_summary": state.get("stream_summary", ""),
        "new_stream": state.get("new_stream", ""),
    })
    updates = {
        "stream_summary": output.new_stream_summary if output.new_stream_summary else state.get("stream_summary", ""),
        "new_stream": ""
    }

    if not output.subtasks:
        return Command(
            update=updates,
            goto="__end__"
        )
    
    ready_subtasks = prepare_new_subtasks(state, output.subtasks, agent_type="passive")
    
    user_message = ", ".join(
        f"{task['query']}" for task in ready_subtasks
    )
    updates.update({
        "recent_messages": [HumanMessage(content=user_message)]
    })

    return Command(
        update=updates,
        goto=[
            Send(
                task["type"] + "_node",
                {
                    "id": task["id"],
                    "query": task["query"],
                    "progress": task["progress"],
                    "existing_subtasks_count": 2,       # any number larger than 1
                    "tenant_id": state.get("tenant_id", ""),
                    "current_datetime": state.get("current_datetime", str(datetime.now()))
                }
            ) for task in ready_subtasks
        ]
    )


async def passive_clarification_router_node(state: PassiveState):
    """ Passive clarification router node."""
    print("Passive clarification router node")
    print("Clarifications:", state.get("clarification", ""))

    if not state.get("clarification"):
        return Command(goto="__end__")

    # TODO: get the subtask by ID {"type": "", "query": "", "progress": "", "added_at": ""}
    subtask = {}

    progress = subtask.get("progress", "") + "\nUser: {state.get('clarification', '')}"

    return Command(
        update={
            "task_id": None,
            "clarification": ""
        },
        goto= Send(
            subtask["type"] + "_node",
            {
                "id": subtask["id"],
                "query": subtask["query"],
                "progress": progress,
                "existing_subtasks_count": 2,       # any number larger than 1
                "tenant_id": state.get("tenant_id", ""),
                "current_datetime": subtask.get("added_at", "") or state.get("current_datetime", str(datetime.now()))
            }
        )
    )


async def passive_mail_router_node(state: PassiveState):
    """ Passive mail router node."""
    print("Passive mail router node")
    print("Mail:", state.get("mail", ""))

    mail = state.get("mail", {})
    if not mail:
        return Command(goto="__end__")
    
    output = get_passive_mail_chain().invoke({
        "email_content": mail.get("content", ""),
        })
    
    if not output.subtasks:
        return Command(
            update={
                "mail": {}
            },
            goto="__end__"
        )
    
    ready_subtasks = prepare_new_subtasks(state, output.subtasks, agent_type="passive")
    

    return Command(
        update={
            "mail": {}
        },
        goto=[
            Send(
                task["type"] + "_node",
                {
                    "id": task["id"],
                    "query": task["query"],
                    "progress": task["progress"],
                    "existing_subtasks_count": 2,       # any number larger than 1
                    "tenant_id": state.get("tenant_id", ""),
                    "current_datetime": state.get("current_datetime", str(datetime.now())),
                    "email": mail  # pass the email to the subtask
                }
            ) for task in ready_subtasks
        ]
    )

# ==================== Passive Conversation Agent ==================== #

async def passive_stream_reply_node(state: PassiveState):
    return Command(goto="summarize_conversation_node")


async def Passive_summarize_conversation_node(state: PassiveState):
    """
    Summarize the conversation or end.
    """
    if len(state.get("recent_messages", [])) <= settings.MESSAGE_SUMMARY_TRIGGER:
        return Command(goto="__end__")

    summary = state.get("history_summary", "")

    old_messages = state["recent_messages"][:-settings.MAX_KEPT_MESSAGES]
    recent_messages = state["recent_messages"][-settings.MAX_KEPT_MESSAGES:]

    messages_text = "\n".join(f"{msg.type}: {msg.content}" for msg in old_messages)

    summary = get_summarize_chat_chain(
            is_first_summary=bool(summary), 
            is_passive=True
        ).invoke({
            "history_summary": state.get("history_summary", ""),
            "messages": messages_text
    })

    state["recent_messages"] = recent_messages
    state["history_summary"] = summary
