from fastapi import APIRouter

from app.api.v1.routes import (
    agents,
    approvals,
    ai,
    auth,
    dashboard,
    health,
    integrations,
    knowledge,
    metrics,
    orchestrations,
    organizations,
    plans,
    tasks,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(organizations.router)
api_router.include_router(plans.router)
api_router.include_router(dashboard.router)
api_router.include_router(tasks.router)
api_router.include_router(agents.router)
api_router.include_router(approvals.router)
api_router.include_router(ai.router)
api_router.include_router(orchestrations.router)
api_router.include_router(workflows.router)
api_router.include_router(integrations.router)
api_router.include_router(knowledge.router)
api_router.include_router(metrics.router)
