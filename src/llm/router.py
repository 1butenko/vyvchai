from enum import Enum
from typing import Any, Dict, List, Optional

import structlog

from src.core.config import get_settings
from src.llm.lapa_manager import lapa_manager
from src.llm.openai_client import openai_client

logger = structlog.get_logger()


class LLMProvider(str, Enum):
    LAPA = "lapa"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class IntelligentLLMRouter:
    """
    Intelligent router that selects best LLM provider
    based on task type, cost, and availability.
    """

    def __init__(self):
        self.provider_priority = [
            LLMProvider.LAPA,  # Prefer local first
            LLMProvider.OPENAI,  # Fallback to cloud
        ]

        # Task type to provider mapping
        self.task_routing = {
            "topic_routing": LLMProvider.LAPA,
            "content_generation": LLMProvider.LAPA,
            "quiz_generation": LLMProvider.LAPA,
            "solver_algebra": LLMProvider.LAPA,
            "solver_general": LLMProvider.LAPA,
            "grading": LLMProvider.LAPA,
            "recommendation": LLMProvider.LAPA,
            "quality_check": LLMProvider.OPENAI,  # Use GPT for QA
        }

    async def route_request(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        tenant_id: str,
        force_provider: Optional[LLMProvider] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Route request to best available provider.

        Args:
            messages: Chat messages
            task_type: Task type
            tenant_id: Tenant ID
            force_provider: Force specific provider
            **kwargs: Additional parameters

        Returns:
            LLM response
        """
        # Determine provider
        if force_provider:
            provider = force_provider
        else:
            provider = self.task_routing.get(task_type, LLMProvider.LAPA)

        # Try primary provider
        try:
            if provider == LLMProvider.LAPA:
                return await self._call_lapa(messages, task_type, tenant_id, **kwargs)
            elif provider == LLMProvider.OPENAI:
                return await self._call_openai(messages, task_type, tenant_id, **kwargs)
            else:
                raise ValueError(f"Unknown provider {provider}")
        except Exception as e:
            logger.warning(
                "provider_failed_attempting_fallback", provider=provider, error=str(e)
            )

            # Fallback strategy
            settings = get_settings()
            if settings.FALLBACK_TO_CLOUD and provider == LLMProvider.LAPA:
                logger.info("falling_back_to_openai")
                return await self._call_openai(messages, task_type, tenant_id, **kwargs)
            else:
                raise

    async def _call_lapa(
        self, messages: List[Dict[str, str]], task_type: str, tenant_id: str, **kwargs
    ) -> Dict[str, Any]:
        """Call LapaLLM."""
        return await lapa_manager.chat_completion(
            messages=messages, task_type=task_type, tenant_id=tenant_id, **kwargs
        )

    async def _call_openai(
        self, messages: List[Dict[str, str]], task_type: str, tenant_id: str, **kwargs
    ) -> Dict[str, Any]:
        """Call OpenAI."""
        return await openai_client.chat_completion(
            messages=messages, task_type=task_type, tenant_id=tenant_id, **kwargs
        )


# Global router
llm_router = IntelligentLLMRouter()
