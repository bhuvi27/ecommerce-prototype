from contextlib import asynccontextmanager
from app.shared.health.router import router as health_router

from shared.app_factory import create_base_app
from shared.config import get_service_settings
from payment.kafka_bridge import get_kafka_producer, install_payment_kafka_hooks
from app.modules.payment.router import router as payment_router


@asynccontextmanager
async def lifespan(app):
    install_payment_kafka_hooks()
    await get_kafka_producer()
    yield


settings = get_service_settings()
app = create_base_app(title=f"{settings.app_name} — Payment", lifespan=lifespan)
prefix = f"/{settings.api_prefix}"

app.include_router(payment_router, prefix=prefix)
app.include_router(health_router)
