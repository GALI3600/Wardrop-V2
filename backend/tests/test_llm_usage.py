import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest

from app.models.llm_usage import LLMUsage
from app.models.product import Product
from app.services.llm_usage_tracker import (
    PRICING,
    calculate_cost,
    get_usage_summary,
    track_llm_usage,
)


class TestCalculateCost:
    def test_haiku_pricing(self):
        # 1000 input tokens @ $1/M = $0.001000
        # 500 output tokens @ $5/M = $0.002500
        cost = calculate_cost("claude-haiku-4-5-20251001", 1000, 500)
        assert cost == Decimal("0.003500")

    def test_unknown_model_uses_fallback(self):
        # Should use Haiku pricing as fallback
        cost = calculate_cost("unknown-model", 1000, 500)
        assert cost == Decimal("0.003500")

    def test_zero_tokens(self):
        cost = calculate_cost("claude-haiku-4-5-20251001", 0, 0)
        assert cost == Decimal("0.000000")

    def test_large_token_count(self):
        # 1M input + 1M output = $1 + $5 = $6
        cost = calculate_cost("claude-haiku-4-5-20251001", 1_000_000, 1_000_000)
        assert cost == Decimal("6.000000")

    def test_groq_llama_70b_pricing(self):
        # 1000 input @ $0.59/M = $0.000590
        # 500 output @ $0.79/M = $0.000395
        cost = calculate_cost("llama-3.3-70b-versatile", 1000, 500)
        assert cost == Decimal("0.000985")

    def test_groq_llama_8b_pricing(self):
        # 1000 input @ $0.05/M = $0.000050
        # 500 output @ $0.08/M = $0.000040
        cost = calculate_cost("llama-3.1-8b-instant", 1000, 500)
        assert cost == Decimal("0.000090")

    def test_openai_gpt4o_mini_pricing(self):
        # 1000 input @ $0.15/M = $0.000150
        # 500 output @ $0.60/M = $0.000300
        cost = calculate_cost("gpt-4o-mini", 1000, 500)
        assert cost == Decimal("0.000450")

    def test_gemini_flash_pricing(self):
        # 1000 input @ $0.15/M = $0.000150
        # 500 output @ $0.60/M = $0.000300
        cost = calculate_cost("gemini-2.5-flash", 1000, 500)
        assert cost == Decimal("0.000450")


class TestTrackLLMUsage:
    def test_saves_record_to_db(self, db):
        record = track_llm_usage(
            db, "product_parsing", "claude-haiku-4-5-20251001", 500, 200
        )
        db.commit()

        assert record.id is not None
        assert record.operation == "product_parsing"
        assert record.model == "claude-haiku-4-5-20251001"
        assert record.input_tokens == 500
        assert record.output_tokens == 200

    def test_calculates_cost_correctly(self, db):
        record = track_llm_usage(
            db, "similarity_matching", "claude-haiku-4-5-20251001", 1000, 500
        )
        assert record.cost_usd == Decimal("0.003500")

    def test_saves_product_id(self, db):
        product = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="Test Product",
        )
        db.add(product)
        db.flush()

        record = track_llm_usage(
            db,
            "similarity_matching",
            "claude-haiku-4-5-20251001",
            1000,
            500,
            product_id=product.id,
        )
        assert record.product_id == product.id

    def test_record_has_timestamp(self, db):
        record = track_llm_usage(
            db, "product_parsing", "claude-haiku-4-5-20251001", 100, 50
        )
        assert record.created_at is not None


class TestGetUsageSummary:
    def test_empty_db_returns_zeros(self, db):
        summary = get_usage_summary(db)

        assert summary["daily"] == []
        assert summary["monthly"] == []
        assert summary["totals"]["total_calls"] == 0
        assert summary["totals"]["total_input_tokens"] == 0

    def test_aggregates_by_day(self, db):
        # Add two records for today
        track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 500, 200)
        track_llm_usage(db, "similarity_matching", "claude-haiku-4-5-20251001", 1000, 500)
        db.commit()

        summary = get_usage_summary(db)

        assert len(summary["daily"]) == 1
        day = summary["daily"][0]
        assert day["total_calls"] == 2
        assert day["total_input_tokens"] == 1500
        assert day["total_output_tokens"] == 700

    def test_aggregates_by_month(self, db):
        track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 500, 200)
        db.commit()

        summary = get_usage_summary(db)

        assert len(summary["monthly"]) == 1
        month = summary["monthly"][0]
        assert month["total_calls"] == 1

    def test_totals_accumulate(self, db):
        track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 500, 200)
        track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 300, 100)
        track_llm_usage(db, "similarity_matching", "claude-haiku-4-5-20251001", 1000, 500)
        db.commit()

        summary = get_usage_summary(db)
        totals = summary["totals"]

        assert totals["total_calls"] == 3
        assert totals["total_input_tokens"] == 1800
        assert totals["total_output_tokens"] == 800


class TestMetricsEndpoints:
    def test_usage_summary_endpoint(self, client, db):
        # Add a record
        track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 500, 200)
        db.commit()

        response = client.get("/api/metrics/usage")
        assert response.status_code == 200
        data = response.json()
        assert "daily" in data
        assert "monthly" in data
        assert "totals" in data
        assert data["totals"]["total_calls"] == 1

    def test_usage_summary_empty(self, client):
        response = client.get("/api/metrics/usage")
        assert response.status_code == 200
        data = response.json()
        assert data["totals"]["total_calls"] == 0

    def test_recent_usage_endpoint(self, client, db):
        track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 500, 200)
        track_llm_usage(db, "similarity_matching", "claude-haiku-4-5-20251001", 1000, 500)
        db.commit()

        response = client.get("/api/metrics/usage/recent")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["operation"] == "similarity_matching"
        assert data[1]["operation"] == "product_parsing"

    def test_recent_usage_respects_limit(self, client, db):
        for i in range(5):
            track_llm_usage(db, "product_parsing", "claude-haiku-4-5-20251001", 100 * i, 50 * i)
        db.commit()

        response = client.get("/api/metrics/usage/recent?limit=3")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_recent_usage_empty(self, client):
        response = client.get("/api/metrics/usage/recent")
        assert response.status_code == 200
        data = response.json()
        assert data == []
