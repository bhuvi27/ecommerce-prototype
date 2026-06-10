"""HTTP-backed checkout for split cart/payment microservices."""
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.modules.cart import service as cart_service
from app.modules.cart.schemas import CartResponse
from app.modules.order.schemas import CheckoutRequest, CheckoutResponse
from app.modules.order.router import _order_response, _shipping_from_body
from app.modules.payment import service as payment_service
from app.shared.db.models import Address, IdempotencyKey, Order, OrderItem, OrderStatus, Payment, User
from app.shared.db.session import get_db
from app.shared.deps import get_current_user, get_guest_id
from shared.http_clients import fetch_cart
from shared.kafka import TOPIC_ORDER_CREATED, create_producer, publish_event

router = APIRouter(prefix="/orders", tags=["orders"])


async def _cart_from_http(request: Request, user: User) -> CartResponse:
    auth = request.headers.get("Authorization")
    guest_id = get_guest_id(request) or request.cookies.get("cart_id")
    data = await fetch_cart(authorization=auth, cart_id=guest_id)
    return CartResponse(**data)


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
        from app.modules.order.schemas import OrderResponse

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
    cart = await _cart_from_http(request, user)
    if not cart.items:
        raise HTTPException(400, "Cart is empty")

    shipping = _shipping_from_body(body, user, addr)

    if body.save_address and not body.address_id:
        addr_count = await db.execute(select(Address).where(Address.user_id == user.id))
        is_first = addr_count.scalars().first() is None
        db.add(
            Address(
                user_id=user.id,
                label=body.address_label or "Home",
                line1=shipping["shipping_line1"],
                line2=shipping["shipping_line2"],
                city=shipping["shipping_city"],
                state=shipping["shipping_state"],
                pincode=shipping["shipping_pincode"],
                phone=shipping["shipping_phone"],
                is_default=is_first,
            )
        )

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

    try:
        producer = await create_producer()
        await publish_event(
            producer,
            TOPIC_ORDER_CREATED,
            {"order_id": str(order.id), "user_id": str(user.id), "subtotal": cart.subtotal},
            key=str(order.id),
        )
        await producer.stop()
    except Exception:
        pass

    for item in cart.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                sku_id=item.sku_id,
                product_name=item.product_name,
                unit_price=item.unit_price,
                quantity=item.quantity,
                image_url=item.image_url,
            )
        )

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

    if order.status == OrderStatus.confirmed:
        await cart_service.clear_cart(db, user, guest_id)

    resp = CheckoutResponse(
        order=_order_response(order, rp_order_id, method),
        payment_method=method,
        razorpay_order_id=rp_order_id,
        razorpay_key_id=rp_key,
        amount=cart.subtotal,
        currency="INR",
    )
    db.add(IdempotencyKey(key=idempotency_key, user_id=user.id, response_body=resp.model_dump(mode="json")))
    await db.flush()
    return resp
