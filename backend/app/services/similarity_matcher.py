"""
Camada 2b: Product matching via text similarity + LLM confirmation.

For products without EAN, this service:
1. Finds candidates from other marketplaces using text similarity
2. Sends top candidates to LLM for confirmation
3. Groups products with high-confidence matches (≥ 85%)
"""

import json
import logging
import re
import string
from difflib import SequenceMatcher

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.product import Product, ProductGroup
from app.services.llm_client import call_llm

logger = logging.getLogger(__name__)

STOPWORDS = {
    "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas",
    "um", "uma", "uns", "umas", "o", "a", "os", "as", "e", "ou",
    "com", "por", "para", "the", "a", "an", "of", "in", "on", "and",
    "or", "with", "for", "to", "from",
}

SIMILARITY_PROMPT = """\
You are a product matching expert. Your job is to determine if a target product \
and candidate products are the SAME PHYSICAL PRODUCT sold on different marketplaces.

Rules:
- "Same product" means identical brand, model, and key specs (storage, RAM, color, size).
- Ignore naming conventions between marketplaces (e.g., "iPhone 15 128GB" vs "Apple iPhone 15 128 GB").
- Ignore language differences (Portuguese vs English).
- Focus on the core product identity (brand, model, specs). Ignore listing details about delivery, format, or condition.
- Accessories, cases, or different variants (e.g., 128GB vs 256GB) are NOT the same product.

Target product:
{target}

Candidates:
{candidates}

For each candidate, return a JSON array with objects containing:
- "candidate_id": the candidate's ID
- "is_same_product": true/false
- "confidence": 0.0 to 1.0
- "reasoning": brief explanation

Return ONLY valid JSON array, no markdown formatting or extra text.
"""

TEXT_SIMILARITY_THRESHOLD = 0.3
LLM_CONFIDENCE_THRESHOLD = 0.75
MAX_CANDIDATES = 5


def normalize_name(name: str | None) -> str:
    """Normalize product name: lowercase, remove punctuation, strip stopwords."""
    if not name:
        return ""
    text = name.lower().strip()
    text = text.translate(str.maketrans("", "", string.punctuation))
    words = text.split()
    words = [w for w in words if w not in STOPWORDS]
    return " ".join(words)


def text_similarity(name_a: str, name_b: str) -> float:
    """Compute similarity ratio between two normalized product names."""
    norm_a = normalize_name(name_a)
    norm_b = normalize_name(name_b)
    if not norm_a or not norm_b:
        return 0.0
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def find_candidates(
    db: Session, product: Product, limit: int = 20
) -> list[tuple[Product, float]]:
    """Find candidate products from other marketplaces with similar names.

    Returns list of (product, similarity_score) tuples, sorted by score desc.
    """
    if not product.name:
        return []

    # Query products from different marketplaces, with names, not in same group
    query = select(Product).where(
        Product.marketplace != product.marketplace,
        Product.name.isnot(None),
        Product.id != product.id,
    )

    # Exclude products already in the same group as target
    if product.group_id:
        query = query.where(
            (Product.group_id != product.group_id) | (Product.group_id.is_(None))
        )

    candidates = db.execute(query).scalars().all()

    # Score and filter by text similarity
    scored = []
    for candidate in candidates:
        score = text_similarity(product.name, candidate.name)
        if score >= TEXT_SIMILARITY_THRESHOLD:
            scored.append((candidate, score))

    # Sort by score descending, return top N
    scored.sort(key=lambda x: x[1], reverse=True)
    result = scored[:limit]
    logger.debug(
        "Found %d candidates (from %d total) for '%s'",
        len(result), len(candidates), product.name,
    )
    return result


async def match_product_by_similarity(
    db: Session, product: Product
) -> ProductGroup | None:
    """Try to match a product via text similarity + LLM confirmation.

    Returns the matched/created group, or None if no match found.
    Skips products that have EAN, already have a group, or have no name.
    """
    # Guard clauses — skip if already in a multi-product group
    if product.group_id:
        group_size = db.execute(
            select(func.count(Product.id)).where(
                Product.group_id == product.group_id
            )
        ).scalar()
        if group_size > 1:
            logger.debug("Skipping similarity match for %s — already in group with %d products", product.id, group_size)
            return None
    if not product.name:
        logger.debug("Skipping similarity match for %s — no name", product.id)
        return None

    logger.info("Starting similarity match for '%s' (%s)", product.name, product.marketplace)

    # Find candidates
    scored_candidates = find_candidates(db, product, limit=MAX_CANDIDATES)
    if not scored_candidates:
        logger.info("No similarity candidates found for '%s'", product.name)
        return None

    candidates = [c for c, _ in scored_candidates]

    # Build prompt
    target_info = f"ID: {product.id}\nName: {product.name}\nMarketplace: {product.marketplace}"
    candidates_info = "\n\n".join(
        f"ID: {c.id}\nName: {c.name}\nMarketplace: {c.marketplace}"
        for c in candidates
    )

    prompt = SIMILARITY_PROMPT.format(
        target=target_info, candidates=candidates_info
    )

    # Call LLM
    logger.info(
        "Sending %d candidates to LLM for '%s'",
        len(candidates), product.name,
    )
    try:
        result = await call_llm(user_content=prompt)

        # Track LLM token usage
        from app.services.llm_usage_tracker import track_llm_usage

        track_llm_usage(
            db,
            "similarity_matching",
            result.model,
            result.input_tokens,
            result.output_tokens,
            product_id=product.id,
        )

        response_text = result.text
        # Strip markdown code fences if present
        response_text = re.sub(r"^```(?:json)?\s*", "", response_text.strip())
        response_text = re.sub(r"\s*```$", "", response_text.strip())

        results = json.loads(response_text)
    except Exception as e:
        logger.error(f"[Wardrop] LLM similarity matching failed: {e}")
        return None

    # Find best match above threshold
    best_match = None
    best_confidence = 0.0

    candidate_map = {str(c.id): c for c in candidates}

    for result in results:
        if (
            result.get("is_same_product")
            and result.get("confidence", 0) >= LLM_CONFIDENCE_THRESHOLD
            and result.get("confidence", 0) > best_confidence
        ):
            candidate_id = str(result["candidate_id"])
            if candidate_id in candidate_map:
                best_match = candidate_map[candidate_id]
                best_confidence = result["confidence"]

    if not best_match:
        logger.info("No LLM-confirmed match for '%s'", product.name)
        return None

    logger.info(
        f"[Wardrop] Similarity match: {product.name} ↔ {best_match.name} "
        f"(confidence: {best_confidence:.0%})"
    )

    return _group_products(db, product, best_match)


def _group_products(
    db: Session, product: Product, matched: Product
) -> ProductGroup:
    """Group two matched products together.

    If the matched product already has a group, add the new product to it.
    Otherwise, create a new group for both.
    """
    if matched.group_id:
        group = db.get(ProductGroup, matched.group_id)
        product.group_id = group.id
        return group

    group = ProductGroup(
        canonical_name=product.name,
    )
    db.add(group)
    db.flush()

    product.group_id = group.id
    matched.group_id = group.id
    return group
