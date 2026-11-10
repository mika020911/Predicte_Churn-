from fastapi import APIRouter

from app.api.v1.endpoints import auth, imports, risk_settings

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(imports.router)
api_router.include_router(risk_settings.router)