from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

import app.models  # noqa: F401 — регистрирует все SQLAlchemy-модели
from app.api.router import api_router
from app.core.config import get_settings
from app.core.project_info import PROJECT_VERSION

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=PROJECT_VERSION,
    debug=settings.debug,
    default_response_class=ORJSONResponse,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
