from typing import Any, Dict

import structlog

from src.agent.prompts.grader_prompts import GRADING_PROMPT
from src.llm.router import llm_router
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class GraderSpecialist:
    """
    Specialist agent for grading student answers.
    """

    async def execute(self, state: AgentState) -> AgentState:
        """
        Grade student answers if available.

        Args:
            state: Current agent state

        Returns:
            Updated state with grading results
        """
        student_answers = state.get("student_answers")

        if not student_answers:
            logger.info("no_student_answers_to_grade")
            return state

        logger.info("grading_student_answers", count=len(student_answers))

        quiz = state.get("quiz", [])
        grading_results = []

        for i, (question, answer) in enumerate(zip(quiz, student_answers)):
            grade = await self._grade_answer(question, answer, state)
            grading_results.append(
                {
                    "question_index": i,
                    "question": question,
                    "student_answer": answer,
                    "grade": grade,
                }
            )

        state["grading_result"] = {
            "results": grading_results,
            "total_questions": len(quiz),
            "correct_answers": sum(1 for r in grading_results if r["grade"]["correct"]),  # type: ignore
            "average_score": sum(r["grade"]["score"] for r in grading_results)  # type: ignore
            / len(grading_results),
        }

        logger.info(
            "grading_completed", correct=state["grading_result"]["correct_answers"]
        )

        return state

    async def _grade_answer(
        self, question: Dict[str, Any], student_answer: str, state: AgentState
    ) -> Dict[str, Any]:
        """Grade a single answer."""
        context = {
            "question": question.get("question", ""),
            "correct_answer": question.get("correct_answer", ""),
            "student_answer": student_answer,
            "question_type": question.get("type", "open"),
            "subject": state["subject"],
            "grade": state["grade"],
        }

        messages = [
            {
                "role": "system",
                "content": "Ти - вчитель який оцінює відповіді учнів. Будь справедливим та детальним.",
            },
            {
                "role": "user",
                "content": GRADING_PROMPT.format(**context),
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="grading",
            tenant_id=state["tenant_id"],
            temperature=0.2,  # Low temperature for consistent grading
            max_tokens=512,
        )

        # Parse grading response
        content = response["content"]

        # Simple parsing - look for score and feedback
        try:
            # Assume format: "Оцінка: X/10\nПояснення: ..."
            lines = content.split("\n")
            score_line = next((line for line in lines if "оцінк" in line.lower()), "")
            score = self._extract_score(score_line)

            return {
                "score": score,
                "max_score": 10,
                "correct": score >= 7,  # 70% threshold
                "feedback": content,
                "auto_graded": True,
            }
        except Exception:
            return {
                "score": 5,  # Default middle score
                "max_score": 10,
                "correct": False,
                "feedback": content,
                "auto_graded": True,
            }

    def _extract_score(self, score_line: str) -> int:
        """Extract numeric score from text."""
        import re

        numbers = re.findall(r"\d+", score_line)
        return int(numbers[0]) if numbers else 5
