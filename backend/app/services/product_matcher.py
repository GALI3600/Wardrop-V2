"""
Camada 2: Automatic product matching via EAN/GTIN.
Camada 2b: Background similarity matching via LLM.

When a product is saved with an EAN, this service:
1. Searches for an existing product_group with the same EAN
2. If found → links the product to that group
3. If not found → creates a new group and links the product

For products without EAN, match_product_by_similarity_background()
runs in the background to find matches via text similarity + LLM.
"""

import asyncio
import logging
import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.price_history import UserProduct
from app.models.product import Product, ProductGroup
from app.services.similarity_matcher import TEXT_SIMILARITY_THRESHOLD, text_similarity


def propagate_tracking_to_group(db: Session, group_id) -> None:
    """When a product joins a group, ensure all users tracking any product
    in the group also track the other products in the group."""
    products = db.execute(
        select(Product).where(Product.group_id == group_id)
    ).scalars().all()
    product_ids = [p.id for p in products]

    # Get all user_ids tracking any product in this group
    user_trackings = db.execute(
        select(UserProduct).where(UserProduct.product_id.in_(product_ids))
    ).scalars().all()

    user_ids = {ut.user_id for ut in user_trackings}
    existing_pairs = {(ut.user_id, ut.product_id) for ut in user_trackings}

    for user_id in user_ids:
        for pid in product_ids:
            if (user_id, pid) not in existing_pairs:
                db.add(UserProduct(
                    user_id=user_id,
                    product_id=pid,
                    notify_on_any_drop=True,
                ))
                logger.info("Auto-tracked product %s for user %s (group sync)", pid, user_id)

logger = logging.getLogger(__name__)


def match_product_by_ean(db: Session, product: Product) -> ProductGroup | None:
    """Try to match a product to an existing group by EAN.

    Returns the matched/created group, or None if the product has no EAN.
    """
    if not product.ean:
        return None

    logger.debug("Attempting EAN match for product %s (EAN: %s)", product.id, product.ean)

    # Search for existing group with this EAN
    existing_group = db.execute(
        select(ProductGroup).where(ProductGroup.ean == product.ean)
    ).scalar_one_or_none()

    if existing_group:
        product.group_id = existing_group.id
        logger.info(
            "EAN match: product %s joined existing group %s (EAN: %s)",
            product.id, existing_group.id, product.ean,
        )
        propagate_tracking_to_group(db, existing_group.id)
        return existing_group

    # No group exists — check if another product has this EAN but no group yet
    other_product = db.execute(
        select(Product).where(
            Product.ean == product.ean,
            Product.id != product.id,
        )
    ).scalars().first()

    if other_product:
        # Create a new group for both products
        group = ProductGroup(
            canonical_name=product.name,
            ean=product.ean,
        )
        db.add(group)
        db.flush()

        product.group_id = group.id
        other_product.group_id = group.id
        logger.info(
            "EAN match: created group %s for products %s and %s (EAN: %s)",
            group.id, product.id, other_product.id, product.ean,
        )
        propagate_tracking_to_group(db, group.id)
        return group

    # Only one product with this EAN so far — create group for future matches
    group = ProductGroup(
        canonical_name=product.name,
        ean=product.ean,
    )
    db.add(group)
    db.flush()

    product.group_id = group.id
    logger.info(
        "EAN match: created solo group %s for product %s (EAN: %s)",
        group.id, product.id, product.ean,
    )
    return group


def trigger_reverse_similarity(db: Session, product: Product) -> None:
    """Check if orphan products from other marketplaces match this product.

    An orphan is a product with no group and no EAN, from a different marketplace.
    For each orphan with sufficient text similarity, schedule a background
    similarity match so it can be grouped.
    """
    if not product.name:
        return

    orphans = db.execute(
        select(Product).where(
            Product.group_id.is_(None),
            Product.ean.is_(None),
            Product.marketplace != product.marketplace,
            Product.name.isnot(None),
            Product.id != product.id,
        )
    ).scalars().all()

    for orphan in orphans:
        score = text_similarity(product.name, orphan.name)
        if score >= TEXT_SIMILARITY_THRESHOLD:
            logger.info(
                "Reverse similarity: scheduling match for orphan %s ('%s', score=%.2f)",
                orphan.id, orphan.name, score,
            )
            asyncio.create_task(match_product_by_similarity_background(orphan.id))


async def match_product_by_similarity_background(product_id: uuid.UUID) -> None:
    """Background task: try to match a product via similarity + LLM.

    Opens its own DB session so it's decoupled from the request lifecycle.
    """
    from app.db.database import SessionLocal
    from app.services.similarity_matcher import match_product_by_similarity

    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product:
            logger.warning(f"[Wardrop] Similarity match: product {product_id} not found")
            return

        # Re-check: another concurrent task may have already grouped this product
        db.refresh(product)
        if product.group_id:
            group_size = db.execute(
                select(func.count(Product.id)).where(
                    Product.group_id == product.group_id
                )
            ).scalar()
            if group_size > 1:
                logger.debug(
                    "[Wardrop] Similarity match skipped for %s — already grouped by concurrent task",
                    product_id,
                )
                return

        result = await match_product_by_similarity(db, product)
        if result:
            propagate_tracking_to_group(db, result.id)
            db.commit()
            logger.info(
                f"[Wardrop] Similarity match: product {product_id} → group {result.id}"
            )
    except Exception as e:
        db.rollback()
        logger.error(f"[Wardrop] Similarity match failed for {product_id}: {e}")
    finally:
        db.close()
