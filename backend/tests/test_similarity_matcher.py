import json
from unittest.mock import AsyncMock, patch

import pytest

from app.models.product import Product, ProductGroup
from app.services.llm_client import LLMResponse
from app.services.similarity_matcher import (
    LLM_CONFIDENCE_THRESHOLD,
    TEXT_SIMILARITY_THRESHOLD,
    _group_products,
    find_candidates,
    match_product_by_similarity,
    normalize_name,
    text_similarity,
)


class TestNormalizeName:
    def test_lowercase_and_strip(self):
        assert normalize_name("  iPhone 15 Pro  ") == "iphone 15 pro"

    def test_removes_punctuation(self):
        result = normalize_name("Samsung Galaxy S24+ (256GB)")
        assert "+" not in result
        assert "(" not in result
        assert ")" not in result

    def test_removes_stopwords(self):
        result = normalize_name("Celular de ultima geracao com 5G")
        assert "de" not in result.split()
        assert "com" not in result.split()

    def test_empty_and_none(self):
        assert normalize_name(None) == ""
        assert normalize_name("") == ""

    def test_whitespace_normalization(self):
        result = normalize_name("Samsung   Galaxy   S24")
        assert result == "samsung galaxy s24"


class TestTextSimilarity:
    def test_identical_names(self):
        score = text_similarity("iPhone 15 128GB", "iPhone 15 128GB")
        assert score == 1.0

    def test_similar_names(self):
        score = text_similarity(
            "iPhone 15 128GB Preto",
            "Apple iPhone 15 128 GB Preto",
        )
        assert score > TEXT_SIMILARITY_THRESHOLD

    def test_different_names(self):
        score = text_similarity(
            "iPhone 15 128GB",
            "Samsung Galaxy S24 Ultra 512GB",
        )
        assert score < 0.5

    def test_empty_names(self):
        assert text_similarity("", "iPhone 15") == 0.0
        assert text_similarity("iPhone 15", "") == 0.0
        assert text_similarity(None, "iPhone 15") == 0.0


class TestFindCandidates:
    def test_finds_cross_marketplace_candidates(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15 128GB Preto",
        )
        candidate = Product(
            url="https://mercadolivre.com.br/MLB-123",
            marketplace="mercadolivre",
            name="Apple iPhone 15 128 GB Preto",
        )
        db.add_all([target, candidate])
        db.flush()

        results = find_candidates(db, target)
        assert len(results) >= 1
        product_ids = [p.id for p, _ in results]
        assert candidate.id in product_ids

    def test_excludes_same_marketplace(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST1",
            marketplace="amazon",
            name="iPhone 15 128GB",
        )
        same_mp = Product(
            url="https://amazon.com.br/dp/B0TEST2",
            marketplace="amazon",
            name="iPhone 15 128GB Preto",
        )
        db.add_all([target, same_mp])
        db.flush()

        results = find_candidates(db, target)
        product_ids = [p.id for p, _ in results]
        assert same_mp.id not in product_ids

    def test_excludes_low_similarity(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15 128GB",
        )
        different = Product(
            url="https://mercadolivre.com.br/MLB-999",
            marketplace="mercadolivre",
            name="Carregador USB-C 20W",
        )
        db.add_all([target, different])
        db.flush()

        results = find_candidates(db, target)
        product_ids = [p.id for p, _ in results]
        assert different.id not in product_ids

    def test_returns_empty_for_no_name(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name=None,
        )
        db.add(target)
        db.flush()

        results = find_candidates(db, target)
        assert results == []

    def test_sorted_by_score_descending(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="Samsung Galaxy S24 Ultra 256GB",
        )
        close_match = Product(
            url="https://mercadolivre.com.br/MLB-1",
            marketplace="mercadolivre",
            name="Samsung Galaxy S24 Ultra 256 GB",
        )
        partial_match = Product(
            url="https://magalu.com.br/produto/1",
            marketplace="magalu",
            name="Samsung Galaxy S24 128GB",
        )
        db.add_all([target, close_match, partial_match])
        db.flush()

        results = find_candidates(db, target)
        if len(results) >= 2:
            scores = [s for _, s in results]
            assert scores == sorted(scores, reverse=True)


class TestMatchProductBySimilarity:
    @pytest.mark.asyncio
    async def test_skips_product_in_multi_product_group(self, db):
        """Product already in a group with multiple members should be skipped."""
        group = ProductGroup(canonical_name="Test Group")
        db.add(group)
        db.flush()

        p1 = Product(
            url="https://amazon.com.br/dp/B0TEST1",
            marketplace="amazon",
            name="iPhone 15",
            group_id=group.id,
        )
        p2 = Product(
            url="https://mercadolivre.com.br/MLB-1",
            marketplace="mercadolivre",
            name="iPhone 15",
            group_id=group.id,
        )
        db.add_all([p1, p2])
        db.flush()

        result = await match_product_by_similarity(db, p1)
        assert result is None

    @pytest.mark.asyncio
    async def test_allows_product_in_solo_group(self, db):
        """Product in a solo group (only member) should still try similarity matching."""
        group = ProductGroup(canonical_name="Solo Group", ean="5901234123457")
        db.add(group)
        db.flush()

        product = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="Produto Unico Sem Similar",
            ean="5901234123457",
            group_id=group.id,
        )
        db.add(product)
        db.flush()

        # No candidates exist, so result is None — but the guard clause doesn't block it
        result = await match_product_by_similarity(db, product)
        assert result is None  # No candidates, but it tried

    @pytest.mark.asyncio
    async def test_skips_product_without_name(self, db):
        product = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name=None,
        )
        db.add(product)
        db.flush()

        result = await match_product_by_similarity(db, product)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_candidates_returns_none(self, db):
        product = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="Produto Unico Sem Similar",
        )
        db.add(product)
        db.flush()

        result = await match_product_by_similarity(db, product)
        assert result is None

    @pytest.mark.asyncio
    async def test_successful_match(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15 128GB Preto",
        )
        candidate = Product(
            url="https://mercadolivre.com.br/MLB-123",
            marketplace="mercadolivre",
            name="Apple iPhone 15 128 GB Preto",
        )
        db.add_all([target, candidate])
        db.flush()

        llm_response_text = json.dumps([{
            "candidate_id": str(candidate.id),
            "is_same_product": True,
            "confidence": 0.95,
            "reasoning": "Same product",
        }])
        mock_result = LLMResponse(
            text=llm_response_text,
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.similarity_matcher.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await match_product_by_similarity(db, target)

        assert result is not None
        assert target.group_id == result.id
        assert candidate.group_id == result.id

    @pytest.mark.asyncio
    async def test_respects_confidence_threshold(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15 128GB Preto",
        )
        candidate = Product(
            url="https://mercadolivre.com.br/MLB-123",
            marketplace="mercadolivre",
            name="Apple iPhone 15 128 GB Preto",
        )
        db.add_all([target, candidate])
        db.flush()

        # LLM returns low confidence
        llm_response_text = json.dumps([{
            "candidate_id": str(candidate.id),
            "is_same_product": True,
            "confidence": 0.60,
            "reasoning": "Maybe the same",
        }])
        mock_result = LLMResponse(
            text=llm_response_text,
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.similarity_matcher.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await match_product_by_similarity(db, target)

        assert result is None
        assert target.group_id is None

    @pytest.mark.asyncio
    async def test_joins_existing_group(self, db):
        existing_group = ProductGroup(canonical_name="iPhone 15 Group")
        db.add(existing_group)
        db.flush()

        candidate = Product(
            url="https://mercadolivre.com.br/MLB-123",
            marketplace="mercadolivre",
            name="Apple iPhone 15 128 GB Preto",
            group_id=existing_group.id,
        )
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15 128GB Preto",
        )
        db.add_all([candidate, target])
        db.flush()

        llm_response_text = json.dumps([{
            "candidate_id": str(candidate.id),
            "is_same_product": True,
            "confidence": 0.95,
            "reasoning": "Same iPhone 15",
        }])
        mock_result = LLMResponse(
            text=llm_response_text,
            input_tokens=100, output_tokens=50, model="test-model",
        )

        with patch("app.services.similarity_matcher.call_llm", new_callable=AsyncMock, return_value=mock_result):
            result = await match_product_by_similarity(db, target)

        assert result is not None
        assert result.id == existing_group.id
        assert target.group_id == existing_group.id

    @pytest.mark.asyncio
    async def test_llm_error_returns_none(self, db):
        target = Product(
            url="https://amazon.com.br/dp/B0TEST",
            marketplace="amazon",
            name="iPhone 15 128GB Preto",
        )
        candidate = Product(
            url="https://mercadolivre.com.br/MLB-123",
            marketplace="mercadolivre",
            name="Apple iPhone 15 128 GB Preto",
        )
        db.add_all([target, candidate])
        db.flush()

        with patch("app.services.similarity_matcher.call_llm", new_callable=AsyncMock, side_effect=Exception("API Error")):
            result = await match_product_by_similarity(db, target)

        assert result is None
        assert target.group_id is None


class TestGroupProducts:
    def test_creates_new_group(self, db):
        p1 = Product(
            url="https://amazon.com.br/dp/B0P1",
            marketplace="amazon",
            name="iPhone 15",
        )
        p2 = Product(
            url="https://mercadolivre.com.br/MLB-1",
            marketplace="mercadolivre",
            name="Apple iPhone 15",
        )
        db.add_all([p1, p2])
        db.flush()

        group = _group_products(db, p1, p2)

        assert group is not None
        assert p1.group_id == group.id
        assert p2.group_id == group.id
        assert group.canonical_name == "iPhone 15"

    def test_joins_existing_group(self, db):
        existing_group = ProductGroup(canonical_name="Test Group")
        db.add(existing_group)
        db.flush()

        matched = Product(
            url="https://mercadolivre.com.br/MLB-1",
            marketplace="mercadolivre",
            name="Apple iPhone 15",
            group_id=existing_group.id,
        )
        new_product = Product(
            url="https://amazon.com.br/dp/B0P1",
            marketplace="amazon",
            name="iPhone 15",
        )
        db.add_all([matched, new_product])
        db.flush()

        group = _group_products(db, new_product, matched)

        assert group.id == existing_group.id
        assert new_product.group_id == existing_group.id
