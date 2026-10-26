from fastapi import APIRouter

from src.routes import ask, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(ask.router, tags=["ask"])
