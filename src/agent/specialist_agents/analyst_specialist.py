from typing import Any, Dict, Optional

import structlog

from src.llm.router import llm_router
from src.schemas.agent_state import AgentState

logger = structlog.get_logger()


class AnalystSpecialist:
    """
    Specialist agent for analyzing student profiles and generating recommendations.
    """

    async def execute(self, state: AgentState) -> AgentState:
        """
        Analyze student performance and generate recommendations.

        Args:
            state: Current agent state

        Returns:
            Updated state with analytics and recommendations
        """
        logger.info("analyzing_student_profile")

        # Get student profile and performance data
        profile = state.get("student_profile", {})
        grading_result = state.get("grading_result", {})

        if not profile and not grading_result:
            logger.info("no_data_for_analysis")
            return state

        # Generate analysis
        analysis = await self._analyze_performance(profile, grading_result, state)

        # Generate recommendations
        recommendations = await self._generate_recommendations(analysis, state)

        state["student_analysis"] = analysis
        state["recommendations"] = recommendations

        logger.info("analysis_completed")

        return state

    async def _analyze_performance(
        self, profile: Optional[Dict[str, Any]], grading_result: Dict[str, Any], state: AgentState
    ) -> Dict[str, Any]:
        """Analyze student performance."""
        if profile is None:
            profile = {}
        context = {
            "profile": profile,
            "grading": grading_result,
            "subject": state["subject"],
            "grade": state["grade"],
            "topic": state["topic_query"],
        }

        messages = [
            {
                "role": "system",
                "content": "Ти - педагогічний аналітик. Проаналізуй профіль та успішність учня.",
            },
            {
                "role": "user",
                "content": f"""
Проаналізуй дані учня:

Профіль учня: {context['profile']}
Результати тестування: {context['grading']}
Предмет: {context['subject']}
Клас: {context['grade']}
Тема: {context['topic']}

Дай аналіз сильних та слабких сторін, рівня знань та прогресу навчання.
""".strip(),
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="analytics",
            tenant_id=state["tenant_id"],
            temperature=0.4,
            max_tokens=1024,
        )

        return {
            "analysis": response["content"],
            "profile": profile,
            "performance_metrics": grading_result,
        }

    async def _generate_recommendations(
        self, analysis: Dict[str, Any], state: AgentState
    ) -> Dict[str, Any]:
        """Generate personalized recommendations."""
        context = {
            "analysis": analysis["analysis"],
            "subject": state["subject"],
            "grade": state["grade"],
            "current_topic": state["topic_query"],
        }

        messages = [
            {
                "role": "system",
                "content": "Ти - педагогічний консультант. Створи персоналізовані рекомендації для учня.",
            },
            {
                "role": "user",
                "content": f"""
На основі аналізу створи рекомендації для учня:

Аналіз: {context['analysis']}
Предмет: {context['subject']}
Клас: {context['grade']}
Поточна тема: {context['current_topic']}

Створи:
1. Рекомендації по навчанню
2. Додаткові матеріали для вивчення
3. Вправи для закріплення
4. Стратегії покращення
""".strip(),
            },
        ]

        response = await llm_router.route_request(
            messages=messages,
            task_type="recommendation",
            tenant_id=state["tenant_id"],
            temperature=0.6,
            max_tokens=1024,
        )

        return {
            "recommendations": response["content"],
            "generated_at": "now",  # Could use datetime
            "topic": state["topic_query"],
        }
