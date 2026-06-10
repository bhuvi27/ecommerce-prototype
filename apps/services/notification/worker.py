import asyncio
import logging
import os

from shared.config import apply_monolith_env, get_service_settings
from shared.kafka import TOPIC_ORDER_CONFIRMED, TOPIC_PAYMENT_COMPLETED, consume_loop, create_consumer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def handle_event(topic: str, payload: dict) -> None:
    from app.modules.notification import service as notification_service

    order_id = payload.get("order_id")
    if not order_id:
        logger.warning("Missing order_id on topic=%s payload=%s", topic, payload)
        return

    if topic == TOPIC_ORDER_CONFIRMED:
        await notification_service.send_order_confirmation(str(order_id))
    elif topic == TOPIC_PAYMENT_COMPLETED:
        logger.info("Payment completed for order %s — sending confirmation", order_id)
        await notification_service.send_order_confirmation(str(order_id))


async def main() -> None:
    apply_monolith_env()
    settings = get_service_settings()
    logger.info("Notification worker starting (kafka=%s)", settings.kafka_bootstrap_servers)
    consumer = await create_consumer(
        TOPIC_ORDER_CONFIRMED,
        TOPIC_PAYMENT_COMPLETED,
        group_id=os.environ.get("KAFKA_CONSUMER_GROUP", "notification-worker"),
    )
    await consume_loop(consumer, handle_event)


if __name__ == "__main__":
    asyncio.run(main())
