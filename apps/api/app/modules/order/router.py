import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import get_settings
from app.shared.db.models import IdempotencyKey, Order, OrderItem, OrderStatus, Payment, PaymentStatus, User
from app.shared.db.session import get_db
from app.shared.deps import get_current_user, get_current_user_optional, get_guest_id
from app.modules.cart import service as cart_service
from app.modules.order.schemas import CheckoutRequest, CheckoutResponse, OrderItemResponse, OrderResponse
from app.modules.payment import service as payment_service

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_response(order: Order, rp_order_id: str | None = None) -> OrderResponse:
    s = get_settings()
    return OrderResponse(
        id=order.id,
        status=order.status.value,
        subtotal=order.subtotal,
        currency=order.currency,
        items=[
            OrderItemResponse(
                product_id=i.product_id,
                sku_id=i.sku_id,
                product_name=i.product_name,
                unit_price=i.unit_price,
                quantity=i.quantity,
                image_url=i.image_url,
            )
            for i in order.items
        ],
        razorpay_order_id=rp_order_id,
        razorpay_key_id=s.razorpay_key_id or None,
        created_at=order.created_at,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key header required")

    existing = await db.execute(select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key))
    if row := existing.scalar_one_or_none():
        body = row.response_body
        if isinstance(body.get("order"), dict):
            body["order"] = OrderResponse(**body["order"])
        return CheckoutResponse(**body)

    guest_id = get_guest_id(request) or request.cookies.get("cart_id")
    cart = await cart_service.get_cart_response(db, user, guest_id)
    if not cart.items:
        raise HTTPException(400, "Cart is empty")

    s = get_settings()
    order = Order(
        user_id=user.id if user else None,
        status=OrderStatus.pending,
        idempotency_key=idempotency_key,
        subtotal=cart.subtotal,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=s.order_expire_hours),
        **body.model_dump(),
    )
    db.add(order)
    await db.flush()

    for item in cart.items:
        db.add(OrderItem(
            order_id=order.id,
            product_id=item.product_id,
            sku_id=item.sku_id,
            product_name=item.product_name,
            unit_price=item.unit_price,
            quantity=item.quantity,
            image_url=item.image_url,
        ))

    payment = Payment(order_id=order.id, amount=cart.subtotal, currency="INR")
    db.add(payment)
    await db.flush()

    try:
        rp_order_id = await payment_service.create_razorpay_order(db, order, payment)
    except Exception as e:
        order.status = OrderStatus.payment_failed
        raise HTTPException(502, f"Payment initiation failed: {e}")

    await db.refresh(order, ["items"])
    resp = CheckoutResponse(
        order=_order_response(order, rp_order_id),
        razorpay_order_id=rp_order_id,
        razorpay_key_id=s.razorpay_key_id or "mock",
        amount=cart.subtotal,
        currency="INR",
    )
    db.add(IdempotencyKey(key=idempotency_key, user_id=user.id if user else None, response_body=resp.model_dump(mode="json")))
    await db.flush()
    return resp


@router.get("", response_model=list[OrderResponse])
async def my_orders(user: Annotated[User, Depends(get_current_user)], db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.user_id == user.id).order_by(Order.created_at.desc())
    )
    return [_order_response(o) for o in result.scalars().all()]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(order_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)], user: Annotated[User | None, Depends(get_current_user_optional)]):
    result = await db.execute(select(Order).options(selectinload(Order.items)).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(404, "Order not found")
    if user and order.user_id and order.user_id != user.id:
        raise HTTPException(403, "Forbidden")
    payment_result = await db.execute(select(Payment).where(Payment.order_id == order_id))
    payment = payment_result.scalar_one_or_none()
    return _order_response(order, payment.razorpay_order_id if payment else None)


@router.post("/{order_id}/mock-pay")
async def mock_pay(order_id: uuid.UUID, db: Annotated[AsyncSession, Depends(get_db)]):
    """Dev only: confirm order without Razorpay when keys not set."""
    s = get_settings()
    if s.razorpay_key_id:
        raise HTTPException(403, "Only available without Razorpay keys")
    await payment_service.mock_capture_payment(db, order_id)
    result = await db.execute(select(Order).options(selectinload(Order.items)).where(Order.id == order_id))
    order = result.scalar_one()
    return _order_response(order)
