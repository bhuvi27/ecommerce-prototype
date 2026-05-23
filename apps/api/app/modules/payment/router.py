from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.db.session import get_db
from app.shared.deps import get_current_user
from app.shared.db.models import User
from app.modules.payment import service as payment_service
from app.modules.payment.schemas import PaymentVerifyRequest, PaymentVerifyResponse

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/verify", response_model=PaymentVerifyResponse)
async def verify_payment(
    body: PaymentVerifyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    try:
        order = await payment_service.verify_checkout_payment(
            db,
            body.razorpay_order_id,
            body.razorpay_payment_id,
            body.razorpay_signature,
        )
    except payment_service.PaymentVerifyError as e:
        raise HTTPException(400, str(e)) from e
    if order.user_id and order.user_id != user.id:
        raise HTTPException(403, "Forbidden")
    return PaymentVerifyResponse(order_id=str(order.id), status=order.status.value)


@router.post("/webhook")
async def razorpay_webhook(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    x_razorpay_signature: Annotated[str | None, Header()] = None,
):
    body = await request.body()
    if x_razorpay_signature and not payment_service.verify_webhook_signature(body, x_razorpay_signature):
        raise HTTPException(400, "Invalid signature")
    import json
    payload = json.loads(body)
    event = payload.get("event")
    if event == "payment.captured":
        await payment_service.handle_payment_captured(db, payload)
    return {"status": "ok"}
