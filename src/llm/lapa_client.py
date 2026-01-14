from typing import Any, AsyncIterator, Dict, List, Optional

import openai
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from src.core.exceptions import LLMError

logger = structlog.get_logger()


class LapaLLMClient:
    """Client for interacting with LapaLLM API (OpenAI-compatible)."""

    def __init__(
        self,
        base_url: str = "http://146.59.127.106:4000",
        api_key: str = "dummy_key",  # LapaLLM might not require a real key
        model_name: str = "lapa",
        timeout: int = 120,
        max_retries: int = 3,
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = openai.AsyncOpenAI(
            api_key=api_key, base_url=base_url, timeout=timeout
        )

        logger.info("lapa_client_initialized", model=model_name, url=base_url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        top_p: float = 0.9,
        frequency_penalty: float = 0.0,
        presence_penalty: float = 0.0,
        stop: Optional[List[str]] = None,
        stream: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Chat completion with LapaLLM.

        Args:
            messages: Chat messages in OpenAI format
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop: Stop sequences
            stream: Enable streaming

        Returns:
            Response dict with content and metadata
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop=stop,
                stream=stream,
                **kwargs,
            )

            if stream:
                return self._handle_stream(response)
            else:
                return await self._handle_completion(response)

        except openai.APIError as e:
            logger.error("lapa_api_error", error=str(e))
            raise LLMError(f"LapaLLM API error: {str(e)}") from e
        except Exception as e:
            logger.error("lapa_unexpected_error", error=str(e))
            raise LLMError(f"Unexpected LapaLLM error: {str(e)}") from e

    async def _handle_completion(self, response) -> Dict[str, Any]:
        """Handle non-streaming completion."""
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

        logger.info(
            "lapa_completion",
            model=self.model_name,
            tokens=result["usage"]["total_tokens"],
            finish_reason=result["finish_reason"],
        )

        return result

    async def _handle_stream(self, response) -> AsyncIterator[str]:
        """Handle streaming completion."""
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def generate_embeddings(
        self, texts: List[str], model: str = "text-embedding-qwen"
    ) -> List[List[float]]:
        """Generate embeddings using LapaLLM."""
        try:
            response = await self.client.embeddings.create(
                input=texts, model=model, encoding_format="float"
            )

            embeddings = [item.embedding for item in response.data]

            logger.info("lapa_embeddings_generated", count=len(embeddings))

            return embeddings

        except Exception as e:
            logger.error("lapa_embeddings_error", error=str(e))
            raise LLMError(f"LapaLLM embeddings error: {str(e)}") from e

    async def close(self):
        """Close the client."""
        # OpenAI client doesn't need explicit closing
        pass
