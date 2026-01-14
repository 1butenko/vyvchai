from datetime import datetime, timedelta
from typing import Dict, List, Optional

import structlog
from app.models.metric import LLMUsageLog
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()


class MetricsService:
    @staticmethod
    async def log_llm_usage(
        db: AsyncSession,
        tenant_id: str,
        user_id: Optional[str],
        provider: str,
        model: str,
        purpose: str,
        input_tokens: int,
        output_tokens: int,
        cost_usd: float,
        request_id: str,
        trace_id: str,
        metadata: Optional[Dict] = None,
    ):
        log_entry = LLMUsageLog(
            tenant_id=tenant_id,
            user_id=user_id,
            provider=provider,
            model=model,
            purpose=purpose,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=cost_usd,
            request_id=request_id,
            trace_id=trace_id,
            metadata=metadata or {},
        )

        db.add(log_entry)
        await db.flush()

    @staticmethod
    async def get_tenant_llm_cost(
        db: AsyncSession, tenant_id: str, start_date: datetime, end_date: datetime
    ) -> Dict:
        result = await db.execute(
            select(
                func.sum(LLMUsageLog.cost_usd).label("total_cost"),
                func.sum(LLMUsageLog.total_tokens).label("total_tokens"),
                func.count(LLMUsageLog.id).label("total_calls"),
            ).where(
                LLMUsageLog.tenant_id == tenant_id,
                LLMUsageLog.timestamp >= start_date,
                LLMUsageLog.timestamp <= end_date,
            )
        )

        row = result.one()
        return {
            "total_cost_usd": float(row.total_cost or 0),
            "total_tokens": int(row.total_tokens or 0),
            "total_calls": int(row.total_calls or 0),
        }

    @staticmethod
    async def get_cost_breakdown_by_model(
        db: AsyncSession, tenant_id: str, days: int = 30
    ) -> List[Dict]:
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                LLMUsageLog.provider,
                LLMUsageLog.model,
                func.sum(LLMUsageLog.cost_usd).label("cost"),
                func.sum(LLMUsageLog.total_tokens).label("tokens"),
                func.count(LLMUsageLog.id).label("calls"),
            )
            .where(
                LLMUsageLog.tenant_id == tenant_id, LLMUsageLog.timestamp >= start_date
            )
            .group_by(LLMUsageLog.provider, LLMUsageLog.model)
            .order_by(func.sum(LLMUsageLog.cost_usd).desc())
        )

        return [
            {
                "provider": row.provider,
                "model": row.model,
                "cost_usd": float(row.cost),
                "tokens": int(row.tokens),
                "calls": int(row.calls),
            }
            for row in result
        ]
