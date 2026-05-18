from typing import Annotated
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.db.session import get_db
from app.modules.payment import service as payment_service

router = APIRouter(prefix="/payments", tags=["payments"])


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
