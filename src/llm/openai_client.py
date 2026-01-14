from typing import Any, Dict, List, Optional

import openai
import structlog

from src.core.config import get_settings
from src.core.exceptions import LLMError
from src.utils.telemetry.business_metrics import business_metrics

logger = structlog.get_logger()


class OpenAIClient:
    """Client for OpenAI API with telemetry."""

    def __init__(self, api_key: Optional[str] = None):
        settings = get_settings()
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = None

        if self.api_key:
            self.client = openai.AsyncOpenAI(api_key=self.api_key)
            logger.info("openai_client_initialized")
        else:
            logger.warning("openai_client_not_initialized_no_api_key")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        task_type: str,
        tenant_id: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        max_tokens: int = 2048,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Chat completion with OpenAI.

        Args:
            messages: Chat messages
            task_type: Task type for telemetry
            tenant_id: Tenant ID
            model: OpenAI model
            temperature: Sampling temperature
            max_tokens: Max tokens

        Returns:
            Completion response
        """
        if not self.client:
            raise LLMError("OpenAI client not initialized - no API key provided")

        try:
            response = await self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            # Convert to consistent format
            result = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "finish_reason": response.choices[0].finish_reason,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "model": response.model,
                "id": response.id,
                "created": response.created,
            }

            # Track metrics
            business_metrics.track_llm_call(
                class_id=tenant_id,
                provider="openai",
                model=model,
                purpose=task_type,
                input_tokens=result["usage"]["prompt_tokens"],
                output_tokens=result["usage"]["completion_tokens"],
                status="success",
                cost_usd=self._calculate_cost(model, result["usage"]),
            )

            logger.info(
                "openai_completion", model=model, tokens=result["usage"]["total_tokens"]
            )

            return result

        except openai.APIError as e:
            logger.error("openai_api_error", error=str(e))
            business_metrics.track_llm_call(
                class_id=tenant_id,
                provider="openai",
                model=model,
                purpose=task_type,
                input_tokens=0,
                output_tokens=0,
                status="error",
                cost_usd=0.0,
            )
            raise LLMError(f"OpenAI API error: {str(e)}") from e

    def _calculate_cost(self, model: str, usage: Dict[str, int]) -> float:
        """Calculate approximate cost in USD."""
        # Simplified pricing (update with current rates)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
        }

        rates = pricing.get(model, {"input": 0.0, "output": 0.0})

        input_cost = (usage["prompt_tokens"] / 1000) * rates["input"]
        output_cost = (usage["completion_tokens"] / 1000) * rates["output"]

        return round(input_cost + output_cost, 4)


# Global instance
openai_client = OpenAIClient()
