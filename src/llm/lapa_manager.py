import asyncio
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from src.core.config import get_settings
from src.core.exceptions import LLMError
from src.llm.lapa_client import LapaLLMClient
from src.utils.telemetry.business_metrics import business_metrics

logger = structlog.get_logger()


class LapaModelTier(str, Enum):
    """LapaLLM model tiers for different use cases."""

    FAST = "lapa-8b"  # Швидка модель для простих задач
    BALANCED = "lapa-13b"  # Балансована модель
    PREMIUM = "lapa-70b"  # Найкраща якість (якщо доступна)
    EMBEDDINGS = "lapa-embeddings"


class LapaLLMManager:
    """
    Manager for LapaLLM with intelligent routing,
    load balancing, and fallback strategies.
    """

    def __init__(self):
        self.clients: Dict[str, LapaLLMClient] = {}
        self._initialize_clients()

        # Model capabilities mapping
        self.model_capabilities = {
            LapaModelTier.FAST: {
                "max_tokens": 4096,
                "best_for": ["classification", "simple_qa", "topic_routing"],
                "cost_multiplier": 1.0,
                "speed_score": 10,
            },
            LapaModelTier.BALANCED: {
                "max_tokens": 8192,
                "best_for": ["content_generation", "reasoning", "solver"],
                "cost_multiplier": 2.0,
                "speed_score": 7,
            },
            LapaModelTier.PREMIUM: {
                "max_tokens": 16384,
                "best_for": ["complex_reasoning", "creative_writing"],
                "cost_multiplier": 5.0,
                "speed_score": 4,
            },
        }

        # Request queue for rate limiting
        self.request_queue = asyncio.Queue()
        self.rate_limit_per_second = 10

        logger.info("lapa_manager_initialized", models=list(self.clients.keys()))

    def _initialize_clients(self):
        """Initialize LapaLLM clients for different tiers."""
        settings = get_settings()
        base_urls = {
            LapaModelTier.FAST: settings.LAPA_LLM_URL,
            LapaModelTier.BALANCED: settings.LAPA_LLM_URL,
            LapaModelTier.PREMIUM: settings.LAPA_LLM_URL,
        }

        for tier, url in base_urls.items():
            if url and url != "##LAPA_LLM_URL##":
                self.clients[tier] = LapaLLMClient(base_url=url, model_name=tier.value)

    async def select_best_model(
        self, task_type: str, complexity: str = "medium", priority: str = "balanced"
    ) -> LapaModelTier:
        """
        Intelligently select best model based on task requirements.

        Args:
            task_type: Type of task (e.g., "solver", "content_gen")
            complexity: Task complexity ("low", "medium", "high")
            priority: Priority ("speed", "quality", "balanced")

        Returns:
            Selected model tier
        """
        # Simple routing logic
        if priority == "speed" or complexity == "low":
            return LapaModelTier.FAST
        elif priority == "quality" or complexity == "high":
            return (
                LapaModelTier.PREMIUM
                if LapaModelTier.PREMIUM in self.clients
                else LapaModelTier.BALANCED
            )
        else:
            return LapaModelTier.BALANCED

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        tenant_id: str,
        model_tier: Optional[LapaModelTier] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Chat completion with automatic model selection and telemetry.

        Args:
            messages: Chat messages
            task_type: Task type for routing
            tenant_id: Tenant ID for cost tracking
            model_tier: Force specific model tier (optional)
            temperature: Sampling temperature
            max_tokens: Max tokens to generate

        Returns:
            Completion response
        """
        # Auto-select model if not specified
        if not model_tier:
            complexity = kwargs.pop("complexity", "medium")
            priority = kwargs.pop("priority", "balanced")
            model_tier = await self.select_best_model(task_type, complexity, priority)

        # Get client
        client = self.clients.get(model_tier)
        if not client:
            logger.warning("model_unavailable", tier=model_tier)
            # Fallback to balanced
            client = self.clients.get(LapaModelTier.BALANCED)
            model_tier = LapaModelTier.BALANCED

        if not client:
            raise LLMError("No LapaLLM client available")

        logger.info(
            "lapa_request",
            task=task_type,
            model=model_tier.value,
            messages_count=len(messages),
        )

        # Make request
        start_time = asyncio.get_event_loop().time()

        try:
            result = await client.chat_completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            duration = asyncio.get_event_loop().time() - start_time

            # Track metrics
            business_metrics.track_llm_call(
                class_id=tenant_id,  # Using class_id as tenant_id
                provider="lapa",
                model=model_tier.value,
                purpose=task_type,
                input_tokens=result["usage"]["prompt_tokens"],
                output_tokens=result["usage"]["completion_tokens"],
                status="success",
                cost_usd=0.0,  # LapaLLM is self-hosted
            )

            logger.info(
                "lapa_success",
                model=model_tier.value,
                tokens=result["usage"]["total_tokens"],
                duration=round(duration, 2),
            )

            return result

        except Exception as e:
            logger.error("lapa_error", model=model_tier.value, error=str(e))

            # Track failed attempt
            business_metrics.track_llm_call(
                class_id=tenant_id,
                provider="lapa",
                model=model_tier.value,
                purpose=task_type,
                input_tokens=0,
                output_tokens=0,
                status="error",
                cost_usd=0.0,
            )

            raise

    async def generate_embeddings(
        self, texts: List[str], tenant_id: str
    ) -> List[List[float]]:
        """Generate embeddings using LapaLLM."""
        client = self.clients.get(LapaModelTier.BALANCED)  # Use any available client

        if not client:
            raise LLMError("No LapaLLM client available for embeddings")

        embeddings = await client.generate_embeddings(texts)

        logger.info("embeddings_generated", count=len(embeddings), tenant=tenant_id)

        return embeddings

    async def close_all(self):
        """Close all clients."""
        for client in self.clients.values():
            await client.close()


# Global instance
lapa_manager = LapaLLMManager()
