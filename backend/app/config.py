from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_version: str = "1.0.0"
    cors_allow_origins: str = "http://localhost:3000,http://localhost:5500,http://127.0.0.1:5500,http://localhost:5173"
    fixtures_dir: str = "../fixtures"

    min_papers: int = 2
    max_papers: int = 10
    max_file_mb: int = 20
    max_total_mb: int = 80
    max_paper_chars: int = 24000
    analyze_rate_limit_per_minute: int = 6
    job_ttl_minutes: int = 60
    job_timeout_seconds: int = 90
    arxiv_concurrency: int = 3

    llm_provider_chain: str = "groq,huggingface,ollama"
    groq_api_key: str = ""
    groq_model: str = "llama-3.1-8b-instant"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    hf_token: str = ""
    hf_model: str = "meta-llama/Llama-3.1-8B-Instruct"
    hf_base_url: str = "https://router.huggingface.co/v1"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2:3b"
    llm_timeout_seconds: float = 45.0
    llm_max_retries: int = 2
    llm_max_concurrency: int = 6
    llm_max_rpm: int = 0

    embedding_backend: str = "fastembed"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    similarity_threshold: float = 0.65
    top_k_per_paper: int = 2
    max_referee_pairs: int = 60
    referee_pairs_per_call: int = 4
    cluster_distance_threshold: float = 0.35

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.cors_allow_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
