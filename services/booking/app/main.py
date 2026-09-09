from fastapi import FastAPI

from app.api.bookings import router as bookings_router
from app.api.health import router as health_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name)
    app.include_router(health_router)
    app.include_router(bookings_router)
    return app


app = create_app()
