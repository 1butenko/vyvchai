# import structlog

# # from src.generation.lesson_gen import LessonGenerator
# from schemas.agent_state import AgentState
# from utils.telemetry import traceable

# logger = structlog.get_logger()
# # lesson_gen = LessonGenerator()


# @traceable(name="content_gen_node")
# def content_gen_node(state: AgentState) -> AgentState:

#     logger.info("generating_lesson", topic=state["topic_query"])

#     try:
#         result = lesson_gen.generate(
#             topic=state["topic_query"],
#             docs=state["retrieved_docs"],
#             profile=state.get("student_profile"),
#             grade=state["grade"],
#             subject=state["subject"],
#         )

#         state["lesson_content"] = result["content"]
#         state["lesson_sources"] = result["sources"]
#         # original long line split for readability:
#         # state["step_logs"].append(
#         #     f"Generated lesson ({len(result['content'])} chars)"
#         # )

#         logger.info("lesson_generation_complete")

#     except Exception as e:
#         logger.error("lesson_generation_failed", error=str(e))
#         state["errors"].append(f"Content gen error: {str(e)}")
#         state["lesson_content"] = ""
#         state["lesson_sources"] = []

#     return state
