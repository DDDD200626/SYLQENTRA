from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging import logger, setup_logging
from app.database.base import Base
from app.database.seed import bootstrap_platform_admin, seed_reference_data
from app.database.session import SessionLocal, engine
import app.models  # noqa: F401


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    if settings.ENVIRONMENT == "production" and settings.JWT_SECRET == "change-me-in-env":
        raise RuntimeError("JWT_SECRET must be changed before production startup")
    if settings.JWT_SECRET == "change-me-in-env":
        logger.warning("JWT_SECRET is the development default. Set a private value in .env")
    if settings.AUTO_CREATE_TABLES:
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            seed_reference_data(db)
            bootstrap_platform_admin(db)
        finally:
            db.close()
    logger.info("%s API started", settings.APP_NAME)
    yield
    logger.info("%s API stopped", settings.APP_NAME)


app = FastAPI(title=settings.APP_NAME, version="0.4.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    response = await call_next(request)
    logger.info("%s %s %s", request.method, request.url.path, response.status_code)
    return response


@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(_request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"error": {"code": "INTERNAL_ERROR", "message": "Internal server error"}},
    )


app.include_router(api_router, prefix=settings.API_V1_PREFIX)
