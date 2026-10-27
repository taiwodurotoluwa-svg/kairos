from pathlib import Path
from fastapi import APIRouter
from app.config import get_settings
from app.schemas import HealthResponse, ProviderHealth, SCHEMA_VERSION

router = APIRouter(tags=["health"])

@router.get("/health", response_model=HealthResponse)
def health_check() -> HealthResponse:
    settings = get_settings()
    
    groq_conf = bool(settings.groq_api_key.strip())
    hf_conf = bool(settings.hf_token.strip())
    ollama_conf = bool(settings.ollama_base_url.strip())
    
    providers = {
        "groq": ProviderHealth(configured=groq_conf, model_id=settings.groq_model if groq_conf else None),
        "huggingface": ProviderHealth(configured=hf_conf, model_id=settings.hf_model if hf_conf else None),
        "ollama": ProviderHealth(configured=ollama_conf, model_id=settings.ollama_model if ollama_conf else None),
    }
    
    fixtures_dir = Path(settings.fixtures_dir)
    loaded_presets = []
    if fixtures_dir.exists():
        for f in fixtures_dir.glob("*.json"):
            loaded_presets.append(f.stem)
            
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
