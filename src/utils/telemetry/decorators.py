import time
from functools import wraps
from typing import Any, Callable, Dict, Optional

import structlog
from app import settings
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

from src.utils.telemetry.business_metrics import business_metrics

logger = structlog.get_logger()
tracer = trace.get_tracer(__name__)


def traceable(name: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            span_name = name or func.__name__

            with tracer.start_as_current_span(span_name) as span:
                if metadata:
                    for key, value in metadata.items():
                        span.set_attribute(key, str(value))

                if args and hasattr(args[0], "__getitem__"):
                    state = args[0]
                    if isinstance(state, dict):
                        span.set_attribute("class_id", state.get("class_id", "unknown"))
                        span.set_attribute("subject", state.get("subject", "unknown"))
                        span.set_attribute("trace_id", state.get("trace_id", "unknown"))

                start_time = time.time()

                try:
                    result = await func(*args, **kwargs)

                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)

                    logger.error(
                        "trace_error",
                        span_name=span_name,
                        error=str(e),
                        duration=duration,
                    )
                    raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            span_name = name or func.__name__

            with tracer.start_as_current_span(span_name) as span:
                if metadata:
                    for key, value in metadata.items():
                        span.set_attribute(key, str(value))

                start_time = time.time()

                try:
                    result = func(*args, **kwargs)

                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.OK))

                    return result

                except Exception as e:
                    duration = time.time() - start_time
                    span.set_attribute("duration_seconds", duration)
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise

        import inspect

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def track_llm_call(provider: str, model: str, purpose: str):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = await func(*args, **kwargs)

                input_tokens = result.get("usage", {}).get("prompt_tokens", 0)
                output_tokens = result.get("usage", {}).get("completion_tokens", 0)

                total_tokens = input_tokens + output_tokens
                cost_per_1k = (
                    settings.telemetry.openai_cost_per_1k_tokens
                    if provider == "openai"
                    else 0
                )
                cost_usd = (total_tokens / 1000) * cost_per_1k

                class_id = kwargs.get("class_id", "unknown")
                business_metrics.track_llm_call(
                    class_id=class_id,
                    provider=provider,
                    model=model,
                    purpose=purpose,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    status="success",
                    cost_usd=cost_usd,
                )

                logger.info(
                    "llm_call_completed",
                    provider=provider,
                    model=model,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost_usd=round(cost_usd, 4),
                    duration=time.time() - start_time,
                )

                return result

            except Exception:
                business_metrics.track_llm_call(
                    tenant_id=kwargs.get("tenant_id", "unknown"),
                    provider=provider,
                    model=model,
                    purpose=purpose,
                    input_tokens=0,
                    output_tokens=0,
                    status="error",
                    cost_usd=0,
                )
                raise

        return wrapper

    return decorator
