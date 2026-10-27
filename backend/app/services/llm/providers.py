from dataclasses import dataclass
from app.config import Settings


@dataclass(frozen=True)
class Provider:
    """Represents an open-weight LLM inference provider endpoint."""
    name: str
    base_url: str
    api_key: str
    model: str
    license_name: str
    license_url: str


def build_provider_chain(settings: Settings) -> list[Provider]:
    """
    Builds the active provider fallback chain based on settings.llm_provider_chain.
    Providers with missing credentials or unconfigured URLs are skipped.
    """
    chain_names = [p.strip().lower() for p in settings.llm_provider_chain.split(",") if p.strip()]
    active_providers: list[Provider] = []

    for name in chain_names:
        if name == "groq":
            key = settings.groq_api_key.strip()
            if key:
                active_providers.append(
                    Provider(
                        name="groq",
                        base_url=settings.groq_base_url.strip(),
                        api_key=key,
                        model=settings.groq_model.strip() or "llama-3.1-8b-instant",
                        license_name="Llama 3.1 Community License",
                        license_url="https://www.llama.com/llama3_1/license/",
                    )
                )
        elif name == "huggingface":
            token = settings.hf_token.strip()
            if token:
                active_providers.append(
                    Provider(
                        name="huggingface",
                        base_url=settings.hf_base_url.strip(),
                        api_key=token,
                        model=settings.hf_model.strip() or "meta-llama/Llama-3.1-8B-Instruct",
                        license_name="Llama 3.1 Community License",
                        license_url="https://www.llama.com/llama3_1/license/",
                    )
                )
        elif name == "ollama":
            url = settings.ollama_base_url.strip()
            if url:
                active_providers.append(
                    Provider(
                        name="ollama",
                        base_url=url,
                        api_key="ollama",
                        model=settings.ollama_model.strip() or "llama3.2:3b",
                        license_name="Llama 3.2 Community License",
                        license_url="https://www.llama.com/llama3_2/license/",
                    )
                )

    return active_providers
