import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import get_settings
from app.shared.db.models import Address, IdempotencyKey, Order, OrderItem, OrderStatus, Payment, PaymentStatus, User
from app.shared.db.session import get_db
from app.shared.deps import get_current_user, get_current_user_optional, get_guest_id
from app.modules.cart import service as cart_service
from app.modules.order.schemas import CheckoutRequest, CheckoutResponse, OrderItemResponse, OrderResponse
from app.modules.payment import service as payment_service

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_response(
    order: Order,
    rp_order_id: str | None = None,
    payment_method: str | None = None,
) -> OrderResponse:
    s = get_settings()
    return OrderResponse(
        id=order.id,
        status=order.status.value,
        subtotal=order.subtotal,
        currency=order.currency,
        payment_method=payment_method,
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


def _shipping_from_body(body: CheckoutRequest, user: User, addr: Address | None) -> dict:
    if addr:
        return {
            "shipping_name": user.name or user.email.split("@")[0],
            "shipping_phone": addr.phone,
            "shipping_line1": addr.line1,
            "shipping_line2": addr.line2,
            "shipping_city": addr.city,
            "shipping_state": addr.state,
            "shipping_pincode": addr.pincode,
        }
    return {
        "shipping_name": body.shipping_name,
        "shipping_phone": body.shipping_phone,
        "shipping_line1": body.shipping_line1,
        "shipping_line2": body.shipping_line2,
        "shipping_city": body.shipping_city,
        "shipping_state": body.shipping_state,
        "shipping_pincode": body.shipping_pincode,
    }


@router.post("/checkout", response_model=CheckoutResponse)
async def checkout(
    body: CheckoutRequest,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
):
    if not idempotency_key:
        raise HTTPException(400, "Idempotency-Key header required")

    existing = await db.execute(select(IdempotencyKey).where(IdempotencyKey.key == idempotency_key))
    if row := existing.scalar_one_or_none():
        cached = row.response_body
        if isinstance(cached.get("order"), dict):
            cached["order"] = OrderResponse(**cached["order"])
        return CheckoutResponse(**cached)

    addr: Address | None = None
    if body.address_id:
        addr_result = await db.execute(
            select(Address).where(Address.id == body.address_id, Address.user_id == user.id)
        )
        addr = addr_result.scalar_one_or_none()
        if not addr:
            raise HTTPException(404, "Address not found")

    guest_id = get_guest_id(request) or request.cookies.get("cart_id")
    cart = await cart_service.get_cart_response(db, user, guest_id)
    if not cart.items:
        raise HTTPException(400, "Cart is empty")

    shipping = _shipping_from_body(body, user, addr)

    if body.save_address and not body.address_id:
        addr_count = await db.execute(select(Address).where(Address.user_id == user.id))
        is_first = addr_count.scalars().first() is None
        db.add(Address(
            user_id=user.id,
            label=body.address_label or "Home",
            line1=shipping["shipping_line1"],
            line2=shipping["shipping_line2"],
            city=shipping["shipping_city"],
            state=shipping["shipping_state"],
            pincode=shipping["shipping_pincode"],
            phone=shipping["shipping_phone"],
            is_default=is_first,
        ))

    s = get_settings()
    order = Order(
        user_id=user.id,
        status=OrderStatus.pending,
        idempotency_key=idempotency_key,
        subtotal=cart.subtotal,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=s.order_expire_hours),
        **shipping,
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

    method = body.payment_method
    rp_order_id: str | None = None
    rp_key: str | None = None

    if method == "cod":
        if not s.enable_cod:
            raise HTTPException(400, "Cash on delivery is not available")
        order = await payment_service.confirm_cod_order(db, order.id)
    else:
        try:
            rp_order_id = await payment_service.create_razorpay_order(db, order, payment)
            rp_key = s.razorpay_key_id or "mock"
        except Exception as e:
            order.status = OrderStatus.payment_failed
            raise HTTPException(502, f"Payment initiation failed: {e}") from e

    await db.refresh(order, ["items"])
    resp = CheckoutResponse(
        order=_order_response(order, rp_order_id, method),
        payment_method=method,
        razorpay_order_id=rp_order_id,
        razorpay_key_id=rp_key,
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
    method = None
    if payment and payment.razorpay_payment_id and payment.razorpay_payment_id.startswith("cod_"):
        method = "cod"
    elif payment and payment.razorpay_order_id:
        method = "online"
    return _order_response(order, payment.razorpay_order_id if payment else None, method)


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
