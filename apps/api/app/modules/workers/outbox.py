import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from app.shared.db.session import async_session_factory
from app.shared.db.models import OutboxEvent, Order, User
from app.modules.notification.service import send_order_confirmation

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 5


async def process_outbox_batch() -> None:
    async with async_session_factory() as db:
        result = await db.execute(
            select(OutboxEvent)
            .where(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at)
            .limit(20)
        )
        events = result.scalars().all()
        for event in events:
            try:
                if event.event_type == "order.confirmed":
                    order_id = event.payload.get("order_id")
                    email = None
                    user_id = event.payload.get("user_id")
                    if user_id:
                        user_result = await db.execute(select(User).where(User.id == UUID(user_id)))
                        user = user_result.scalar_one_or_none()
                        email = user.email if user else None
                    else:
                        order_result = await db.execute(select(Order).where(Order.id == UUID(order_id)))
                        order = order_result.scalar_one_or_none()
                        if order and order.user_id:
                            user_result = await db.execute(select(User).where(User.id == order.user_id))
                            user = user_result.scalar_one_or_none()
                            email = user.email if user else None
                    await send_order_confirmation(order_id, email)
                event.status = "processed"
                event.processed_at = datetime.now(timezone.utc)
            except Exception as e:
                event.attempts += 1
                event.last_error = str(e)
                if event.attempts >= MAX_ATTEMPTS:
                    event.status = "dlq"
                logger.exception("Outbox event failed: %s", event.id)
        await db.commit()
