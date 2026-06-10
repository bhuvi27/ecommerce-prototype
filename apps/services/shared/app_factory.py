import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from shared.config import apply_monolith_env, get_service_settings


def create_base_app(
    title: str | None = None,
    lifespan: Callable[[FastAPI], AsyncIterator[Any]] | None = None,
) -> FastAPI:
    apply_monolith_env()
    settings = get_service_settings()
    app = FastAPI(title=title or settings.app_name, debug=settings.debug, lifespan=lifespan)

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

    return app
