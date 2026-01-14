# import structlog

# # from src.rag.topic_router import route_query_to_topics
# from schemas.agent_state import AgentState
# from utils.telemetry.decorators import traceable

# logger = structlog.get_logger()


# @traceable(name="router_node")
# def router_node(state: AgentState) -> AgentState:

#     logger.info("routing_query", query=state["topic_query"], subject=state["subject"])

#     try:
#         matched_topics = route_query_to_topics(
#             query=state["topic_query"], subject=state["subject"], grade=state["grade"]
#         )

#         state["matched_topics"] = matched_topics
#         state["step_logs"].append(f"Matched topics: {matched_topics}")

#         logger.info("routing_complete", topics_count=len(matched_topics))

#     except Exception as e:
#         logger.error("routing_failed", error=str(e))
#         state["errors"].append(f"Router error: {str(e)}")
#         state["matched_topics"] = []

#     return state
