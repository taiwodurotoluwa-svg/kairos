from fastapi import APIRouter
from app.config import get_settings
from app.schemas import HealthResponse, ProviderHealth, SCHEMA_VERSION
from app.api.demo import PRESETS, _resolve_fixture_path

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()

    provider_chain = [p.strip() for p in settings.llm_provider_chain.split(",") if p.strip()]

    groq_conf = "groq" in provider_chain and bool(settings.groq_api_key.strip())
    hf_conf = "huggingface" in provider_chain and bool(settings.hf_token.strip())
    ollama_conf = "ollama" in provider_chain and bool(settings.ollama_base_url.strip())

    providers = {
        "groq": ProviderHealth(configured=groq_conf, model_id=settings.groq_model if groq_conf else None),
        "huggingface": ProviderHealth(configured=hf_conf, model_id=settings.hf_model if hf_conf else None),
        "ollama": ProviderHealth(configured=ollama_conf, model_id=settings.ollama_model if ollama_conf else None),
    }

    # Canonical preset IDs resolved safely via _resolve_fixture_path
    loaded_presets = [pid for pid, (fn, *_) in PRESETS.items() if _resolve_fixture_path(fn).exists()]

    has_llm = groq_conf or hf_conf or ollama_conf
    status = "ok" if has_llm else "degraded"

    return HealthResponse(
        status=status,
        version=settings.app_version,
        schema_version=SCHEMA_VERSION,
        providers=providers,
        embedding_backend=settings.embedding_backend,
        presets_loaded=sorted(loaded_presets)
    )
