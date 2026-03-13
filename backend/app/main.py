from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.chat import router as chat_router
from app.api.escalation import router as escalation_router
from app.api.health import router as health_router
from app.api.marketing import router as marketing_router
from app.api.review import router as review_router
from app.api.sales import router as sales_router
from app.api.support import router as support_router
from app.config import configure_openai, get_settings
from app.database import init_db


def configure_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(level=level)
        return
    root_logger.setLevel(level)

def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.log_level)
    configure_openai(settings)

    app = FastAPI(title=settings.app_name)
    init_db()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if settings.trusted_host_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_host_list)

    app.include_router(health_router)
    app.include_router(chat_router)
    app.include_router(support_router)
    app.include_router(escalation_router)
    app.include_router(sales_router)
    app.include_router(marketing_router)
    app.include_router(review_router)
    return app


app = create_app()
