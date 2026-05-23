import uuid
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.config import get_settings
from app.shared.db.models import Cart, CartItem, User
from app.shared.redis.client import redis_get, redis_set, redis_delete
from app.modules.catalog import service as catalog_service
from app.modules.cart.schemas import CartItemInput, CartItemResponse, CartResponse

CART_PREFIX = "cart:"


def _cart_response(cart_id: str, items: list[CartItemResponse]) -> CartResponse:
    subtotal = sum(i.line_total for i in items)
    return CartResponse(cart_id=cart_id, items=items, subtotal=subtotal, item_count=sum(i.quantity for i in items))


def _items_from_db(items: list[CartItem]) -> list[CartItemResponse]:
    return [
        CartItemResponse(
            product_id=i.product_id,
            sku_id=i.sku_id,
            product_name=i.product_name,
            unit_price=i.unit_price,
            quantity=i.quantity,
            image_url=i.image_url,
            line_total=i.unit_price * i.quantity,
        )
        for i in items
    ]


async def get_or_create_cart(db: AsyncSession, user: User | None, guest_id: str | None) -> tuple[Cart, str]:
    if user:
        result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user.id))
        cart = result.scalar_one_or_none()
        if cart:
            return cart, str(cart.id)
        cart = Cart(user_id=user.id)
        db.add(cart)
        await db.flush()
        return cart, str(cart.id)

    if not guest_id:
        guest_id = str(uuid.uuid4())
    cache_key = f"{CART_PREFIX}{guest_id}"
    cached = await redis_get(cache_key)
    if cached:
        return None, guest_id  # type: ignore - guest uses redis only

    cart = Cart(guest_id=guest_id)
    db.add(cart)
    await db.flush()
    return cart, guest_id


async def get_cart_response(db: AsyncSession, user: User | None, guest_id: str | None) -> CartResponse:
    s = get_settings()
    ttl = s.cart_ttl_days * 86400

    if user:
        result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user.id))
        cart = result.scalar_one_or_none()
        if not cart:
            return _cart_response(str(uuid.uuid4()), [])
        return _cart_response(str(cart.id), _items_from_db(cart.items))

    gid = guest_id or str(uuid.uuid4())
    cache_key = f"{CART_PREFIX}{gid}"
    cached = await redis_get(cache_key)
    if cached:
        items = [CartItemResponse(**i) for i in cached.get("items", [])]
        return _cart_response(gid, items)

    result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.guest_id == gid))
    cart = result.scalar_one_or_none()
    if cart:
        items = _items_from_db(cart.items)
        await redis_set(cache_key, {"items": [i.model_dump() for i in items]}, ttl)
        return _cart_response(gid, items)
    return _cart_response(gid, [])


async def upsert_item(db: AsyncSession, user: User | None, guest_id: str | None, body: CartItemInput) -> CartResponse:
    product = await catalog_service.get_product_by_id(body.product_id)
    if not product:
        raise ValueError("Product not found")
    sku = next((s for s in product.skus if s.id == body.sku_id), None)
    if not sku:
        raise ValueError("SKU not found")

    item_data = CartItemResponse(
        product_id=body.product_id,
        sku_id=body.sku_id,
        product_name=product.name,
        unit_price=sku.price,
        quantity=body.quantity,
        image_url=product.image_url,
        line_total=sku.price * body.quantity,
    )

    if user:
        result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user.id))
        cart = result.scalar_one_or_none()
        if not cart:
            cart = Cart(user_id=user.id)
            db.add(cart)
            await db.flush()
            existing = None
        else:
            existing = next((i for i in cart.items if i.product_id == body.product_id and i.sku_id == body.sku_id), None)
        if existing:
            existing.quantity = body.quantity
            existing.unit_price = sku.price
            existing.product_name = product.name
            existing.image_url = product.image_url
        else:
            db.add(CartItem(
                cart_id=cart.id,
                product_id=body.product_id,
                sku_id=body.sku_id,
                product_name=product.name,
                unit_price=sku.price,
                quantity=body.quantity,
                image_url=product.image_url,
            ))
        await db.flush()
        result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.id == cart.id))
        cart = result.scalar_one()
        return _cart_response(str(cart.id), _items_from_db(cart.items))

    gid = guest_id or str(uuid.uuid4())
    resp = await get_cart_response(db, None, gid)
    items = {f"{i.product_id}:{i.sku_id}": i for i in resp.items}
    items[f"{body.product_id}:{body.sku_id}"] = item_data
    new_items = list(items.values())
    await redis_set(f"{CART_PREFIX}{gid}", {"items": [i.model_dump() for i in new_items]}, get_settings().cart_ttl_days * 86400)
    return _cart_response(gid, new_items)


async def remove_item(db: AsyncSession, user: User | None, guest_id: str | None, product_id: str, sku_id: str) -> CartResponse:
    if user:
        result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user.id))
        cart = result.scalar_one_or_none()
        if cart:
            await db.execute(
                delete(CartItem).where(
                    CartItem.cart_id == cart.id,
                    CartItem.product_id == product_id,
                    CartItem.sku_id == sku_id,
                )
            )
            await db.flush()
            await db.refresh(cart, ["items"])
            return _cart_response(str(cart.id), _items_from_db(cart.items))
        return _cart_response(str(uuid.uuid4()), [])

    gid = guest_id or ""
    resp = await get_cart_response(db, None, gid)
    new_items = [i for i in resp.items if not (i.product_id == product_id and i.sku_id == sku_id)]
    await redis_set(f"{CART_PREFIX}{gid}", {"items": [i.model_dump() for i in new_items]}, get_settings().cart_ttl_days * 86400)
    return _cart_response(gid, new_items)


async def clear_cart(db: AsyncSession, user: User, guest_id: str | None = None) -> CartResponse:
    """Empty cart after successful checkout (Flipkart-style)."""
    result = await db.execute(select(Cart).options(selectinload(Cart.items)).where(Cart.user_id == user.id))
    cart = result.scalar_one_or_none()
    if cart and cart.items:
        await db.execute(delete(CartItem).where(CartItem.cart_id == cart.id))
        await db.flush()
        await db.refresh(cart, ["items"])
    if guest_id:
        await redis_delete(f"{CART_PREFIX}{guest_id}")
    return await get_cart_response(db, user, guest_id)
