import json
from enum import Enum
from typing import List

import structlog

from src.agent.prompts.supervisor_prompts import (
    SUPERVISOR_SYSTEM_PROMPT,
    TASK_ROUTING_PROMPT,
)
from src.llm.router import llm_router
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class AgentTask(str, Enum):
    """Available specialist tasks."""

    CONTENT_GENERATION = "content_generation"
    QUIZ_GENERATION = "quiz_generation"
    SOLVING = "solving"
    GRADING = "grading"
    ANALYTICS = "analytics"
    QUALITY_CHECK = "quality_check"


class SupervisorAgent:
    """
    Supervisor agent that coordinates specialist agents.
    Uses LLM to make intelligent routing decisions.
    """

    def __init__(self):
        self.specialist_agents = {}
        self._register_specialists()

    def _register_specialists(self):
        """Register all specialist agents."""
        from src.agent.specialist_agents.analyst_specialist import AnalystSpecialist
        from src.agent.specialist_agents.content_specialist import ContentSpecialist
        from src.agent.specialist_agents.grader_specialist import GraderSpecialist
        from src.agent.specialist_agents.solver_specialist import SolverSpecialist

        self.specialist_agents = {
            AgentTask.CONTENT_GENERATION: ContentSpecialist(),
            AgentTask.QUIZ_GENERATION: ContentSpecialist(),  # Same specialist
            AgentTask.SOLVING: SolverSpecialist(),
            AgentTask.GRADING: GraderSpecialist(),
            AgentTask.ANALYTICS: AnalystSpecialist(),
        }

    async def plan_execution(self, state: AgentState) -> List[AgentTask]:
        """
        Use LLM to create execution plan based on state.

        Args:
            state: Current agent state

        Returns:
            Ordered list of tasks to execute
        """
        # Prepare context for supervisor
        context = {
            "query": state["topic_query"],
            "subject": state["subject"],
            "grade": state["grade"],
            "has_student_answers": state.get("student_answers") is not None,
            "current_step": len(state.get("step_logs", [])),
        }

        # Ask supervisor LLM to create plan
        messages = [
            {"role": "system", "content": SUPERVISOR_SYSTEM_PROMPT},
            {"role": "user", "content": TASK_ROUTING_PROMPT.format(**context)},
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="supervisor_planning",
            tenant_id=state["tenant_id"],
            temperature=0.3,  # Low temperature for deterministic planning
            max_tokens=500,
        )

        # Parse plan from response
        plan = self._parse_plan(response["content"])

        logger.info("execution_plan_created", plan=[str(t) for t in plan])

        return plan

    def _parse_plan(self, llm_response: str) -> List[AgentTask]:
        """
        Parse task plan from LLM response.

        Expected format:
        1. CONTENT_GENERATION
        2. QUIZ_GENERATION
        3. SOLVING
        """
        tasks = []

        for line in llm_response.strip().split("\n"):
            line = line.strip()

            if not line or not line[0].isdigit():
                continue

            # Extract task name
            task_name = line.split(".", 1)[-1].strip().upper()

            try:
                task = AgentTask(task_name.lower())
                tasks.append(task)
            except ValueError:
                logger.warning("unknown_task_in_plan", task=task_name)

        # Fallback to default plan if parsing failed
        if not tasks:
            tasks = self._default_plan()

        return tasks

    def _default_plan(self) -> List[AgentTask]:
        """Default execution plan."""
        return [
            AgentTask.CONTENT_GENERATION,
            AgentTask.QUIZ_GENERATION,
            AgentTask.SOLVING,
        ]

    async def execute_plan(
        self, state: AgentState, plan: List[AgentTask]
    ) -> AgentState:
        """
        Execute plan by delegating to specialist agents.

        Args:
            state: Current state
            plan: Execution plan

        Returns:
            Updated state
        """
        for task in plan:
            logger.info("executing_task", task=task.value)

            specialist = self.specialist_agents.get(task)

            if not specialist:
                logger.error("specialist_not_found", task=task)
                continue

            try:
                # Execute specialist task
                state = await specialist.execute(state)

                state["step_logs"].append(f"Completed: {task.value}")

            except Exception as e:
                logger.error("specialist_execution_failed", task=task, error=str(e))
                state["errors"].append(f"{task.value} failed: {str(e)}")

        return state

    async def should_regenerate(self, state: AgentState) -> bool:
        """
        Use supervisor LLM to decide if regeneration is needed.

        Args:
            state: Current state with validation feedback

        Returns:
            Whether to regenerate
        """
        if state.get("regeneration_count", 0) >= 3:
            return False

        feedback = state.get("solver_feedback", {})

        if not feedback or feedback.get("valid", True):
            return False

        # Ask supervisor
        messages = [
            {
                "role": "system",
                "content": "Ти - супервізор AI-тьютора. Визнач чи потрібна регенерація контенту.",
            },
            {
                "role": "user",
                "content": f"""
Фідбек валідатора:
{json.dumps(feedback, ensure_ascii=False, indent=2)}

Кількість спроб: {state.get('regeneration_count', 0)}/3

Чи потрібно регенерувати? Відповідь ТІЛЬКИ 'ТАК' або 'НІ'.
""".strip(),
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="supervisor_decision",
            tenant_id=state["tenant_id"],
            temperature=0.1,  # Very low temperature for yes/no
            max_tokens=10,
        )

        answer = response["content"].strip().upper()

        return "ТАК" in answer or "YES" in answer
