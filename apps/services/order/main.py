from shared.app_factory import create_base_app
from shared.config import get_service_settings
from app.shared.health.router import router as health_router
from app.modules.order.router import router as order_router

settings = get_service_settings()
app = create_base_app(title=f"{settings.app_name} — Order")
prefix = f"/{settings.api_prefix}"

if settings.cart_service_url or settings.payment_service_url:
    order_router.routes = [
        r
        for r in order_router.routes
        if not (
            hasattr(r, "methods")
            and r.methods
            and "POST" in r.methods
            and getattr(r, "path", "") == "/checkout"
        )
    ]
    from order.routes_micro import router as micro_checkout_router

    app.include_router(micro_checkout_router, prefix=prefix)

app.include_router(health_router)
app.include_router(order_router, prefix=prefix)
