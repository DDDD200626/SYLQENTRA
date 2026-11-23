from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.redis import check_redis
from app.database.session import get_db
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> JSONResponse:
    try:
        db.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "error"
    payload = HealthResponse(
        status="ok" if database == "ok" else "degraded",
        service=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        database=database,
        redis=check_redis(),
    )
    return JSONResponse(status_code=200 if database == "ok" else 503, content=payload.model_dump())
