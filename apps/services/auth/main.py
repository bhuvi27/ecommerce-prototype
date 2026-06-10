from shared.app_factory import create_base_app
from shared.config import get_service_settings
from app.shared.health.router import router as health_router
from app.modules.auth.router import router as auth_router

settings = get_service_settings()
app = create_base_app(title=f"{settings.app_name} — Auth")
prefix = f"/{settings.api_prefix}"

app.include_router(health_router)
app.include_router(auth_router, prefix=prefix)
