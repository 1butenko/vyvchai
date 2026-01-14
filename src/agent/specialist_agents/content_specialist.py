import structlog

from src.agent.prompts.content_prompts import (
    LESSON_GENERATION_PROMPT,
    QUIZ_GENERATION_PROMPT,
)
from src.llm.router import llm_router
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class ContentSpecialist:
    """
    Specialist agent for generating educational content and quizzes.
    """

    async def execute(self, state: AgentState) -> AgentState:
        """
        Generate content based on current state.

        Args:
            state: Current agent state

        Returns:
            Updated state with generated content
        """
        # Determine what to generate
        if not state.get("lesson_content"):
            # Generate lesson content
            state = await self._generate_lesson(state)
        elif not state.get("quiz"):
            # Generate quiz
            state = await self._generate_quiz(state)
        else:
            logger.info("content_already_generated")

        return state

    async def _generate_lesson(self, state: AgentState) -> AgentState:
        """Generate lesson content."""
        logger.info("generating_lesson_content", topic=state["topic_query"])

        # Prepare context
        context = {
            "topic": state["topic_query"],
            "subject": state["subject"],
            "grade": state["grade"],
            "retrieved_docs": "\n".join(
                [
                    f"- {doc.get('content', '')[:200]}..."
                    for doc in state.get("retrieved_docs", [])[:3]  # Limit to 3 docs
                ]
            ),
        }

        messages = [
            {
                "role": "system",
                "content": "Ти - експерт з генерації навчального контенту для української школи.",
            },
            {
                "role": "user",
                "content": LESSON_GENERATION_PROMPT.format(**context),
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="content_generation",
            tenant_id=state["tenant_id"],
            temperature=0.7,
            max_tokens=2048,
        )

        # Parse and store content
        content = response["content"]
        state["lesson_content"] = content
        state["lesson_sources"] = [
            doc.get("source", "generated") for doc in state.get("retrieved_docs", [])
        ]

        logger.info("lesson_content_generated", length=len(content))

        return state

    async def _generate_quiz(self, state: AgentState) -> AgentState:
        """Generate quiz questions."""
        logger.info("generating_quiz", topic=state["topic_query"])

        context = {
            "topic": state["topic_query"],
            "subject": state["subject"],
            "grade": state["grade"],
            "lesson_content": state.get("lesson_content", "")[:1000],  # Limit content
        }

        messages = [
            {
                "role": "system",
                "content": "Ти - експерт з створення тестів для української школи.",
            },
            {"role": "user", "content": QUIZ_GENERATION_PROMPT.format(**context)},
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="quiz_generation",
            tenant_id=state["tenant_id"],
            temperature=0.6,
            max_tokens=1024,
        )

        # Parse quiz (assuming JSON format)
        try:
            import json

            quiz_data = json.loads(response["content"])
            state["quiz"] = quiz_data if isinstance(quiz_data, list) else [quiz_data]
        except json.JSONDecodeError:
            # Fallback: store as raw text
            state["quiz"] = [{"content": response["content"], "type": "text"}]

        logger.info("quiz_generated", questions=len(state["quiz"]))

        return state
