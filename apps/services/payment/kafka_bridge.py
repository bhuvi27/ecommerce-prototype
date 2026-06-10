import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from shared.kafka import TOPIC_ORDER_CONFIRMED, TOPIC_PAYMENT_COMPLETED, TOPIC_PAYMENT_FAILED, create_producer, publish_event

logger = logging.getLogger(__name__)
_producer = None


async def get_kafka_producer():
    global _producer
    if _producer is None:
        _producer = await create_producer()
    return _producer


async def publish_payment_completed(order_id: str, payment_id: str | None = None) -> None:
    producer = await get_kafka_producer()
    await publish_event(
        producer,
        TOPIC_PAYMENT_COMPLETED,
        {"order_id": order_id, "payment_id": payment_id},
        key=order_id,
    )


async def publish_payment_failed(order_id: str, reason: str) -> None:
    producer = await get_kafka_producer()
    await publish_event(
        producer,
        TOPIC_PAYMENT_FAILED,
        {"order_id": order_id, "reason": reason},
        key=order_id,
    )


async def publish_order_confirmed(order_id: str) -> None:
    producer = await get_kafka_producer()
    await publish_event(producer, TOPIC_ORDER_CONFIRMED, {"order_id": order_id}, key=order_id)


def install_payment_kafka_hooks() -> None:
    from app.modules.payment import service as payment_service

    if getattr(payment_service, "_kafka_hooks_installed", False):
        return

    original_captured = payment_service.handle_payment_captured
    original_mock = payment_service.mock_capture_payment

    async def handle_payment_captured(db: AsyncSession, payload: dict) -> None:
        await original_captured(db, payload)
        order_id = _order_id_from_webhook(payload)
        if order_id:
            await publish_payment_completed(order_id)

    async def mock_capture_payment(db: AsyncSession, order_id) -> None:
        await original_mock(db, order_id)
        await publish_payment_completed(str(order_id))
        await publish_order_confirmed(str(order_id))

    payment_service.handle_payment_captured = handle_payment_captured
    payment_service.mock_capture_payment = mock_capture_payment
    payment_service._kafka_hooks_installed = True
    logger.info("Payment service Kafka hooks installed")


def _order_id_from_webhook(payload: dict[str, Any]) -> str | None:
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    notes = entity.get("notes") or {}
    if oid := notes.get("order_id"):
        return str(oid)
    receipt = entity.get("receipt")
    return str(receipt) if receipt else None
