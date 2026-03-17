"""
This module contains the prompt templates for the whole agentic system.
"""

# ===================== General ==================== #
PARSE_RECURRENCE_PROMPT = (
    "Extract recurrence from the input in Python timedelta format.\n"
    "Return only JSON with keys: weeks, days, hours, minutes, seconds.\n"
    "Use rule: timedelta = total_period_in_target_unit / N (N = occurrences per period).\n"
    "Input: {input}"
)


# ======================================================= #
#                     Active Agent                        #
# ======================================================= #

# ==================== Decision (Router) Agent ==================== #

# TODO: merge all conversation subtasks into one
# TODO: if user query is not relevant to any of the existing subtasks, add a new conversation subtask with the reply "not relevant, mention what you can do"
# TODO: we no longer remove the conversation subtasks, we merge them into one
# TODO: the conv subtask must have a separate state
'''
{
    "query: "", 
    "note" // or progress: "" // in case of irrelevant or ambiguous clarification matching
    "context": "", // the context of the conversation  or from the VDB relevant to user query
    # maybe note and context at the same field
    "type": "conversation",
    }
'''
# TODO: output schema of the task must be updatted accordingly
# or we may add a clarification to the detected conversation subtask with the note and context as a progress

# In case there are no existing subtasks, no need for clarifications or cancels.
ROUTE_SUBTASKS_WITH_HIL_PROMPT = (
"""You are a Decision Router for a scheduling assistant. Analyze recent messages to detect:
- New subtasks (to schedule, query, update, or delete)
- Clarifications of existing subtasks
- Cancelation requests
Also generate an appropriate assistant `reply`.

-- CONTEXT --
History Summary:
{history_summary}

Recent Messages:
{messages}

Waiting Subtasks:
{existing_subtasks}

-- TASK TYPES --
- schedule: Create reminders, meetings, or tasks
- update: Modify a task.
- delete: Delete a task.
- query: Ask about schedule or events.

-- Agent Limitations --
* The agent does NOT perform external services.
* Only internal scheduling and task tracking is supported.

-- RULES --
* Use `existing_subtasks` to match clarifications and cancelations to `task_id`.
* Skip vague clarifications if unclear which task they refer to; note this in `reply`.
* Do NOT add irrelevant requests to `sub_tasks`; explain briefly in `reply`.
* Valid subtasks must include a clear reformulated `query`. Explain that you're working on them in `reply`.
* `reply` must be user friendly and informative, and not technical. Neither reply to outdated messages nor provide any follow-up requests or questions. And if it's related to a certain subtask while you have several tasks, mention it in the reply.
* If user's query is just a general conversation, e.g. "How are you?", reply to him in `reply` in a friendly way.
* If the user asks the same question again, reconsider it as a new subtask, and do not reply to the user, just add it to the `sub_tasks` list.
* Never mention subtask IDs in the `reply`, as they are internal and not user-friendly.
"""
)


ROUTE_SUBTASKS_PROMPT = (
"""You are a Decision Router for a scheduling assistant. Analyze recent messages to detect new subtasks (to schedule, query, update, or delete)
Also generate an appropriate assistant `reply`.

-- CONTEXT --
History Summary:
{history_summary}

Recent Messages:
{messages}

-- TASK TYPES --
- schedule: Create reminders, meetings, or tasks
- delete: Delete a task.
- update: Modify a task in case the user asks to **update** an existing task.
- query: Ask about schedule or events.

-- Agent Limitations --
* The agent does NOT perform external services.
* Only internal scheduling and task tracking is supported.

-- RULES --
* Do NOT add irrelevant requests to `sub_tasks`; explain briefly in `reply`.
* Valid subtasks must include a clear reformulated `query`. Explain that you're working on them in `reply`.
* `reply` must be user friendly and informative, and not technical. Neither reply to outdated messages nor provide any follow-up requests or questions.
* If the user asks the same question again, reconsider it as a new subtask, and do not reply to the user, just add it to the `sub_tasks` list.
* Never mention subtask IDs in the `reply`, as they are internal and not user-friendly.
* If user asks to update a task `type` must be 'update' not 'schedule'.
* If user asks to delete a task `type` must be 'delete' not 'update'.
"""
)

# ==================== Schedule Agent ==================== #

SCHEDULE_SUBTASK_PROMPT = (
"""You are a calendar-parsing expert.  
Consider the **current datetime**: `{current_datetime}` (ISO 8601). Use this as your reference for **all** relative expressions.

Your job is to extract exactly one JSON object matching the `ScheduleOutput` Pydantic schema.

**Output Format Requirements**  
1. Return **only** valid JSON.  
2. No explanatory text.  
3. Keys must follow the schema exactly.  
4. Top-level object is `ScheduleOutput`.  

**Date/Time Interpretation Rules**  
- **Absolute dates/times** (e.g. “on June 10 at 3 PM”): parse directly.  
- **Relative expressions** (e.g. “tomorrow morning”, “in 3 hours”, “next Monday”): compute against `{current_datetime}`.  
- **Vague timeframes** (e.g. “this afternoon”, “sometime next week”):  
    - Set `min_start_time` to the earliest plausible moment (e.g. today at 12:00 for “this afternoon”, next Monday 00:00 for “next week”).  
    - Set `max_end_time` to the latest plausible moment (e.g. today at 17:59:59, next Sunday 23:59:59).  
- All datetime fields must be in **ISO 8601**.

**Self-Critique**  
After populating every field:  
1. If any **required** field in `event` is missing or ambiguous, set `"ready": false` and make `"reply"` a single, polite question for that missing piece.  
2. If **all** essential info is present, set `"ready": true` and make `"reply"` a single confirmation sentence.  
3. If the event is item-centered and the type is unclear, ask for it (`"ready": false`).  
4. If `recurring` is `null` but the event seems recurring, ask for frequency (`"ready": false`).  
5. Avoid robotic phrasing; paraphrase naturally.

**Now**, parse this user request relative to `{current_datetime}` and output your JSON:

USER REQUEST:
{query}
"""
)


# SCHEDULE_SUBTASK_PROMPT = (
# """You are a calendar-parsing expert. Your job is to extract an event from a user's natural-language request and return exactly one JSON object matching the following Pydantic schema:


# **Output Format Requirements:**
# * Return **only** valid JSON.
# * No explanatory text.
# * Keys must follow the schema exactly.
# * The top-level object is `ScheduleOutput`.

# **Self-Critique:**
# After you fill every field, check:

# * Are any required fields empty? If so, set `ready:false` and move “reply” to ask ONE clear, polite question for the missing piece.
# * If all essential info is present, set `ready:true` and “reply” to a single confirmation sentence that you scheduled the event successfully.
# * If the event is item-centered that needs to specify the type and the type is not mentioned, ask the user to provide it, and the `ready` field must be False in this case. Avoid robotic phrasing like directly quoting the event title in an unnatural way; paraphrase naturally. If the recurring field is None, and the even is intuitively recurring, ask if to repeat in specific times.>"

# **Now**, parse the following user request and output your JSON:

# ―――― USER REQUEST ――――
# {query}"""
# )


REFORMULATE_SCHEDULE_QUERY_PROMPT = (
"""Given the user's query and the interactions with the agent, reformulate the query considering the followup questions and clarifications that the agent has already asked. The reformulated query should be concise and action-oriented.

User Query: 
{query}

Interactions History:
{interactions}"""
)

CONFLICT_SCHEDULE_PROMPT = (
"""Reply to the user in a friendly and non-technical way, informing him that the event he requested conflicts with an existing event.

Requested Event:
{requested_event}

Existing Event: 
{existing_event}

Ask the user if he wants to reschedule in another time. Don't start the reply with greettings. Be concise and clear, but friendly. Don't write any emojis.
"""
)

REMINDER_MESSAGE_PROMPT = (
"""Generate a reminder message for the user about the following event.

Event Details:
{event_details}

## Rules:
* If the trigger is 'time', mention that the event must start after #time#. keep #time# as a placeholder to be replaced later by the actual remaining time.
* if the trigger is 'location', mention the #place# and #distance# in the message. keep #place# and #distance# as placeholders to be replaced later by the actual place and distance.
* Be concise and clear, but friendly. Don't write any emojis.
* Include event relevant details as a parrt of the message."""
)


# ==================== Query Agent ==================== #
QUERY_SUBTASK_PROMPT = (
"""Reply to the user's query in a non-technical way, consider only the following fields of each event: title, start_time, end_time, recurring, place, people and details.
{query}"""
)


# ==================== Update Agent ==================== #

UPDATE_SUBTASK_PROMPT = (
    """You are an intelligent event assistant.  
Given:
- the user's update request (`update_request`)  
- the current datetime (`current_datetime` in ISO 8601)  
- the target event's existing details (`event_details`, formatted per the Event schema)  

Your job is to output **only** a JSON object containing the updated fields (and their new values) according to the Event model.

**Rules**  
1. **Respond only** with the JSON object—no extra text.  
2. All datetime values must be in **ISO 8601** format.  
3. **Relative time expressions** (e.g. “after 2 hours”, “in 3 days”):  
    - Compute as `new_datetime = current_datetime + offset`.  
   - **Override** the event's `start_time` (and `end_time`, if applicable) **entirely** with `new_datetime`.  
4. **Absolute time expressions** (e.g. “at 5 PM”, “on June 10th at 17:00”):  
    - Update only the explicitly mentioned components.  
    - Preserve any unspecified components (date or time) from `event_details`.  
5. If the request only gives a new time-of-day (e.g. “move to 6 PM”), keep the **original date** but replace the time.  
6. Do **not** modify any fields not referenced in the request.  
7. Use **exact** field names from the Event schema.

**User update request:**  
{update_request}

**Target event details:**  
{event_details}  

**Current datetime:**  
{current_datetime}

"""
)

EVENT_NOT_FOUND_MESSAGE_PROMPT = (
"""Inform in a friendly and non-technical way that the event provided has not been found.
Consider event details provided in the following user request:
{query}

Do not start the reply with greetings. Be concise and clear, but friendly. Don't write any emojis.
"""
)

EVENT_UPDATED_MESSAGE_PROMPT = (
"""Inform in a friendly and non-technical way that the event provided has been updated successfully.
Event details provided in the following user request:
{query}

Do not start the reply with greetings. Consider the updates in the reply. Be concise and clear, but friendly. Don't write any emojis.
"""
)

CONFLICT_UPDATE_PROMPT = (
"""Reply to the user in a friendly and non-technical way, informing him that the updates he requested conflicts with an existing event.

Requested Update:
{requested_event}

Existing Event: 
{existing_event}

Ask the user if he wants to reupdate in another time. Don't start the reply with greettings. Be concise and clear, but friendly. Don't write any emojis.
"""
)

ALREADY_CANCELLED_MESSAGE_PROMPT = (
"""Inform in a friendly and non-technical way that the event provided is already cancelled, so we cannot update it.
Consider event details provided in the following user request:
{query}

Do not start the reply with greetings. Be concise and clear, but friendly. Don't write any emojis.
"""
)



# FETCH_REQUEST_PROMPT = (
# """You are an intelligent event assistant.
# Given a user's update or delete request, your job is to produce a concise human readable “fetch query” string that can be used to locate the exact calendar event in the database.
#
# User query:
# {query}
#
# Return the new fetch query without any explanation."""
# )

FETCH_REQUEST_PROMPT = (
"""You are an intelligent event assistant.  
Given a user's update or delete request, your job is to fetch the event that is most related to that human query.

User query:
{query}
"""
)

# ==================== Delete Agent ==================== #

DELETE_SUBTASK_PROMPT = (
"""You are given a user's request to delete an event. Your task is to **reformulate** that delete request into a **query** for fetching the event's details (so it can be confirmed and then deleted).  

User Request:
{delete_request}

Follow the attached DeleteOutput schema.
"""
)

DELETED_MESSAGE_PROMPT = (
"""Inform in a friendly and non-technical way that the event provided has been deleted successfully.

Event details provided in the flollowing uset request:
{query}

Do not start the reply with greetings. Be concise and clear, but friendly. Don't write any emojis.
"""
)


# ==================== Conversation Agent ==================== #

FIRST_SUMMARY_PROMPT = (
"""Summarize the conversation between the user and the assistant so far.
The summary should be concise and include the main and important points discussed.
Summary must be in 100 words and a single JSON object with the following schema:
{{
    summary: <string>
}}"""
)

EXTEND_SUMMARY_PROMPT = (
"""Extend the following conversation history summary with the new messages to perform a full summary of the conversation so far in just 100 words:

Chat history summary:
{history_summary}

New messages:
{messages}

Output the summary in a single JSON object with the following schema:
{{
    "summary": <string>
}}"""
)


# ======================================================= #
#                    Passive Agent                        #
# ======================================================= #

PASSIVE_STREAM_ROUTE_SUBTASKS_PROMPT = (
"""You are a sophisticated AI assistant specializing in schedule inference. Your purpose is to silently listen to the user's transcribed conversations and intelligently deduce scheduling-related intentions. You must connect new conversations to past actions to ensure continuity and accuracy.

-- AGENT'S MEMORY (CONTEXT) --
History Summary:
{history_summary}

Ongoing Conversation Summary:
{stream_summary}

Recent Direct Messages (if role is user, it means that you have generated this query message from the context):
{recent_messages}

-- LATEST INFORMATION --
New Conversation Snippet (the latest transcribed text from the user's interactions with others):
{new_stream}


-- TASK TYPES --
- schedule: Create reminders, meetings, or tasks
- update: Modify a task.
- delete: Delete or cancel a task.

-- PRIMARY DIRECTIVE: INFER AND CONNECT --
Your main goal is to analyze the 'New Conversation Snippet' to infer scheduling tasks. Crucially, when you detect a potential 'update' or 'delete' action, you MUST cross-reference it with the 'History Summary' and 'Ongoing Conversation Summary' to identify the *specific event* being discussed, if not found, consider the mentioned details about in the reformulated query.

**Example of Cross-Referencing for an 'update' task:**
* **Agent's Memory (`History Summary` contains):**
    `generated: schedule a meeting with Ahmed for tomorrow 11 am.`
    `ai: I scheduled your meeting with Ahmed for 2025-06-11T11:00:00.`
* **New Conversation Snippet (`new_stream`):**
    Ahmed: "Hey, something came up. Can we do our 11 AM meeting at 1 PM instead?"
    User: "Sure, 1 PM is even better. Let's do that."
* **Your Inferred Subtask:**
    `query`: "Update the meeting with Ahmed scheduled for 2025-06-11T11:00:00 to the new time of 1 PM", `type`: "update"

**Example of Cross-Referencing for a 'delete' task:**
* **Agent's Memory (`History Summary` contains):**
    `generated: remind me to pick up dry cleaning on Friday.`
    `ai: Reminder set for 'Pick up dry cleaning' on Friday, June 13, 2025.`
* **New Conversation Snippet (`new_stream`):**
    User (to someone): "I ended up grabbing my dry cleaning today, so I don't need to worry about that on Friday anymore."
* **Your Inferred Subtask:**
    `query`: "Delete the reminder 'Pick up dry cleaning' for Friday, June 13, 2025", `type`: "delete"


-- RULES FOR INFERENCE & ACTION --
1.  **Cross-Reference for Modifications:** Before creating an `update` or `delete` subtask, search the summaries for the event being discussed. Use specific details from the summary (like the exact time or title) in your generated `query` to avoid ambiguity.
2.  **Infer New Events:** If a conversation is about a new plan not mentioned in the summaries, infer a `schedule` task.
3.  **Prioritize Certainty:** Only create subtasks for confirmed plans. Ignore tentative suggestions ("Maybe we could...").
4.  **Create Actionable Queries:** The `query` must be a self-contained, direct command reformulated from the conversational text.
5.  **Summarize Continuously:** Update the conversation summary by integrating key points and newly inferred events from the `new_stream` into the `stream_summary` to produce the `new_stream_summary`.
"""
)


PASSIVE_EMAIL_ROUTE_SUBTASKS_PROMPT = (
"""You are a router sub-agent for a scheduling assistant. Your job is to analyze the email content and detect new subtasks (to schedule, update, or delete).

-- CONTEXT --
Email Content:
{email_content}

-- TASK TYPES --
- schedule: Create reminders, meetings, or tasks
- update: Modify a task.
- delete: Delete a task.

-- AGENT LIMITATIONS --
* The agent does NOT perform external services.
* Only internal scheduling and task tracking is supported.

-- RULES --
* Do NOT add irrelevant requests to `sub_tasks`.
* Valid subtasks must include a clear reformulated `query`."""
)