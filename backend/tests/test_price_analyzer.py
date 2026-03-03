from decimal import Decimal
from unittest.mock import patch, call

import pytest

from app.services.price_analyzer import check_price_drop


class TestCheckPriceDrop:
    def test_notifies_on_price_drop(self, db, sample_product, tracked_product, sample_user):
        """Should notify when price drops and user has notify_on_any_drop=True."""
        sample_product.current_price = Decimal("200.00")
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            check_price_drop(db, sample_product, Decimal("150.00"))

            mock_notify.assert_called_once()
            args = mock_notify.call_args
            assert args[0][0].id == sample_user.id
            assert args[0][1].id == sample_product.id
            assert args[0][2] == 200.00  # old price
            assert args[0][3] == 150.00  # new price

    def test_no_notification_on_price_increase(self, db, sample_product, tracked_product):
        """Should NOT notify when price goes up."""
        sample_product.current_price = Decimal("100.00")
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            check_price_drop(db, sample_product, Decimal("150.00"))
            mock_notify.assert_not_called()

    def test_no_notification_on_same_price(self, db, sample_product, tracked_product):
        """Should NOT notify when price stays the same."""
        sample_product.current_price = Decimal("100.00")
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            check_price_drop(db, sample_product, Decimal("100.00"))
            mock_notify.assert_not_called()

    def test_no_notification_when_current_price_is_none(self, db, sample_product, tracked_product):
        """Should NOT notify when there's no previous price."""
        sample_product.current_price = None
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            check_price_drop(db, sample_product, Decimal("50.00"))
            mock_notify.assert_not_called()

    def test_no_notification_when_no_trackers(self, db, sample_product):
        """Should NOT notify when no users are tracking the product."""
        sample_product.current_price = Decimal("200.00")
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            check_price_drop(db, sample_product, Decimal("100.00"))
            mock_notify.assert_not_called()

    def test_notifies_on_target_price_reached(self, db, sample_product, sample_user):
        """Should notify when price drops below target_price even if notify_on_any_drop is False."""
        from app.models.price_history import UserProduct

        up = UserProduct(
            user_id=sample_user.id,
            product_id=sample_product.id,
            target_price=Decimal("100.00"),
            notify_on_any_drop=False,
        )
        db.add(up)
        db.commit()

        sample_product.current_price = Decimal("200.00")
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            # Price drops to 90, below target of 100
            check_price_drop(db, sample_product, Decimal("90.00"))
            mock_notify.assert_called_once()

    def test_no_notification_when_above_target_and_no_any_drop(
        self, db, sample_product, sample_user
    ):
        """Should NOT notify when price drops but stays above target and notify_on_any_drop is False."""
        from app.models.price_history import UserProduct

        up = UserProduct(
            user_id=sample_user.id,
            product_id=sample_product.id,
            target_price=Decimal("50.00"),
            notify_on_any_drop=False,
        )
        db.add(up)
        db.commit()

        sample_product.current_price = Decimal("200.00")
        db.commit()

        with patch("app.services.price_analyzer.notify_price_drop") as mock_notify:
            # Price drops to 150, still above target of 50
            check_price_drop(db, sample_product, Decimal("150.00"))
            mock_notify.assert_not_called()
