import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import get_settings
from app.schemas import ErrorCode

client = TestClient(app)


def test_health_endpoint():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["status"] in ["ok", "degraded"]
    assert "providers" in data
    assert "groq" in data["providers"]
    assert data["presets_loaded"] == ["contract_sample", "llm_quantization", "microgrids", "radiology"]


def test_health_degraded_when_no_llm_configured(monkeypatch):
    """Verify health status is degraded and Ollama is not falsely reported as configured when empty."""
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("HF_TOKEN", "")
    monkeypatch.setenv("OLLAMA_BASE_URL", "")
    get_settings.cache_clear()

    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "degraded"
    assert data["providers"]["groq"]["configured"] is False
    assert data["providers"]["huggingface"]["configured"] is False
    assert data["providers"]["ollama"]["configured"] is False
    assert data["presets_loaded"] == ["contract_sample", "llm_quantization", "microgrids", "radiology"]

    # Restore cache
    get_settings.cache_clear()


def test_list_demo_presets():
    res = client.get("/api/v1/demo")
    assert res.status_code == 200
    presets = res.json()
    assert isinstance(presets, list)
    preset_ids = {p["preset_id"] for p in presets}
    assert "radiology" in preset_ids
    assert "llm_quantization" in preset_ids
    assert "microgrids" in preset_ids
    assert "contract_sample" in preset_ids


def test_get_demo_preset_radiology():
    res = client.get("/api/v1/demo/radiology")
    assert res.status_code == 200
    data = res.json()
    assert data["preset_id"] == "radiology"
    assert data["fixture_provenance"] == "REAL_PIPELINE_OUTPUT"
    assert len(data["papers"]) >= 2
    assert len(data["claims"]) >= 4


def test_get_demo_preset_llm_quantization():
    res = client.get("/api/v1/demo/llm_quantization")
    assert res.status_code == 200
    data = res.json()
    assert data["preset_id"] == "llm_quantization"
    assert data["fixture_provenance"] == "REAL_PIPELINE_OUTPUT"
    assert len(data["papers"]) >= 2
    assert len(data["claims"]) >= 4


def test_get_demo_preset_microgrids():
    res = client.get("/api/v1/demo/microgrids")
    assert res.status_code == 200
    data = res.json()
    assert data["preset_id"] == "microgrids"
    assert data["fixture_provenance"] == "REAL_PIPELINE_OUTPUT"
    assert len(data["papers"]) >= 2
    assert len(data["claims"]) >= 4


def test_get_demo_preset_not_found():
    res = client.get("/api/v1/demo/nonexistent_preset_xyz")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == ErrorCode.PRESET_NOT_FOUND.value
    assert "Unknown preset" in data["error"]["message"]


def test_error_envelope_for_http_404():
    """Verify unhandled HTTP 404 errors adhere to the ErrorResponse wire contract."""
    res = client.get("/api/v1/totally_non_existent_route")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == ErrorCode.PRESET_NOT_FOUND.value
    assert data["error"]["message"] == "Not Found"


def test_error_envelope_for_validation_error():
    """Verify 422 request validation errors return ErrorResponse with structured details."""
    from fastapi import APIRouter
    from pydantic import BaseModel, Field

    class SampleInput(BaseModel):
        num: int = Field(ge=10)

    test_router = APIRouter()

    @test_router.post("/test-val")
    def sample_endpoint(payload: SampleInput):
        return {"status": "ok"}

    app.include_router(test_router, prefix="/api/v1/test-validation")

    res = client.post("/api/v1/test-validation/test-val", json={"num": 3})
    assert res.status_code == 422
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == ErrorCode.INTERNAL_ERROR.value
    assert data["error"]["message"] == "Request validation error"
    assert "errors" in data["error"]["details"]



def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["health_url"] == "/api/v1/health"


def test_vercel_cors_origin_regex():
    res = client.get(
        "/api/v1/health",
        headers={"Origin": "https://kairos-openbuild.vercel.app"},
    )
    assert res.status_code == 200
    assert res.headers.get("access-control-allow-origin") == "https://kairos-openbuild.vercel.app"


def test_get_demo_preset_by_filename_alias():
    res = client.get("/api/v1/demo/demo_radiology_8papers")
    assert res.status_code == 200
    assert res.json()["preset_id"] == "radiology"
