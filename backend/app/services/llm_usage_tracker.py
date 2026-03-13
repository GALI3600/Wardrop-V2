"""
LLM usage tracking: records token consumption and estimated cost per API call.
"""

import logging
from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.llm_usage import LLMUsage
from app.utils import now_brasilia

logger = logging.getLogger(__name__)

# Pricing per token (USD)
PRICING: dict[str, dict[str, Decimal]] = {
    "claude-haiku-4-5-20251001": {
        "input": Decimal("1.00") / 1_000_000,
        "output": Decimal("5.00") / 1_000_000,
    },
    "llama-3.3-70b-versatile": {
        "input": Decimal("0.59") / 1_000_000,
        "output": Decimal("0.79") / 1_000_000,
    },
    "llama-3.1-8b-instant": {
        "input": Decimal("0.05") / 1_000_000,
        "output": Decimal("0.08") / 1_000_000,
    },
    "gpt-4o-mini": {
        "input": Decimal("0.15") / 1_000_000,
        "output": Decimal("0.60") / 1_000_000,
    },
    "gemini-2.5-flash": {
        "input": Decimal("0.15") / 1_000_000,
        "output": Decimal("0.60") / 1_000_000,
    },
}

# Fallback pricing for unknown models (uses Haiku rates)
_FALLBACK_PRICING = PRICING["claude-haiku-4-5-20251001"]


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    """Calculate estimated cost in USD for an LLM call."""
    pricing = PRICING.get(model, _FALLBACK_PRICING)
    cost = (pricing["input"] * input_tokens) + (pricing["output"] * output_tokens)
    return cost.quantize(Decimal("0.000001"))


def track_llm_usage(
    db: Session,
    operation: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    product_id=None,
) -> LLMUsage:
    """Record an LLM API call with token counts and estimated cost."""
    cost = calculate_cost(model, input_tokens, output_tokens)

    logger.info(
        "LLM | %s | %d in / %d out | $%s",
        operation, input_tokens, output_tokens, cost,
    )

    record = LLMUsage(
        operation=operation,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cost_usd=cost,
        product_id=product_id,
    )
    db.add(record)
    db.flush()
    return record


def get_usage_summary(db: Session, days: int = 30) -> dict:
    """Get aggregated usage statistics by day and month."""
    cutoff = now_brasilia() - timedelta(days=days)

    # Daily aggregation
    daily_rows = db.execute(
        select(
            func.date(LLMUsage.created_at).label("date"),
            func.count().label("total_calls"),
            func.sum(LLMUsage.input_tokens).label("total_input_tokens"),
            func.sum(LLMUsage.output_tokens).label("total_output_tokens"),
            func.sum(LLMUsage.cost_usd).label("total_cost_usd"),
        )
        .where(LLMUsage.created_at >= cutoff)
        .group_by(func.date(LLMUsage.created_at))
        .order_by(func.date(LLMUsage.created_at).desc())
    ).all()

    daily = [
        {
            "date": str(row.date),
            "total_calls": row.total_calls,
            "total_input_tokens": row.total_input_tokens or 0,
            "total_output_tokens": row.total_output_tokens or 0,
            "total_cost_usd": str(row.total_cost_usd or Decimal("0")),
        }
        for row in daily_rows
    ]

    # Monthly aggregation (all time)
    # Use strftime for SQLite compatibility in tests, works with PostgreSQL too
    monthly_rows = db.execute(
        select(
            func.strftime("%Y-%m", LLMUsage.created_at).label("month"),
            func.count().label("total_calls"),
            func.sum(LLMUsage.input_tokens).label("total_input_tokens"),
            func.sum(LLMUsage.output_tokens).label("total_output_tokens"),
            func.sum(LLMUsage.cost_usd).label("total_cost_usd"),
        )
        .group_by(func.strftime("%Y-%m", LLMUsage.created_at))
        .order_by(func.strftime("%Y-%m", LLMUsage.created_at).desc())
    ).all()

    monthly = [
        {
            "month": row.month,
            "total_calls": row.total_calls,
            "total_input_tokens": row.total_input_tokens or 0,
            "total_output_tokens": row.total_output_tokens or 0,
            "total_cost_usd": str(row.total_cost_usd or Decimal("0")),
        }
        for row in monthly_rows
    ]

    # Totals (all time)
    totals_row = db.execute(
        select(
            func.count().label("total_calls"),
            func.coalesce(func.sum(LLMUsage.input_tokens), 0).label("total_input_tokens"),
            func.coalesce(func.sum(LLMUsage.output_tokens), 0).label("total_output_tokens"),
            func.coalesce(func.sum(LLMUsage.cost_usd), 0).label("total_cost_usd"),
        )
    ).one()

    totals = {
        "total_calls": totals_row.total_calls,
        "total_input_tokens": totals_row.total_input_tokens,
        "total_output_tokens": totals_row.total_output_tokens,
        "total_cost_usd": str(totals_row.total_cost_usd),
    }

    return {"daily": daily, "monthly": monthly, "totals": totals}
