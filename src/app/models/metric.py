import uuid
from datetime import datetime

from settings import Base
from sqlalchemy import JSON, Column, DateTime, Float, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    metric_name = Column(String(255), nullable=False)
    metric_value = Column(Float, nullable=False)
    labels = Column(JSON)  # Metric labels
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_tenant_metric_time", "tenant_id", "metric_name", "timestamp"),
    )


class LLMUsageLog(Base):
    __tablename__ = "llm_usage_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True))

    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    purpose = Column(String(100))

    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)

    cost_usd = Column(Float, nullable=False)

    request_id = Column(String(255))
    trace_id = Column(String(255))

    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    __table_args__ = (
        Index("idx_tenant_time", "tenant_id", "timestamp"),
        Index("idx_provider_model", "provider", "model"),
    )


class PerformanceLog(Base):
    __tablename__ = "performance_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    endpoint = Column(String(255), nullable=False)
    method = Column(String(10))

    duration_ms = Column(Float, nullable=False)
    status_code = Column(Integer)

    tenant_id = Column(UUID(as_uuid=True), index=True)
    user_id = Column(UUID(as_uuid=True))

    metadata = Column(JSON)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
