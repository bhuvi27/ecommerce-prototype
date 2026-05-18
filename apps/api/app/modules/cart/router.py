import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from app.shared.db.models import User
from app.shared.db.session import get_db
from app.shared.deps import get_current_user_optional, get_guest_id
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.cart import service
from app.modules.cart.schemas import CartItemInput, CartResponse

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("", response_model=CartResponse)
async def get_cart(
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
):
    guest_id = get_guest_id(request)
    cart = await service.get_cart_response(db, user, guest_id)
    if not user and not request.cookies.get("cart_id"):
        response.set_cookie("cart_id", cart.cart_id, max_age=30 * 86400, samesite="lax")
    return cart


@router.post("/items", response_model=CartResponse)
async def add_item(
    body: CartItemInput,
    request: Request,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
):
    guest_id = get_guest_id(request) or request.cookies.get("cart_id")
    try:
        cart = await service.upsert_item(db, user, guest_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    if not user:
        response.set_cookie("cart_id", cart.cart_id, max_age=30 * 86400, samesite="lax")
    return cart


@router.delete("/items/{product_id}/{sku_id}", response_model=CartResponse)
async def remove_item(
    product_id: str,
    sku_id: str,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User | None, Depends(get_current_user_optional)],
):
    guest_id = get_guest_id(request) or request.cookies.get("cart_id")
    return await service.remove_item(db, user, guest_id, product_id, sku_id)
