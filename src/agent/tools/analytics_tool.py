from typing import Any, Dict, List

import structlog

logger = structlog.get_logger()


class AnalyticsTool:
    """
    Tool for analyzing student performance and learning patterns.
    """

    def analyze_performance(
        self,
        student_answers: List[str],
        correct_answers: List[str],
        question_types: List[str],
        subject: str,
        grade: int,
    ) -> Dict[str, Any]:
        """
        Analyze student performance across different question types.

        Args:
            student_answers: Student's answers
            correct_answers: Correct answers
            question_types: Types of questions
            subject: Subject area
            grade: Grade level

        Returns:
            Performance analysis
        """
        logger.info("analyzing_performance", subject=subject, grade=grade)

        if not student_answers or not correct_answers:
            return {"error": "No answers to analyze"}

        # Calculate basic metrics
        total_questions = len(correct_answers)
        correct_count = 0
        type_performance = {}

        for _, (student_ans, correct_ans, q_type) in enumerate(
            zip(student_answers, correct_answers, question_types)
        ):
            is_correct = self._compare_answers(student_ans, correct_ans)

            if is_correct:
                correct_count += 1

            # Track by question type
            if q_type not in type_performance:
                type_performance[q_type] = {"correct": 0, "total": 0, "accuracy": 0.0}

            type_performance[q_type]["total"] += 1
            if is_correct:
                type_performance[q_type]["correct"] += 1

        # Calculate percentages
        accuracy = correct_count / total_questions if total_questions > 0 else 0

        for q_type in type_performance:
            perf = type_performance[q_type]
            perf["accuracy"] = (
                perf["correct"] / perf["total"] if perf["total"] > 0 else 0
            )

        # Generate insights
        insights = self._generate_insights(accuracy, type_performance, subject, grade)

        return {
            "total_questions": total_questions,
            "correct_answers": correct_count,
            "accuracy": accuracy,
            "type_performance": type_performance,
            "insights": insights,
            "recommendations": self._generate_recommendations(insights, subject),
        }

    def _compare_answers(self, student: str, correct: str) -> bool:
        """Compare student answer with correct answer."""
        # Simple string comparison (could be improved with NLP)
        student_clean = student.strip().lower()
        correct_clean = correct.strip().lower()

        # Exact match
        if student_clean == correct_clean:
            return True

        # Check if student answer contains key elements of correct answer
        # This is a simplified approach
        return correct_clean in student_clean or student_clean in correct_clean

    def _generate_insights(
        self,
        accuracy: float,
        type_performance: Dict[str, Any],
        subject: str,
        grade: int,
    ) -> List[str]:
        """Generate insights from performance data."""
        insights = []

        if accuracy >= 0.8:
            insights.append("Відмінний результат! Учень добре засвоїв матеріал.")
        elif accuracy >= 0.6:
            insights.append("Добрий результат, але є над чим працювати.")
        else:
            insights.append("Потрібно більше уваги до цього матеріалу.")

        # Analyze by question type
        for q_type, perf in type_performance.items():
            acc = perf["accuracy"]
            if acc < 0.5:
                insights.append(f"Слабкі знання в питаннях типу '{q_type}'")
            elif acc >= 0.8:
                insights.append(f"Сильні знання в питаннях типу '{q_type}'")

        return insights

    def _generate_recommendations(self, insights: List[str], subject: str) -> List[str]:
        """Generate learning recommendations."""
        recommendations = []

        if any("слабкі" in insight.lower() for insight in insights):
            recommendations.append("Рекомендується додаткове вивчення складних тем")
            recommendations.append("Практика розв'язування подібних задач")

        if any("добрий" in insight.lower() for insight in insights):
            recommendations.append("Продовжуйте в тому ж дусі!")
            recommendations.append("Можете переходити до складніших завдань")

        recommendations.append(f"Рекомендується більше практики з предмету '{subject}'")

        return recommendations
