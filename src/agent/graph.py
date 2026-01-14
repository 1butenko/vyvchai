from typing import Any, Dict

import structlog

from src.agent.qa_agent import QualityAssuranceAgent
from src.agent.supervisor import SupervisorAgent
from src.agent.tools.rag_tool import RAGTool
from src.core.config import get_settings
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class MultiAgentOrchestrator:
    """
    Main orchestrator for the multi-agent system.
    """

    def __init__(self):
        self.supervisor = SupervisorAgent()
        self.qa_agent = QualityAssuranceAgent()
        self.rag_tool = RAGTool()
        self.max_regeneration_attempts = get_settings().MAX_REGENERATION_ATTEMPTS

        logger.info("multi_agent_orchestrator_initialized")

    async def process_request(self, initial_state: Dict[str, Any]) -> AgentState:
        """
        Process a tutoring request using the multi-agent system.

        Args:
            initial_state: Initial agent state

        Returns:
            Final processed state
        """
        logger.info("processing_request", request_id=initial_state.get("request_id"))

        # Initialize state
        state: AgentState = {
            "request_id": initial_state["request_id"],
            "class_id": initial_state["class_id"],
            "tenant_id": initial_state["class_id"],  # Using class_id as tenant_id
            "student_id": initial_state["student_id"],
            "teacher_id": initial_state["teacher_id"],
            "grade": initial_state["grade"],
            "subject": initial_state["subject"],
            "topic_query": initial_state["topic_query"],
            "student_profile": initial_state.get("student_profile"),
            "matched_topics": [],
            "retrieved_docs": [],
            "lesson_content": "",
            "lesson_sources": [],
            "quiz": [],
            "solver_feedback": {},
            "validation_passed": False,
            "regeneration_count": 0,
            "student_answers": initial_state.get("student_answers"),
            "grading_result": None,
            "recommendations": None,
            "trace_id": initial_state.get("trace_id", ""),
            "step_logs": [],
            "errors": [],
        }

        try:
            # Step 1: RAG - Retrieve relevant context
            state = await self._retrieve_context(state)

            # Step 2: Plan execution with supervisor
            plan = await self.supervisor.plan_execution(state)

            # Step 3: Execute plan
            state = await self.supervisor.execute_plan(state, plan)

            # Step 4: Quality assurance
            feedback = await self.qa_agent.validate_content(state)

            # Step 5: Regeneration loop if needed
            state["solver_feedback"] = feedback

            while (
                not feedback["valid"]
                and state["regeneration_count"] < self.max_regeneration_attempts
            ):
                logger.info(
                    "regenerating_content", attempt=state["regeneration_count"] + 1
                )

                state["regeneration_count"] += 1

                # Ask supervisor if regeneration is needed
                should_regenerate = await self.supervisor.should_regenerate(state)

                if not should_regenerate:
                    break

                # Re-plan and execute
                plan = await self.supervisor.plan_execution(state)
                state = await self.supervisor.execute_plan(state, plan)

                # Re-validate
                feedback = await self.qa_agent.validate_content(state)
                state["solver_feedback"] = feedback

            state["validation_passed"] = feedback["valid"]

            logger.info(
                "request_processing_completed",
                valid=state["validation_passed"],
                regenerations=state["regeneration_count"],
            )

        except Exception as e:
            logger.error("request_processing_failed", error=str(e))
            state["errors"].append(f"Processing failed: {str(e)}")

        return state

    async def _retrieve_context(self, state: AgentState) -> AgentState:
        """Retrieve relevant context using RAG."""
        logger.info("retrieving_context", query=state["topic_query"])

        try:
            docs = await self.rag_tool.retrieve_context(
                query=state["topic_query"],
                subject=state["subject"],
                grade=state["grade"],
                matched_topics=state.get("matched_topics", []),
                limit=5,
            )

            state["retrieved_docs"] = docs
            state["step_logs"].append(f"Retrieved {len(docs)} documents")

            logger.info("context_retrieved", count=len(docs))

        except Exception as e:
            logger.error("context_retrieval_failed", error=str(e))
            state["errors"].append(f"RAG error: {str(e)}")

        return state


# Global orchestrator instance
orchestrator = MultiAgentOrchestrator()
