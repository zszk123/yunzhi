"""FastAPI 入口：uvicorn app.main:app"""

import structlog
from fastapi import FastAPI

from app.api.healthz import router as healthz_router
from app.core.logging import configure_logging
from app.core.settings import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(title="yunzhi-backend", version="0.1.0")
    app.include_router(healthz_router)

    structlog.get_logger().info(
        "server.started", app_env=settings.app_env, port=settings.backend_port
    )
    return app


app = create_app()
