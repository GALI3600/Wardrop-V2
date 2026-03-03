from unittest.mock import MagicMock, patch

import pytest

from app.services.notifier import (
    notify_price_drop,
    send_email_notification,
    send_push_notification,
)


class TestSendPushNotification:
    @patch("app.services.notifier.settings")
    @patch("app.services.notifier.webpush")
    def test_sends_push_when_configured(self, mock_webpush, mock_settings):
        mock_settings.vapid_private_key = "test-private-key"
        mock_settings.vapid_email = "test@example.com"

        subscription = {"endpoint": "https://push.example.com", "keys": {"p256dh": "key", "auth": "auth"}}
        send_push_notification(subscription, "Title", "Body", "https://example.com")

        mock_webpush.assert_called_once()
        call_kwargs = mock_webpush.call_args
        assert call_kwargs[1]["subscription_info"] == subscription

    @patch("app.services.notifier.settings")
    @patch("app.services.notifier.webpush")
    def test_skips_when_no_vapid_key(self, mock_webpush, mock_settings):
        mock_settings.vapid_private_key = ""

        send_push_notification({}, "Title", "Body")
        mock_webpush.assert_not_called()

    @patch("app.services.notifier.settings")
    @patch("app.services.notifier.webpush")
    def test_handles_webpush_exception(self, mock_webpush, mock_settings):
        from pywebpush import WebPushException

        mock_settings.vapid_private_key = "test-key"
        mock_settings.vapid_email = "test@example.com"
        mock_webpush.side_effect = WebPushException("Push failed")

        # Should not raise
        send_push_notification({"endpoint": "https://x.com"}, "Title", "Body")


class TestSendEmailNotification:
    @patch("app.services.notifier.settings")
    @patch("app.services.notifier.smtplib.SMTP")
    def test_sends_email_when_configured(self, mock_smtp_class, mock_settings):
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_settings.smtp_user = "user"
        mock_settings.smtp_password = "pass"
        mock_settings.smtp_from = "noreply@wardrop.com"

        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__ = MagicMock(return_value=mock_server)
        mock_smtp_class.return_value.__exit__ = MagicMock(return_value=False)

        send_email_notification("user@example.com", "Subject", "<p>Body</p>")

        mock_smtp_class.assert_called_once_with("smtp.example.com", 587)

    @patch("app.services.notifier.settings")
    @patch("app.services.notifier.smtplib.SMTP")
    def test_skips_when_no_smtp_host(self, mock_smtp_class, mock_settings):
        mock_settings.smtp_host = ""

        send_email_notification("user@example.com", "Subject", "<p>Body</p>")
        mock_smtp_class.assert_not_called()

    @patch("app.services.notifier.settings")
    @patch("app.services.notifier.smtplib.SMTP")
    def test_handles_smtp_exception(self, mock_smtp_class, mock_settings):
        mock_settings.smtp_host = "smtp.example.com"
        mock_settings.smtp_port = 587
        mock_smtp_class.side_effect = Exception("SMTP connection failed")

        # Should not raise
        send_email_notification("user@example.com", "Subject", "<p>Body</p>")


class TestNotifyPriceDrop:
    @patch("app.services.notifier.send_email_notification")
    @patch("app.services.notifier.send_push_notification")
    def test_sends_both_push_and_email(self, mock_push, mock_email):
        user = MagicMock()
        user.notify_push = True
        user.push_subscription = {"endpoint": "https://push.example.com"}
        user.notify_email = True
        user.email = "user@example.com"

        product = MagicMock()
        product.name = "iPhone 15"
        product.url = "https://amazon.com.br/dp/B0TEST"

        notify_price_drop(user, product, 4299.00, 3999.00)

        mock_push.assert_called_once()
        mock_email.assert_called_once()

    @patch("app.services.notifier.send_email_notification")
    @patch("app.services.notifier.send_push_notification")
    def test_skips_push_when_disabled(self, mock_push, mock_email):
        user = MagicMock()
        user.notify_push = False
        user.push_subscription = {"endpoint": "https://push.example.com"}
        user.notify_email = True
        user.email = "user@example.com"

        product = MagicMock()
        product.name = "Product"
        product.url = "https://example.com"

        notify_price_drop(user, product, 100.0, 80.0)

        mock_push.assert_not_called()
        mock_email.assert_called_once()

    @patch("app.services.notifier.send_email_notification")
    @patch("app.services.notifier.send_push_notification")
    def test_skips_push_when_no_subscription(self, mock_push, mock_email):
        user = MagicMock()
        user.notify_push = True
        user.push_subscription = None
        user.notify_email = True
        user.email = "user@example.com"

        product = MagicMock()
        product.name = "Product"
        product.url = "https://example.com"

        notify_price_drop(user, product, 100.0, 80.0)

        mock_push.assert_not_called()
        mock_email.assert_called_once()

    @patch("app.services.notifier.send_email_notification")
    @patch("app.services.notifier.send_push_notification")
    def test_skips_email_when_disabled(self, mock_push, mock_email):
        user = MagicMock()
        user.notify_push = True
        user.push_subscription = {"endpoint": "https://push.example.com"}
        user.notify_email = False
        user.email = "user@example.com"

        product = MagicMock()
        product.name = "Product"
        product.url = "https://example.com"

        notify_price_drop(user, product, 100.0, 80.0)

        mock_push.assert_called_once()
        mock_email.assert_not_called()
