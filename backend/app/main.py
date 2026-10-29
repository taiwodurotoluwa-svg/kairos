from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analyze, demo, health
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
    allow_origin_regex=settings.cors_allow_origin_regex or None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
install_error_handlers(app)
app.include_router(health.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
app.include_router(analyze.router, prefix="/api/v1")


@app.get("/", tags=["root"])
def root_info() -> dict[str, str]:
    """Root service discovery endpoint for live deployment links."""
    return {
        "service": "Kairos Literature Synthesis & Contradiction Mapping API",
        "version": settings.app_version,
        "status": "online",
        "health_url": "/api/v1/health",
        "demo_presets_url": "/api/v1/demo",
        "docs_url": "/docs",
    }
