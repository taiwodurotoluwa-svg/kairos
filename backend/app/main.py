from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import demo, health
from app.config import get_settings
from app.errors import install_error_handlers


@asynccontextmanager
async def lifespan(app: FastAPI):
    demo.warm_demo_cache()
    settings = get_settings()
    if settings.embedding_backend == "fastembed":
        try:
            from app.services.embeddings import get_embedder

            get_embedder(settings)
        except Exception:
            pass
    yield


settings = get_settings()
app = FastAPI(title="Kairos API", version=settings.app_version, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
install_error_handlers(app)
app.include_router(health.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
