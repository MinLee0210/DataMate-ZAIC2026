from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import settings
from src.modules.health_module import HealthModule
from src.routes import api_router
from src.utils import get_logger

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # the API serves debugging and the demo UI (app/); the competition runs `python -m src`
    app.state.health = HealthModule()
    app.state.qa = None  # built on the first /ask, so /health works without data or an LLM
    try:
        yield
    finally:
        if app.state.qa is not None:
            app.state.qa.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.include_router(api_router)
    return app


app = create_app()
