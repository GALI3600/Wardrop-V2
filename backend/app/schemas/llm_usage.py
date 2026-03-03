from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel


class LLMUsageOut(BaseModel):
    id: int
    operation: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    product_id: UUID | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyUsageOut(BaseModel):
    date: str
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: str


class MonthlyUsageOut(BaseModel):
    month: str
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: str


class UsageTotalsOut(BaseModel):
    total_calls: int
    total_input_tokens: int
    total_output_tokens: int
    total_cost_usd: str


class UsageSummaryOut(BaseModel):
    daily: list[DailyUsageOut]
    monthly: list[MonthlyUsageOut]
    totals: UsageTotalsOut
