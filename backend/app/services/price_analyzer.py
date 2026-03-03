import logging
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.price_history import PriceHistory, UserProduct
from app.models.product import Product
from app.services.notifier import notify_price_drop

logger = logging.getLogger(__name__)


def check_price_drop(db: Session, product: Product, new_price: Decimal):
    """Check if the new price is a drop and notify relevant users."""
    if product.current_price is None:
        return

    old_price = product.current_price
    if new_price >= old_price:
        return

    logger.info(
        "Price drop detected for '%s': R$%s → R$%s",
        product.name, old_price, new_price,
    )

    # Find all users tracking this product
    user_products = db.execute(
        select(UserProduct).where(UserProduct.product_id == product.id)
    ).scalars().all()

    for up in user_products:
        user = up.user
        should_notify = False

        if up.notify_on_any_drop:
            should_notify = True
        elif up.target_price and new_price <= up.target_price:
            should_notify = True

        if should_notify:
            notify_price_drop(user, product, float(old_price), float(new_price))
