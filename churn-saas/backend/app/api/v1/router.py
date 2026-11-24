from fastapi import APIRouter

from app.api.v1.endpoints import (
    actions,
    auth,
    customers,
    imports,
    ingest,
    risk_settings,
    settings,
    team,
)

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(imports.router)
api_router.include_router(ingest.router)
api_router.include_router(risk_settings.router)
api_router.include_router(settings.router)
api_router.include_router(customers.router)
api_router.include_router(actions.router)
api_router.include_router(team.router)