import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.llm_usage import LLMUsage
from app.schemas.llm_usage import LLMUsageOut, UsageSummaryOut
from app.services.llm_usage_tracker import get_usage_summary

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/usage", response_model=UsageSummaryOut)
def usage_summary(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """Get aggregated LLM usage statistics by day and month."""
    logger.info("Usage summary requested (last %d days)", days)
    summary = get_usage_summary(db, days=days)
    return summary


@router.get("/usage/recent", response_model=list[LLMUsageOut])
def recent_usage(
    limit: int = Query(default=50, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get the most recent individual LLM API calls."""
    records = db.execute(
        select(LLMUsage)
        .order_by(LLMUsage.created_at.desc())
        .limit(limit)
    ).scalars().all()
    return records
