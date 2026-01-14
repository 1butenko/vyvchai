from typing import Any, Dict, Optional

import structlog

from src.llm.router import llm_router

logger = structlog.get_logger()


class SolverTool:
    """
    Tool for solving mathematical and logical problems.
    """

    async def solve_problem(
        self,
        problem: str,
        subject: str,
        grade: int,
        tenant_id: str,
        context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Solve a mathematical or logical problem.

        Args:
            problem: Problem statement
            subject: Subject area
            grade: Grade level
            tenant_id: Tenant ID
            context: Additional context

        Returns:
            Solution with steps
        """
        logger.info("solving_problem", subject=subject, grade=grade)

        # Prepare prompt
        prompt = f"""Розв'яжи цю задачу крок за кроком:

Задача: {problem}
Предмет: {subject}
Клас: {grade}

{f'Додатковий контекст: {context}' if context else ''}

Покажи повний розв'язок з детальними поясненнями кожного кроку."""

        messages = [
            {
                "role": "system",
                "content": "Ти - експерт з розв'язування математичних та логічних задач.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]

        try:
            response = await llm_router.route_request(
                messages=messages,
                task_type=f"solver_{subject.lower()}",
                tenant_id=tenant_id,
                temperature=0.1,  # Low temperature for accuracy
                max_tokens=2048,
            )

            solution = {
                "problem": problem,
                "solution": response["content"],
                "solved": True,
                "confidence": 0.8,  # Could be improved with validation
            }

            logger.info("problem_solved")

            return solution

        except Exception as e:
            logger.error("problem_solving_failed", error=str(e))

            return {
                "problem": problem,
                "solution": f"Не вдалося розв'язати задачу: {str(e)}",
                "solved": False,
                "error": str(e),
            }
