import logging

from app.modules.catalog.schemas import ProductResponse
from shared.config import get_service_settings
from shared.http_clients import fetch_product

logger = logging.getLogger(__name__)


def apply_catalog_http_patch() -> None:
    settings = get_service_settings()
    if not settings.catalog_service_url:
        return

    from app.modules.catalog import service as catalog_service

    original = catalog_service.get_product_by_id

    async def get_product_by_id_http(product_id: str) -> ProductResponse | None:
        data = await fetch_product(product_id)
        if data:
            return ProductResponse(**data)
        return await original(product_id)

    catalog_service.get_product_by_id = get_product_by_id_http
    logger.info("Cart service using catalog HTTP at %s", settings.catalog_service_url)
