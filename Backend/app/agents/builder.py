from .nodes import route_subtasks, schedule_node, update_node, query_node, conversation_node, summarize_conversation_node, stream_reply_node, delete_node
from .state import OverallState
# from langgraph.checkpoint.memory import InMemorySaver
# from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph
# import asyncio
# import uuid
from app.settings import settings


# ====================== Active Agent ==================== #

active_builder = StateGraph(OverallState)

active_builder.add_node("router_node", route_subtasks)
active_builder.add_node("schedule_node", schedule_node)
active_builder.add_node("update_node", update_node) 
active_builder.add_node("delete_node", delete_node)
active_builder.add_node("query_node", query_node)
active_builder.add_node("stream_reply_node", stream_reply_node)
active_builder.add_node("conversation_node", conversation_node)
active_builder.add_node("summarize_conversation_node", summarize_conversation_node)

active_builder.set_entry_point("router_node")




active_agent = active_builder.compile() # checkpointer=InMemorySaver())

