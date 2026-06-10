import logging
from typing import Any

import httpx

from shared.config import get_service_settings

logger = logging.getLogger(__name__)


def _base(service_url: str) -> str:
    return service_url.rstrip("/")


async def fetch_product(product_id: str) -> dict[str, Any] | None:
    settings = get_service_settings()
    if not settings.catalog_service_url:
        return None
    url = f"{_base(settings.catalog_service_url)}/api/v1/catalog/products/id/{product_id}"
    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.get(url)
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()


async def fetch_cart(
    *,
    authorization: str | None = None,
    cart_id: str | None = None,
    extra_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    settings = get_service_settings()
    if not settings.cart_service_url:
        raise RuntimeError("CART_SERVICE_URL is not configured")
    url = f"{_base(settings.cart_service_url)}/api/v1/cart"
    headers: dict[str, str] = dict(extra_headers or {})
    if authorization:
        headers["Authorization"] = authorization
    cookies = {"cart_id": cart_id} if cart_id else None
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url, headers=headers, cookies=cookies)
        r.raise_for_status()
        return r.json()


async def initiate_payment(
    *,
    authorization: str,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    razorpay_signature: str,
) -> dict[str, Any]:
    settings = get_service_settings()
    if not settings.payment_service_url:
        raise RuntimeError("PAYMENT_SERVICE_URL is not configured")
    url = f"{_base(settings.payment_service_url)}/api/v1/payments/verify"
    body = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature,
    }
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(url, json=body, headers={"Authorization": authorization})
        r.raise_for_status()
        return r.json()
