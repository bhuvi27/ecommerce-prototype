from shared.app_factory import create_base_app
from app.shared.health.router import router as health_router
from shared.config import get_service_settings
from app.modules.catalog.router import router as catalog_router
from app.modules.admin.router import router as admin_router
from catalog.internal_routes import router as catalog_internal_router

settings = get_service_settings()
app = create_base_app(title=f"{settings.app_name} — Catalog")
prefix = f"/{settings.api_prefix}"

app.include_router(catalog_router, prefix=prefix)
app.include_router(catalog_internal_router, prefix=prefix)
app.include_router(admin_router, prefix=prefix)
app.include_router(health_router)
