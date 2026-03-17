from app.agents.nodes import route_subtasks, schedule_node, update_node, query_node, conversation_node
from app.agents.state import OverallState
from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import StateGraph, END
import asyncio


def test_route_subtasks():
    # Test the route_subtasks function
    import datetime
    time = datetime.datetime.now()
    print(f"Current time: {time}")
    messages= [
        ("user", "how are u today. I need to schedule a meeting with Ahmed tomorrow, and I need to know my schedule today."),
        ("ai", "user tasks: 1. schedule a meeting with Ahned tomorrow.\n2. query today's schedule."),
        ("ai", "Could you tell the exact time and duration of the meeting with Ahmed, and where?"),
        # ("user", "actually forget about it. and i need to meet Ali next week. And tell me my schedule for tomorrow."),
        ("user", "1 pm for 1 hour. and i need to meet Ali next week in Paris for 2 hours. And tell me my schedule for tomorrow."),
        # ("user", "Good mornng. Can you book me a flight ticket, and what is my schedule for tomorrow?"),
    ]


    state = OverallState(
        history_summary="",
        recent_messages=[
            AIMessage(content=msg[1], role=msg[0]) if msg[0] == "ai" else HumanMessage(content=msg[1], role=msg[0]) for msg in messages 
        ],
        running_subtasks=[
            {
                "id": 2,
                "query": "query today's schedule",
                "type": "query",
                "progress": ""
            }
        ],
        waiting_subtasks=[
            {
                "id": 1,
                "query": "schedule a meeting with Ahmed tomorrow.",
                "type": "schedule",
                "progress": ""
            }
        ],
        recent_id=2
    )
    

    builder = StateGraph(OverallState)

    builder.add_node("start", route_subtasks)
    builder.add_node("schedule_node", schedule_node)
    builder.add_node("update_node", update_node)
    builder.add_node("query_node", query_node)
    builder.add_node("conversation_node", conversation_node)

    builder.set_entry_point("start")

    # for node in [
    #     "schedule_node",
    #     "update_node",
    #     "query_node",
    #     "conversation_node"
    # ]:
    #     builder.add_edge(node, END)
    

    checkpointer = InMemorySaver()


    agent = builder.compile(checkpointer=checkpointer)

    config = {
        "configurable": {
            "thread_id": "1"
        }
    }

    # for event in agent.stream(state, config):
    #     for k, v in event.items():
    #         if k != "__end__":
    #             print(v)

    state_ =  asyncio.run(agent.ainvoke(state, config))
    print(state_)

    time2 = datetime.datetime.now()
    print(f"Current time: {time2}")
    print(f"Time elapsed: {time2 - time}")

if __name__ == "__main__":
    test_route_subtasks()