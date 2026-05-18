import logging
from app.config import get_settings

logger = logging.getLogger(__name__)


async def send_order_confirmation(order_id: str, email: str | None = None) -> None:
    s = get_settings()
    subject = f"Order confirmed — {order_id[:8]}"
    body = f"Your beauty store order {order_id} has been confirmed. Thank you for shopping!"
    if s.smtp_host and email:
        try:
            import aiosmtplib
            from email.message import EmailMessage
            msg = EmailMessage()
            msg["From"] = s.email_from
            msg["To"] = email
            msg["Subject"] = subject
            msg.set_content(body)
            await aiosmtplib.send(
                msg,
                hostname=s.smtp_host,
                port=s.smtp_port,
                username=s.smtp_user or None,
                password=s.smtp_pass or None,
                start_tls=True,
            )
            logger.info("Email sent to %s for order %s", email, order_id)
        except Exception as e:
            logger.error("Failed to send email: %s", e)
            raise
    else:
        logger.info("[DEV EMAIL] To=%s Subject=%s Body=%s", email or "n/a", subject, body)
