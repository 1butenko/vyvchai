from typing import Any, Dict, List

import structlog

from src.core.exceptions import LLMError
from src.llm.router import LLMProvider, llm_router

logger = structlog.get_logger()


class FallbackStrategy:
    """
    Fallback strategy for LLM calls when primary provider fails.
    """

    def __init__(self):
        self.fallback_chain = [
            LLMProvider.LAPA,
            LLMProvider.OPENAI,
        ]

    async def execute_with_fallback(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        tenant_id: str,
        primary_provider: LLMProvider,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Execute LLM call with fallback strategy.

        Args:
            messages: Chat messages
            task_type: Task type
            tenant_id: Tenant ID
            primary_provider: Primary provider to try first
            **kwargs: Additional parameters

        Returns:
            LLM response

        Raises:
            LLMError: If all providers fail
        """
        errors = []

        # Try providers in fallback chain
        for provider in self.fallback_chain:
            try:
                logger.info("trying_provider", provider=provider.value, task=task_type)

                result = await llm_router.route_request(
                    messages=messages,
                    task_type=task_type,
                    tenant_id=tenant_id,
                    force_provider=provider,
                    **kwargs,
                )

                if provider != primary_provider:
                    logger.info(
                        "fallback_successful",
                        primary=primary_provider.value,
                        fallback=provider.value,
                    )

                return result

            except Exception as e:
                error_msg = f"{provider.value}: {str(e)}"
                errors.append(error_msg)
                logger.warning("provider_failed", provider=provider.value, error=str(e))

        # All providers failed
        final_error = f"All LLM providers failed: {'; '.join(errors)}"
        logger.error("all_providers_failed", errors=errors)
        raise LLMError(final_error)


# Global fallback strategy
fallback_strategy = FallbackStrategy()
