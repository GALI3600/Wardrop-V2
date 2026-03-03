import json
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from pywebpush import webpush, WebPushException

from app.config import settings

logger = logging.getLogger(__name__)


def send_push_notification(subscription_info: dict, title: str, body: str, url: str = ""):
    """Send a Web Push notification to a user."""
    if not settings.vapid_private_key:
        logger.debug("Push notification skipped — no VAPID key configured")
        return

    payload = json.dumps({
        "title": title,
        "body": body,
        "url": url,
    })

    try:
        webpush(
            subscription_info=subscription_info,
            data=payload,
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={
                "sub": f"mailto:{settings.vapid_email}",
            },
        )
    except WebPushException as e:
        logger.error("Push notification failed: %s", e)


def send_email_notification(to_email: str, subject: str, body_html: str):
    """Send an email notification to a user."""
    if not settings.smtp_host:
        logger.debug("Email notification skipped — no SMTP host configured")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from
    msg["To"] = to_email
    msg.attach(MIMEText(body_html, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_from, to_email, msg.as_string())
    except Exception as e:
        logger.error("Email notification failed: %s", e)


def notify_price_drop(user, product, old_price, new_price):
    """Send price drop notifications via push and/or email."""
    logger.info(
        "Notifying user %s about price drop: %s R$%.2f → R$%.2f",
        user.email, product.name, old_price, new_price,
    )
    title = "Queda de preço!"
    body = f"{product.name}: de R${old_price:.2f} para R${new_price:.2f}"
    url = product.url

    if user.notify_push and user.push_subscription:
        send_push_notification(user.push_subscription, title, body, url)

    if user.notify_email and user.email:
        html = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h2 style="color: #6366f1;">Queda de preço!</h2>
            <p><strong>{product.name}</strong></p>
            <p>De <s>R$ {old_price:.2f}</s> para
               <span style="color: #16a34a; font-size: 24px; font-weight: bold;">
                   R$ {new_price:.2f}
               </span>
            </p>
            <p><a href="{url}" style="color: #6366f1;">Ver produto</a></p>
        </div>
        """
        send_email_notification(user.email, f"Wardrop: {product.name} caiu para R${new_price:.2f}", html)
