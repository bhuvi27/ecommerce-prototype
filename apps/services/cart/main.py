from shared.app_factory import create_base_app
from app.shared.health.router import router as health_router
from shared.config import get_service_settings
from cart.catalog_patch import apply_catalog_http_patch
from app.modules.cart.router import router as cart_router

apply_catalog_http_patch()

settings = get_service_settings()
app = create_base_app(title=f"{settings.app_name} — Cart")
prefix = f"/{settings.api_prefix}"

app.include_router(cart_router, prefix=prefix)
app.include_router(health_router)
