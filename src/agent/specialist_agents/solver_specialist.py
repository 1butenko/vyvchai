from typing import List

import structlog

from src.agent.prompts.solver_prompts import PROBLEM_SOLVING_PROMPT
from src.llm.router import llm_router
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class SolverSpecialist:
    """
    Specialist agent for solving mathematical and logical problems.
    """

    async def execute(self, state: AgentState) -> AgentState:
        """
        Solve problems in the generated content.

        Args:
            state: Current agent state

        Returns:
            Updated state with solved problems
        """
        logger.info("solving_problems", subject=state["subject"])

        # Only solve for mathematical subjects
        if state["subject"].lower() not in ["algebra", "math", "математика", "алгебра"]:
            logger.info("skipping_solver_non_math_subject", subject=state["subject"])
            return state

        # Find problems in quiz
        problems = self._extract_problems(state)

        if not problems:
            logger.info("no_problems_to_solve")
            return state

        solved_problems = []

        for problem in problems:
            solution = await self._solve_problem(problem, state)
            solved_problems.append({"problem": problem, "solution": solution})

        # Store solutions
        state["solved_problems"] = solved_problems

        logger.info("problems_solved", count=len(solved_problems))

        return state

    def _extract_problems(self, state: AgentState) -> List[str]:
        """Extract problems from quiz questions."""
        problems = []

        for question in state.get("quiz", []):
            if question.get("type") == "problem":
                problems.append(question.get("question", ""))
            elif "розв'яз" in question.get("question", "").lower():
                problems.append(question.get("question", ""))

        return problems

    async def _solve_problem(self, problem: str, state: AgentState) -> str:
        """Solve a single problem."""
        context = {
            "problem": problem,
            "subject": state["subject"],
            "grade": state["grade"],
            "lesson_content": state.get("lesson_content", "")[:500],  # Context
        }

        messages = [
            {
                "role": "system",
                "content": "Ти - експерт з розв'язування математичних задач для української школи.",
            },
            {
                "role": "user",
                "content": PROBLEM_SOLVING_PROMPT.format(**context),
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type=(
                "solver_algebra"
                if "algebra" in state["subject"].lower()
                else "solver_general"
            ),
            tenant_id=state["tenant_id"],
            temperature=0.3,  # Low temperature for accurate solving
            max_tokens=1024,
        )

        return response["content"]
