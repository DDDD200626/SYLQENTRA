from fastapi import APIRouter

from app.api.v1.routes import agents, ai, auth, dashboard, health, orchestrations, organizations, tasks

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(dashboard.router)
api_router.include_router(tasks.router)
api_router.include_router(agents.router)
api_router.include_router(ai.router)
api_router.include_router(orchestrations.router)
