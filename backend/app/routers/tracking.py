import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.price_history import UserProduct
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductOut, ProductListItem
from app.schemas.user import TrackRequest
from app.services.auth import get_current_user
from app.services.product_enrichment import enrich_product_with_analytics

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/track", status_code=201)
def track_product(
    data: TrackRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Collect all products to track (including group siblings)
    products_to_track = [product]
    if product.group_id:
        siblings = db.execute(
            select(Product).where(
                Product.group_id == product.group_id,
                Product.id != product.id,
            )
        ).scalars().all()
        products_to_track.extend(siblings)

    for p in products_to_track:
        existing = db.execute(
            select(UserProduct).where(
                UserProduct.user_id == user.id,
                UserProduct.product_id == p.id,
            )
        ).scalar_one_or_none()

        if existing:
            existing.target_price = data.target_price
            existing.notify_on_any_drop = data.notify_on_any_drop
        else:
            logger.info("User %s started tracking product %s (%s)", user.id, p.id, p.marketplace)
            up = UserProduct(
                user_id=user.id,
                product_id=p.id,
                target_price=data.target_price,
                notify_on_any_drop=data.notify_on_any_drop,
            )
            db.add(up)

    db.commit()
    return {"status": "tracking"}


@router.delete("/untrack/{product_id}")
def untrack_product(
    product_id: UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    up = db.execute(
        select(UserProduct).where(
            UserProduct.user_id == user.id,
            UserProduct.product_id == product_id,
        )
    ).scalar_one_or_none()

    if not up:
        raise HTTPException(status_code=404, detail="Not tracking this product")

    db.delete(up)
    db.commit()
    logger.info("User %s stopped tracking product %s", user.id, product_id)
    return {"status": "untracked"}


@router.get("/products", response_model=list[ProductListItem])
def get_tracked_products(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all tracked products for the current user with analytics."""
    user_products = db.execute(
        select(UserProduct).where(UserProduct.user_id == user.id)
    ).scalars().all()

    products = [
        db.get(Product, up.product_id)
        for up in user_products
    ]
    products = [p for p in products if p is not None]

    # Group products by group_id
    grouped_products: dict[UUID, list[Product]] = {}
    standalone_products: list[Product] = []

    for product in products:
        if product.group_id:
            grouped_products.setdefault(product.group_id, []).append(product)
        else:
            standalone_products.append(product)

    # Build enriched result
    result: list[ProductListItem] = []

    # Enrich grouped products
    for group_id, group_products in grouped_products.items():
        sorted_by_price = sorted(
            group_products,
            key=lambda p: float(p.current_price) if p.current_price is not None else float("inf"),
        )
        cheapest = sorted_by_price[0]
        result.append(enrich_product_with_analytics(db, cheapest, group_products))

    # Enrich standalone products
    for product in standalone_products:
        result.append(enrich_product_with_analytics(db, product))

    return result
