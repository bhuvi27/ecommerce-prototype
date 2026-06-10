import json
import logging
from collections.abc import AsyncIterator, Callable
from typing import Any

from aiokafka import AIOKafkaConsumer, AIOKafkaProducer

from shared.config import get_service_settings

logger = logging.getLogger(__name__)

TOPIC_ORDER_CREATED = "order.created"
TOPIC_PAYMENT_COMPLETED = "payment.completed"
TOPIC_PAYMENT_FAILED = "payment.failed"
TOPIC_ORDER_CONFIRMED = "order.confirmed"
TOPIC_CATALOG_PRODUCT_UPDATED = "catalog.product.updated"

ALL_TOPICS = (
    TOPIC_ORDER_CREATED,
    TOPIC_PAYMENT_COMPLETED,
    TOPIC_PAYMENT_FAILED,
    TOPIC_ORDER_CONFIRMED,
    TOPIC_CATALOG_PRODUCT_UPDATED,
)


def _bootstrap() -> str:
    return get_service_settings().kafka_bootstrap_servers


async def create_producer() -> AIOKafkaProducer:
    producer = AIOKafkaProducer(bootstrap_servers=_bootstrap())
    await producer.start()
    return producer


async def publish_event(producer: AIOKafkaProducer, topic: str, payload: dict[str, Any], key: str | None = None) -> None:
    data = json.dumps(payload).encode("utf-8")
    k = key.encode("utf-8") if key else None
    await producer.send_and_wait(topic, data, key=k)
    logger.info("Published kafka topic=%s key=%s", topic, key)


async def create_consumer(*topics: str, group_id: str) -> AIOKafkaConsumer:
    consumer = AIOKafkaConsumer(
        *topics,
        bootstrap_servers=_bootstrap(),
        group_id=group_id,
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )
    await consumer.start()
    return consumer


async def consume_loop(
    consumer: AIOKafkaConsumer,
    handler: Callable[[str, dict[str, Any]], Any],
) -> None:
    try:
        async for msg in consumer:
            try:
                payload = json.loads(msg.value.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                logger.exception("Invalid kafka message on %s", msg.topic)
                continue
            try:
                await handler(msg.topic, payload)
            except Exception:
                logger.exception("Handler failed for topic=%s", msg.topic)
    finally:
        await consumer.stop()


async def consumer_messages(consumer: AIOKafkaConsumer) -> AsyncIterator[tuple[str, dict[str, Any]]]:
    async for msg in consumer:
        payload = json.loads(msg.value.decode("utf-8"))
        yield msg.topic, payload
