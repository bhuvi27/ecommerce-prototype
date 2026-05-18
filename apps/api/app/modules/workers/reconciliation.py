import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.shared.db.session import async_session_factory
from app.shared.db.models import Order, OrderStatus, Payment, PaymentStatus
from app.config import get_settings

logger = logging.getLogger(__name__)


async def expire_stale_orders() -> None:
    async with async_session_factory() as db:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=get_settings().order_expire_hours)
        result = await db.execute(
            select(Order).where(Order.status == OrderStatus.pending, Order.created_at < cutoff)
        )
        for order in result.scalars().all():
            order.status = OrderStatus.expired
        await db.commit()
        logger.info("Expired stale pending orders")


async def reconcile_payments() -> None:
    """Placeholder for Razorpay API polling when webhooks missed."""
    s = get_settings()
    if not s.razorpay_key_id:
        return
    async with async_session_factory() as db:
        result = await db.execute(
            select(Payment).where(Payment.status == PaymentStatus.pending)
        )
        pending = result.scalars().all()
        if pending:
            logger.info("Reconciliation: %d pending payments (configure Razorpay fetch in prod)", len(pending))
        await db.commit()
