import asyncio
import random
import re
from typing import Any, Callable, TypeVar
from openai import (
    AsyncOpenAI,
    RateLimitError,
    APITimeoutError,
    APIConnectionError,
    APIStatusError,
    AuthenticationError,
    BadRequestError,
)
from app.config import Settings
from app.errors import KairosError
from app.schemas import ErrorCode
from app.services.llm.json_utils import parse_json_object, InvalidJSON
from app.services.llm.providers import Provider, build_provider_chain
from app.services.prompts.extraction import CORRECTIVE_RETRY_TEMPLATE

T = TypeVar("T")


def _retry_after(exc: RateLimitError) -> float:
    """Extracts Retry-After delay from response headers if available, capped at 5.0s with jitter."""
    delay = 1.5
    try:
        if hasattr(exc, "response") and exc.response is not None:
            header = exc.response.headers.get("retry-after")
            if header:
                delay = min(max(0.5, float(header)), 5.0)
    except Exception:
        pass
    # Add random jitter (0.1s - 0.6s) to prevent concurrent synchronized thundering herd
    return delay + random.uniform(0.1, 0.6)


class LLMClient:
    """
    OpenAI-compatible client managing open-weight LLM inference across a fallback chain:
    - Provider fallback: Groq -> Hugging Face -> local Ollama.
    - Concurrency semaphore (default: 6 concurrent requests).
    - Automatic JSON decoding and schema validation.
    - Single corrective retry upon invalid JSON output.
    - 401/403 provider deactivation without logging secret keys.
    - Rate limit retry once with Retry-After backoff before fail-over.
    - API key scrubbing on unexpected exceptions and error responses.
    """

    def __init__(self, settings: Settings, providers: list[Provider] | None = None):
        self.settings = settings
        self.providers = providers if providers is not None else build_provider_chain(settings)
        self.sem = asyncio.Semaphore(settings.llm_max_concurrency)
        self.disabled: set[str] = set()
        self.last_used_model: str = ""
        self.last_used_provider: str = ""
        self.call_count: int = 0
        self._clients: dict[str, AsyncOpenAI] = {}

    def _get_client(self, p: Provider) -> AsyncOpenAI:
        if p.name not in self._clients:
            self._clients[p.name] = AsyncOpenAI(
                base_url=p.base_url,
                api_key=p.api_key or "none",
                timeout=self.settings.llm_timeout_seconds,
            )
        return self._clients[p.name]

    async def aclose(self) -> None:
        """Close all persistent AsyncOpenAI client connections (Opt 2)."""
        for client in list(self._clients.values()):
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        max_tokens: int,
        temperature: float,
        validate: Callable[[dict[str, Any]], T],
    ) -> tuple[T, str, str]:
        """
        Executes an LLM JSON completion with validation and provider fail-over.
        Returns:
            (validated_result, provider_name, model_id)
        Raises:
            KairosError(LLM_PROVIDER_UNAVAILABLE): if all configured providers fail.
        """
        last_error = "no provider configured"

        for p in self.providers:
            if p.name in self.disabled:
                continue

            client = self._get_client(p)
            messages = [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ]

            use_response_format = True

            for attempt in range(max(1, self.settings.llm_max_retries)):
                text = ""
                try:
                    async with self.sem:
                        kwargs: dict[str, Any] = {
                            "model": p.model,
                            "messages": messages,
                            "temperature": temperature,
                            "max_tokens": max_tokens,
                        }
                        if use_response_format:
                            kwargs["response_format"] = {"type": "json_object"}

                        try:
                            resp = await client.chat.completions.create(**kwargs)
                        except BadRequestError as bad_req:
                            # Some local models or endpoints reject response_format parameter
                            if use_response_format and "response_format" in str(bad_req).lower():
                                use_response_format = False
                                kwargs.pop("response_format", None)
                                resp = await client.chat.completions.create(**kwargs)
                            else:
                                raise

                    text = resp.choices[0].message.content or ""
                    parsed = parse_json_object(text)
                    validated = validate(parsed)
                    self.last_used_model = p.model
                    self.last_used_provider = p.name
                    self.call_count += 1
                    return validated, p.name, p.model

                except (InvalidJSON, ValueError) as err:
                    # Catch JSON parsing error or Pydantic ValidationError (subclass of ValueError)
                    last_error = f"{p.name}: invalid output ({err})"
                    if attempt + 1 < self.settings.llm_max_retries:
                        # Append corrective retry dialog formatted from template
                        messages = list(messages) + [
                            {"role": "assistant", "content": text},
                            {
                                "role": "user",
                                "content": CORRECTIVE_RETRY_TEMPLATE.format(error_message=str(err)),
                            },
                        ]
                        continue
                    break

                except AuthenticationError:
                    self.disabled.add(p.name)
                    last_error = f"{p.name}: authentication failed"
                    break

                except RateLimitError as rle:
                    last_error = f"{p.name}: rate limited"
                    if attempt == 0:
                        await asyncio.sleep(_retry_after(rle))
                        continue
                    break

                except (APITimeoutError, APIConnectionError) as net_err:
                    last_error = f"{p.name}: connection error ({net_err.__class__.__name__})"
                    break

                except APIStatusError as status_err:
                    # Auto-fallback on Groq if llama-3.1-8b-instant is restricted (404) in region/project
                    if p.name == "groq" and status_err.status_code == 404 and p.model != "qwen/qwen3.8-27b":
                        p.model = "qwen/qwen3.8-27b"
                        continue
                    # Auto-truncate prompt if Groq free tier rejects request size with HTTP 413 (TPM limit)
                    if status_err.status_code == 413 and len(messages[-1]["content"]) > 6000:
                        messages[-1]["content"] = messages[-1]["content"][:10000] + "\n\nReturn the JSON object now."
                        max_tokens = min(max_tokens, 1500)
                        continue
                    last_error = f"{p.name}: HTTP {status_err.status_code}"
                    break

                except Exception as exc:
                    last_error = f"{p.name}: unexpected error ({exc})"
                    break

        # Scrub any provider API keys before raising
        for p in self.providers:
            if p.api_key and len(p.api_key) > 4:
                last_error = last_error.replace(p.api_key, "[REDACTED]")

        raise KairosError(
            ErrorCode.LLM_PROVIDER_UNAVAILABLE,
            f"All LLM providers failed ({last_error}). Use a demo preset or check LLM credentials.",
            503,
            details={"last_error": last_error},
        )
