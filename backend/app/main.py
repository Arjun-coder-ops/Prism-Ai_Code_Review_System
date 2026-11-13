from fastapi import FastAPI

from app.api.github_webhooks import router as github_webhooks_router
from app.api.reviews import router as reviews_router
from app.api.system import router as system_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    """Create the PRISM API without connecting to infrastructure at import time."""
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version)
    app.include_router(system_router)
    app.include_router(reviews_router)
    app.include_router(github_webhooks_router)
    return app


app = create_app()
