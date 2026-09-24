from fastapi import APIRouter

from app.api.v1.endpoints import auth, health, personas, research

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(research.router)
api_router.include_router(personas.router)
