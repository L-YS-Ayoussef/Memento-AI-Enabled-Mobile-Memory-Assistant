from fastapi import APIRouter, WebSocket, status
import asyncio
from app.agents.builder import active_builder
from langchain_core.messages import HumanMessage
from app.core.security import get_current_user_ws
from app.settings import settings
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from datetime import datetime
import uuid

router = APIRouter(
    prefix="/agents",
    tags=["Agents"]
)


@router.websocket("/active")
async def active(websocket: WebSocket):
    await websocket.accept()

    user_data = await get_current_user_ws(websocket)
    if not user_data:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return


    try:
        data = await websocket.receive_json()
        msg = data.get("msg")
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # print("CURRENT DATETIME:", data.get("current_datetime"))

    async with AsyncPostgresSaver.from_conn_string(settings.STATE_DB_URL) as checkpointer:
        await checkpointer.setup()
        active_agent = active_builder.compile(checkpointer=checkpointer)
        
        async for node in active_agent.astream(
            {
                "recent_messages": [HumanMessage(content=msg)],
                "tenant_id": user_data.user_id,
                "waiting_subtasks": [],
                "existing_subtasks_count": 0,
                "recent_id": 0,
                "history_summary": "",
                "scheduled_event": {},
                "current_datetime": data.get("current_datetime")
            },
            config={"configurable": {"thread_id": user_data.user_id}}
        ):
            if not node: continue
            print(node)
            
            node_name, output = next(iter(node.items()))

            if node_name not in ["conversation_node", "schedule_node", "query_node", "update_node", "delete_node"]:
                continue

            response_dict = {
                "task": node_name.removesuffix("_node")
            }
            
            # add AI reply to the response
            messages = output.get("recent_messages", [])
            ai_reply = messages[0].content if messages else ""
            if ai_reply: response_dict.update({"reply": ai_reply})

            # add event details if available
            if scheduled_event := output.get("scheduled_event", {}):
                reminder_message = scheduled_event.pop("reminder_message", "")
                scheduled_event.update({
                    "id": uuid.UUID(scheduled_event.get("id", "")).int if scheduled_event.get("id") else None,
                })
                response_dict.update({
                    "event": scheduled_event,
                    "reminder_message": reminder_message
                })
            await websocket.send_json(response_dict)
            
    await websocket.close()