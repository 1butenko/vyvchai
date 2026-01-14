from enum import Enum
from typing import Optional

from core.config import Settings as CoreSettings
from pydantic import BaseModel


class TelemetryProvider(str, Enum):
    PHOENIX = "phoenix"
    JAEGER = "jaeger"
    ZIPKIN = "zipkin"
    OTLP = "otlp"


class TelemetryConfig(BaseModel):
    enabled: bool = False

    phoenix_enabled: bool = False
    phoenix_url: str = "http://localhost:6006"
    phoenix_project_name: str = "vyvchai"

    prometheus_enabled: bool = True
    prometheus_port: int = 9090

    otel_enabled: bool = True
    otel_endpoint: Optional[str] = None
    otel_service_name: str = "vyvchai"

    trace_sample_rate: float = 1.0

    track_llm_costs: bool = True
    track_user_behavior: bool = True
    track_performance: bool = True

    metrics_retention_days: int = 90
    traces_retention_days: int = 30

    enable_alerts: bool = True
    alert_webhook_url: Optional[str] = None

    # TODO
    lapa_cost_per_1k_tokens: float = 0.0


class Settings(CoreSettings):
    TELEMETRY: TelemetryConfig = TelemetryConfig()
