from typing import Any, Dict, List

import structlog

from src.llm.router import LLMProvider, llm_router
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class QualityAssuranceAgent:
    """
    Quality assurance agent that validates generated content.
    """

    async def validate_content(self, state: AgentState) -> Dict[str, Any]:
        """
        Validate the quality of generated content.

        Args:
            state: Current agent state

        Returns:
            Validation feedback
        """
        logger.info("validating_content_quality")

        content = state.get("lesson_content", "")
        quiz = state.get("quiz", [])

        if not content and not quiz:
            return {"valid": False, "issues": ["No content generated"]}

        feedback = {"valid": True, "issues": [], "suggestions": []}

        # Validate lesson content
        if content:
            content_feedback = await self._validate_lesson_content(content, state)
            feedback["issues"].extend(content_feedback.get("issues", []))  # type: ignore
            feedback["suggestions"].extend(content_feedback.get("suggestions", []))  # type: ignore

        # Validate quiz
        if quiz:
            quiz_feedback = await self._validate_quiz(quiz, state)
            feedback["issues"].extend(quiz_feedback.get("issues", []))  # type: ignore
            feedback["suggestions"].extend(quiz_feedback.get("suggestions", []))  # type: ignore

        # Overall validity
        feedback["valid"] = len(feedback["issues"]) == 0  # type: ignore

        logger.info(
            "content_validation_completed",
            valid=feedback["valid"],  # type: ignore
            issues_count=len(feedback["issues"]),  # type: ignore
        )

        return feedback

    async def _validate_lesson_content(
        self, content: str, state: AgentState
    ) -> Dict[str, Any]:
        """Validate lesson content quality."""
        messages = [
            {
                "role": "system",
                "content": "Ти - експерт з перевірки якості навчального контенту.",
            },
            {
                "role": "user",
                "content": f"""
Перевір якість цього навчального матеріалу:

{content[:2000]}...  # Limited for token efficiency

Критерії перевірки:
1. Відповідність шкільній програмі {state['grade']} класу
2. Правильність фактів та інформації
3. Зрозумілість та доступність мови
4. Структура та логіка викладу
5. Наявність прикладів та завдань

Вкажіть проблеми та пропозиції покращення.
""",
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="quality_check",
            tenant_id=state["tenant_id"],
            force_provider=LLMProvider.OPENAI,  # Use GPT for QA
            temperature=0.2,
            max_tokens=512,
        )

        # Parse feedback
        content = response["content"]
        issues = []
        suggestions = []

        # Simple parsing
        if "проблем" in content.lower() or "невірн" in content.lower():
            issues.append("Content quality issues detected")
        if "пропоную" in content.lower() or "рекоменд" in content.lower():
            suggestions.append("Quality improvements suggested")

        return {
            "issues": issues,
            "suggestions": suggestions,
            "detailed_feedback": content,
        }

    async def _validate_quiz(
        self, quiz: List[Dict], state: AgentState
    ) -> Dict[str, Any]:
        """Validate quiz quality."""
        messages = [
            {
                "role": "system",
                "content": "Ти - експерт з перевірки якості тестових завдань.",
            },
            {
                "role": "user",
                "content": f"""
Перевір якість цих тестових питань:

{str(quiz)[:1500]}...

Критерії перевірки:
1. Правильність відповідей
2. Відповідність рівню {state['grade']} класу
3. Різноманітність типів питань
4. Ясність формулювань

Вкажіть проблеми та пропозиції покращення.
""",
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="quality_check",
            tenant_id=state["tenant_id"],
            force_provider=LLMProvider.OPENAI,
            temperature=0.2,
            max_tokens=512,
        )

        content = response["content"]
        issues = []
        suggestions = []

        # Simple parsing
        if "проблем" in content.lower() or "невірн" in content.lower():
            issues.append("Quiz quality issues detected")
        if "пропоную" in content.lower() or "рекоменд" in content.lower():
            suggestions.append("Quiz improvements suggested")

        return {
            "issues": issues,
            "suggestions": suggestions,
            "detailed_feedback": content,
        }
