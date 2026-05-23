import hashlib
import hmac
import json
from datetime import datetime, timezone
from uuid import UUID
import razorpay
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import get_settings
from app.shared.db.models import Order, OrderStatus, OutboxEvent, Payment, PaymentStatus
from app.shared.resilience.circuit import razorpay_circuit


def _client():
    s = get_settings()
    return razorpay.Client(auth=(s.razorpay_key_id, s.razorpay_key_secret))


async def create_razorpay_order(db: AsyncSession, order: Order, payment: Payment) -> str:
    s = get_settings()
    if not s.razorpay_key_id or not s.razorpay_key_secret:
        # Dev mock when keys not set
        mock_id = f"order_mock_{order.id.hex[:12]}"
        payment.razorpay_order_id = mock_id
        payment.status = PaymentStatus.pending
        await db.flush()
        return mock_id

    if not razorpay_circuit.allow():
        raise RuntimeError("Payment service temporarily unavailable")

    try:
        rp_order = _client().order.create({
            "amount": payment.amount,
            "currency": payment.currency,
            "receipt": str(order.id),
            "payment_capture": 1,
        })
        razorpay_circuit.record_success()
        payment.razorpay_order_id = rp_order["id"]
        payment.status = PaymentStatus.pending
        await db.flush()
        return rp_order["id"]
    except Exception:
        razorpay_circuit.record_failure()
        raise


def verify_webhook_signature(body: bytes, signature: str) -> bool:
    s = get_settings()
    if not s.razorpay_webhook_secret:
        return True  # dev only
    expected = hmac.new(
        s.razorpay_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


async def handle_payment_captured(db: AsyncSession, payload: dict) -> None:
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rp_payment_id = entity.get("id")
    rp_order_id = entity.get("order_id")
    if not rp_order_id:
        return

    result = await db.execute(select(Payment).where(Payment.razorpay_order_id == rp_order_id))
    payment = result.scalar_one_or_none()
    if not payment:
        return
    if payment.razorpay_payment_id == rp_payment_id and payment.status == PaymentStatus.captured:
        return  # idempotent

    payment.razorpay_payment_id = rp_payment_id
    payment.status = PaymentStatus.captured
    payment.raw_webhook = payload

    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one()
    order.status = OrderStatus.confirmed

    outbox = OutboxEvent(
        event_type="order.confirmed",
        payload={"order_id": str(order.id), "user_id": str(order.user_id) if order.user_id else None},
    )
    db.add(outbox)
    await db.flush()


class PaymentVerifyError(Exception):
    pass


async def verify_checkout_payment(
    db: AsyncSession,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> Order:
    s = get_settings()
    if not s.razorpay_key_id or not s.razorpay_key_secret:
        raise PaymentVerifyError("Razorpay not configured")

    try:
        _client().utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        })
    except Exception as e:
        raise PaymentVerifyError("Invalid payment signature") from e

    result = await db.execute(select(Payment).where(Payment.razorpay_order_id == razorpay_order_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise PaymentVerifyError("Payment not found")

    if payment.razorpay_payment_id == razorpay_payment_id and payment.status == PaymentStatus.captured:
        order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
        return order_result.scalar_one()

    payment.razorpay_payment_id = razorpay_payment_id
    payment.status = PaymentStatus.captured
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalar_one()
    order.status = OrderStatus.confirmed
    db.add(OutboxEvent(
        event_type="order.confirmed",
        payload={"order_id": str(order.id), "user_id": str(order.user_id) if order.user_id else None},
    ))
    await db.flush()
    return order


async def confirm_cod_order(db: AsyncSession, order_id: UUID) -> Order:
    """Cash on delivery — confirm order without Razorpay (Flipkart-style COD)."""
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise PaymentVerifyError("Payment not found")
    payment.status = PaymentStatus.captured
    payment.razorpay_payment_id = f"cod_{order_id.hex[:16]}"
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one()
    order.status = OrderStatus.confirmed
    db.add(OutboxEvent(
        event_type="order.confirmed",
        payload={"order_id": str(order.id), "user_id": str(order.user_id), "payment_method": "cod"},
    ))
    await db.flush()
    return order


async def mock_capture_payment(db: AsyncSession, order_id: UUID) -> None:
    """Dev helper when Razorpay keys not configured."""
    result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    payment = result.scalar_one_or_none()
    if not payment:
        return
    payment.status = PaymentStatus.captured
    payment.razorpay_payment_id = f"pay_mock_{order_id.hex[:12]}"
    order_result = await db.execute(select(Order).where(Order.id == order_id))
    order = order_result.scalar_one()
    order.status = OrderStatus.confirmed
    db.add(OutboxEvent(event_type="order.confirmed", payload={"order_id": str(order.id)}))
    await db.flush()
