from typing import Any, Dict, List

import structlog

from src.agent.qa_agent import QualityAssuranceAgent

logger = structlog.get_logger()


class ValidatorTool:
    """
    Tool for validating content quality and correctness.
    """

    def __init__(self):
        self.qa_agent = QualityAssuranceAgent()

    async def validate_content(
        self, content: Dict[str, Any], tenant_id: str
    ) -> Dict[str, Any]:
        """
        Validate generated content quality.

        Args:
            content: Content to validate (lesson, quiz, etc.)
            tenant_id: Tenant ID

        Returns:
            Validation results
        """
        logger.info("validating_content")

        # Convert content dict to AgentState-like structure
        state = {
            "tenant_id": tenant_id,
            "lesson_content": content.get("lesson_content", ""),
            "quiz": content.get("quiz", []),
            "subject": content.get("subject", ""),
            "grade": content.get("grade", 0),
            "topic_query": content.get("topic", ""),
        }

        try:
            feedback = await self.qa_agent.validate_content(state)

            logger.info(
                "content_validation_completed",
                valid=feedback["valid"],
                issues=len(feedback["issues"]),
            )

            return feedback

        except Exception as e:
            logger.error("content_validation_failed", error=str(e))

            return {
                "valid": False,
                "issues": [f"Validation error: {str(e)}"],
                "suggestions": ["Try regenerating content"],
                "error": str(e),
            }

    async def validate_answers(
        self, questions: List[Dict[str, Any]], answers: List[str], tenant_id: str
    ) -> Dict[str, Any]:
        """
        Validate student answers.

        Args:
            questions: List of questions
            answers: List of student answers
            tenant_id: Tenant ID

        Returns:
            Validation results
        """
        logger.info("validating_answers", count=len(answers))

        # Simple validation - check if answers exist and are reasonable length
        validation_results = []

        for i, (question, answer) in enumerate(zip(questions, answers)):
            is_valid = self._validate_single_answer(question, answer)

            validation_results.append(
                {
                    "question_index": i,
                    "question": question.get("question", ""),
                    "answer": answer,
                    "valid": is_valid,
                    "issues": (
                        [] if is_valid else ["Answer appears incomplete or invalid"]
                    ),
                }
            )

        overall_valid = all(r["valid"] for r in validation_results)

        return {
            "valid": overall_valid,
            "results": validation_results,
            "total_questions": len(questions),
            "valid_answers": sum(1 for r in validation_results if r["valid"]),
        }

    def _validate_single_answer(self, question: Dict[str, Any], answer: str) -> bool:
        """Validate a single answer."""
        if not answer or not answer.strip():
            return False

        # Check minimum length
        min_length = 5 if question.get("type") == "open" else 1
        if len(answer.strip()) < min_length:
            return False

        # For multiple choice, check if answer matches options
        if question.get("type") == "multiple_choice":
            options = question.get("options", [])
            if options and answer not in options:
                return False

        return True
