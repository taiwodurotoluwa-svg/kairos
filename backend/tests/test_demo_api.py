from fastapi.testclient import TestClient
from app.main import app
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
    assert "presets_loaded" in data

def test_list_demo_presets():
    res = client.get("/api/v1/demo")
    assert res.status_code == 200
    presets = res.json()
    assert isinstance(presets, list)
    preset_ids = {p["preset_id"] for p in presets}
    assert "radiology" in preset_ids
    assert "llm_quantization" in preset_ids
    assert "microgrids" in preset_ids

def test_get_demo_preset_radiology():
    res = client.get("/api/v1/demo/radiology")
    assert res.status_code == 200
    data = res.json()
    assert data["preset_id"] == "radiology"
    assert len(data["papers"]) == 8
    assert len(data["claims"]) == 40
    assert len(data["edges"]) == 8

def test_get_demo_preset_llm_quantization():
    res = client.get("/api/v1/demo/llm_quantization")
    assert res.status_code == 200
    data = res.json()
    assert data["preset_id"] == "llm_quantization"
    assert len(data["papers"]) == 6

def test_get_demo_preset_microgrids():
    res = client.get("/api/v1/demo/microgrids")
    assert res.status_code == 200
    data = res.json()
    assert data["preset_id"] == "microgrids"
    assert len(data["papers"]) == 6

def test_get_demo_preset_not_found():
    res = client.get("/api/v1/demo/nonexistent_preset_xyz")
    assert res.status_code == 404
    data = res.json()
    assert "error" in data
    assert data["error"]["code"] == ErrorCode.PRESET_NOT_FOUND.value
