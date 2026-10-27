import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import pytest
from openai import (
    AuthenticationError,
    RateLimitError,
    APITimeoutError,
)
from app.config import Settings
from app.errors import KairosError
from app.schemas import ErrorCode
from app.services.llm.client import LLMClient
from app.services.llm.json_utils import parse_json_object, InvalidJSON
from app.services.llm.providers import Provider, build_provider_chain


def test_parse_json_object_valid():
    """Verifies that valid JSON objects parse cleanly."""
    res = parse_json_object('{"title": "Test Paper", "year": 2024}')
    assert res == {"title": "Test Paper", "year": 2024}


def test_parse_json_object_code_fenced():
    """Verifies that markdown code-fenced JSON is unpacked."""
    fenced = """```json
    {
      "status": "ok",
      "findings": [1, 2, 3]
    }
    ```"""
    res = parse_json_object(fenced)
    assert res == {"status": "ok", "findings": [1, 2, 3]}


def test_parse_json_object_invalid_syntax():
    """Rejects malformed JSON syntax with InvalidJSON."""
    with pytest.raises(InvalidJSON):
        parse_json_object('{"title": "Unclosed string')

    with pytest.raises(InvalidJSON):
        parse_json_object("Just a regular sentence with no braces.")


def test_build_provider_chain_skips_unconfigured():
    """Verifies that providers with empty keys/tokens are skipped."""
    settings = Settings(
        llm_provider_chain="groq,huggingface,ollama",
        groq_api_key="",  # empty
        hf_token="test_hf_token",  # present
        ollama_base_url="http://localhost:11434/v1",  # present
    )
    chain = build_provider_chain(settings)
    names = [p.name for p in chain]
    assert "groq" not in names
    assert "huggingface" in names
    assert "ollama" in names


def test_llm_client_success():
    """Verifies successful completion without fail-over."""
    async def _run():
        settings = Settings(llm_max_concurrency=2, llm_max_retries=2)
        provider = Provider("groq", "https://api.groq.com", "fake_key", "llama-3.1-8b-instant", "MIT", "http://mit.edu")
        client = LLMClient(settings, providers=[provider])

        mock_choice = MagicMock()
        mock_choice.message.content = '{"result": "success"}'
        mock_resp = MagicMock()
        mock_resp.choices = [mock_choice]

        with patch("app.services.llm.client.AsyncOpenAI") as mock_openai_cls:
            mock_inst = AsyncMock()
            mock_inst.chat.completions.create.return_value = mock_resp
            mock_openai_cls.return_value = mock_inst

            data, prov, model = await client.complete_json(
                system="sys",
                user="usr",
                max_tokens=500,
                temperature=0.1,
                validate=lambda d: d["result"],
            )
            assert data == "success"
            assert prov == "groq"
            assert model == "llama-3.1-8b-instant"

    asyncio.run(_run())


def test_llm_client_corrective_retry_on_invalid_json():
    """Verifies that an initial invalid JSON response triggers a corrective retry that succeeds."""
    async def _run():
        settings = Settings(llm_max_concurrency=2, llm_max_retries=2)
        provider = Provider("groq", "https://api.groq.com", "fake_key", "llama-3.1-8b-instant", "MIT", "http://mit.edu")
        client = LLMClient(settings, providers=[provider])

        # Attempt 1 returns broken JSON, Attempt 2 returns valid JSON
        mock_resp1 = MagicMock()
        mock_resp1.choices = [MagicMock(message=MagicMock(content='broken json text { '))]

        mock_resp2 = MagicMock()
        mock_resp2.choices = [MagicMock(message=MagicMock(content='{"status": "recovered"}'))]

        with patch("app.services.llm.client.AsyncOpenAI") as mock_openai_cls:
            mock_inst = AsyncMock()
            mock_inst.chat.completions.create.side_effect = [mock_resp1, mock_resp2]
            mock_openai_cls.return_value = mock_inst

            data, prov, model = await client.complete_json(
                system="sys",
                user="usr",
                max_tokens=500,
                temperature=0.1,
                validate=lambda d: d["status"],
            )
            assert data == "recovered"
            assert mock_inst.chat.completions.create.call_count == 2

    asyncio.run(_run())


def test_llm_client_401_disabling_and_failover():
    """Verifies that a 401 AuthenticationError disables that provider and fails over to the next."""
    async def _run():
        settings = Settings(llm_max_concurrency=2, llm_max_retries=1)
        p1 = Provider("groq", "https://api.groq.com", "bad_key", "llama-3.1-8b-instant", "MIT", "http://mit.edu")
        p2 = Provider("hf", "https://api.hf.co", "good_token", "meta-llama/Llama-3.1-8B-Instruct", "MIT", "http://mit.edu")
        client = LLMClient(settings, providers=[p1, p2])

        mock_resp_success = MagicMock()
        mock_resp_success.choices = [MagicMock(message=MagicMock(content='{"source": "hf"}'))]

        with patch("app.services.llm.client.AsyncOpenAI") as mock_openai_cls:
            mock_client_p1 = AsyncMock()
            mock_client_p1.chat.completions.create.side_effect = AuthenticationError(
                "Invalid API key", response=MagicMock(status_code=401), body={}
            )

            mock_client_p2 = AsyncMock()
            mock_client_p2.chat.completions.create.return_value = mock_resp_success

            mock_openai_cls.side_effect = [mock_client_p1, mock_client_p2]

            data, prov, model = await client.complete_json(
                system="sys",
                user="usr",
                max_tokens=500,
                temperature=0.1,
                validate=lambda d: d["source"],
            )
            assert data == "hf"
            assert prov == "hf"
            # Verify p1 is permanently disabled
            assert "groq" in client.disabled

    asyncio.run(_run())


def test_llm_client_all_providers_fail():
    """Verifies that exhaustion of all providers raises KairosError(LLM_PROVIDER_UNAVAILABLE)."""
    async def _run():
        settings = Settings(llm_max_concurrency=2, llm_max_retries=1)
        p1 = Provider("ollama", "http://localhost:11434/v1", "ollama", "llama3.2:3b", "MIT", "http://mit.edu")
        client = LLMClient(settings, providers=[p1])

        with patch("app.services.llm.client.AsyncOpenAI") as mock_openai_cls:
            mock_inst = AsyncMock()
            mock_inst.chat.completions.create.side_effect = APITimeoutError(request=MagicMock())
            mock_openai_cls.return_value = mock_inst

            with pytest.raises(KairosError) as exc_info:
                await client.complete_json(
                    system="sys",
                    user="usr",
                    max_tokens=500,
                    temperature=0.1,
                    validate=lambda d: d,
                )
            assert exc_info.value.code == ErrorCode.LLM_PROVIDER_UNAVAILABLE
            assert exc_info.value.status_code == 503

    asyncio.run(_run())
