import logging
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.config import get_settings
from app.shared.health.router import router as health_router
from app.modules.auth.router import router as auth_router
from app.modules.catalog.router import router as catalog_router
from app.modules.admin.router import router as admin_router
from app.modules.cart.router import router as cart_router
from app.modules.order.router import router as order_router
from app.modules.payment.router import router as payment_router
from app.modules.workers.outbox import process_outbox_batch
from app.modules.workers.reconciliation import expire_stale_orders, reconcile_payments

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(process_outbox_batch, "interval", seconds=5, id="outbox")
    scheduler.add_job(expire_stale_orders, "interval", minutes=60, id="expire")
    scheduler.add_job(reconcile_payments, "interval", minutes=15, id="reconcile")
    scheduler.start()
    logger.info("Background workers started")
    yield
    scheduler.shutdown()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response

    prefix = f"/{settings.api_prefix}"
    app.include_router(health_router)
    app.include_router(auth_router, prefix=prefix)
    app.include_router(catalog_router, prefix=prefix)
    app.include_router(admin_router, prefix=prefix)
    app.include_router(cart_router, prefix=prefix)
    app.include_router(order_router, prefix=prefix)
    app.include_router(payment_router, prefix=prefix)

    return app


app = create_app()
