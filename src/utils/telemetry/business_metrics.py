from typing import Optional

import structlog
from opentelemetry import metrics
from prometheus_client import Counter, Gauge, Histogram

logger = structlog.get_logger()


class BusinessMetrics:
    def __init__(self):
        self.meter = metrics.get_meter(__name__)

        self.lesson_requests = Counter(
            "lesson_generation_requests_total",
            "Total lesson generation requests",
            ["class_id", "subject", "grade", "status"],
        )

        self.quiz_requests = Counter(
            "quiz_generation_requests_total",
            "Total quiz generation requests",
            ["class_id§", "subject", "grade", "status"],
        )

        self.lesson_generation_duration = Histogram(
            "lesson_generation_duration_seconds",
            "Lesson generation duration",
            ["class_id", "subject"],
            buckets=[1, 2, 5, 10, 20, 30, 60],
        )

        self.quiz_generation_duration = Histogram(
            "quiz_generation_duration_seconds",
            "Quiz generation duration",
            ["class_id", "subject"],
            buckets=[1, 2, 5, 10, 20, 30, 60],
        )

        self.rag_retrieval_duration = Histogram(
            "rag_retrieval_duration_seconds",
            "RAG retrieval duration",
            ["subject"],
            buckets=[0.1, 0.5, 1, 2, 5, 10],
        )

        self.llm_calls = Counter(
            "llm_calls_total",
            "Total LLM API calls",
            ["provider", "model", "purpose", "status"],
        )

        self.llm_tokens = Counter(
            "llm_tokens_total", "Total tokens used", ["provider", "model", "token_type"]
        )

        self.llm_cost = Counter(
            "llm_cost_usd_total",
            "Total LLM cost in USD",
            ["class_id", "provider", "model"],
        )

        self.solver_attempts = Counter(
            "solver_attempts_total",
            "Solver attempts",
            ["subject", "question_type", "success"],
        )

        self.quiz_validation_failures = Counter(
            "quiz_validation_failures_total",
            "Quiz validation failures requiring regeneration",
            ["subject", "failure_reason"],
        )

        self.quiz_completions = Counter(
            "quiz_completions_total",
            "Quiz completions",
            ["class_id", "subject", "grade"],
        )

        self.quiz_scores = Histogram(
            "quiz_scores",
            "Quiz scores distribution",
            ["class_id", "subject", "grade"],
            buckets=[0, 0.2, 0.4, 0.6, 0.7, 0.8, 0.9, 1.0],
        )

        self.active_users = Gauge(
            "active_users_current", "Current active users", ["class_id"]
        )

        self.cache_hit_rate = Gauge("cache_hit_rate", "Cache hit rate", ["cache_type"])

        self.revenue_tracking = Counter(
            "revenue_usd_total", "Total revenue", ["class_id", "tier"]
        )

        self.feature_usage = Counter(
            "feature_usage_total", "Feature usage count", ["class_id", "feature_name"]
        )

    def track_lesson_request(
        self,
        class_id: str,
        subject: str,
        grade: int,
        status: str,
        duration: Optional[float] = None,
    ):
        self.lesson_requests.labels(
            class_id=class_id, subject=subject, grade=str(grade), status=status
        ).inc()

        if duration:
            self.lesson_generation_duration.labels(
                class_id=class_id, subject=subject
            ).observe(duration)

    def track_llm_call(
        self,
        class_id: str,
        provider: str,
        model: str,
        purpose: str,
        input_tokens: int,
        output_tokens: int,
        status: str,
        cost_usd: float,
    ):
        self.llm_calls.labels(
            provider=provider, model=model, purpose=purpose, status=status
        ).inc()

        self.llm_tokens.labels(provider=provider, model=model, token_type="input").inc(
            input_tokens
        )

        self.llm_tokens.labels(provider=provider, model=model, token_type="output").inc(
            output_tokens
        )

        self.llm_cost.labels(class_id=class_id, provider=provider, model=model).inc(
            cost_usd
        )

    def track_solver_attempt(self, subject: str, question_type: str, success: bool):
        self.solver_attempts.labels(
            subject=subject, question_type=question_type, success=str(success)
        ).inc()

    def track_quiz_completion(
        self, tenant_id: str, subject: str, grade: int, score: float
    ):
        self.quiz_completions.labels(
            tenant_id=tenant_id, subject=subject, grade=str(grade)
        ).inc()

        self.quiz_scores.labels(
            tenant_id=tenant_id, subject=subject, grade=str(grade)
        ).observe(score)

    def track_validation_failure(self, subject: str, reason: str):
        self.quiz_validation_failures.labels(
            subject=subject, failure_reason=reason
        ).inc()

    def update_active_users(self, tenant_id: str, count: int):
        self.active_users.labels(tenant_id=tenant_id).set(count)

    def track_revenue(self, tenant_id: str, tier: str, amount_usd: float):
        self.revenue_tracking.labels(tenant_id=tenant_id, tier=tier).inc(amount_usd)


business_metrics = BusinessMetrics()
