# Argon 4 Review Bundle — D1 (Backend Scaffold, Contract Schemas & Demo Endpoints)
Author: DuroT | Branch: feat/d1-scaffold-contracts | Base: main
Target: Argon 4 (Google AI Studio, thinking = High, temperature = 0.2)

## 1. Acceptance criteria status
- [x] `schemas.py` identical to contract §1; `SCHEMA_VERSION == "1.0.0"`.
- [x] `pytest` passes (10/10 tests passed in 0.67s): every file in `fixtures/*.json` validates against `AnalysisResult`; every `claim.paper_id`, `cluster_id`, `edge.*_claim_id`, `gap.claim_id`, `consensus.*_ids` resolves; edge quotes equal claim quotes; `edge_id` follows contract rule (`e-{src}-{tgt}`); `cross_paper_pairs_total` and `pair_reduction_pct` recompute correctly; `consensus_score` equals the formula; latency parts sum to `total_ms`.
- [x] `GET /api/v1/health`, `GET /api/v1/demo`, `GET /api/v1/demo/{id}` work; unknown id returns 404 `PRESET_NOT_FOUND` with standard `ErrorResponse` shape.
- [x] Three placeholder fixtures exist (8/6/6 papers: `demo_radiology_8papers.json`, `demo_llm_quantization_6papers.json`, `demo_microgrids_6papers.json`) and validate strictly against Pydantic schema with `extra="forbid"`.
- [x] CORS allows `http://localhost:3000`, `http://localhost:5500`, `http://127.0.0.1:5500`, `http://localhost:5173`.
- [x] Early starter files removed; no secrets committed; `.env.example` complete.
- [x] PR template (`.github/pull_request_template.md`) and Argon 4 review bundle created.

## 2. git diff --stat main...HEAD
```
 .github/pull_request_template.md                 |   21 +
 backend/.env.example                             |   46 +-
 backend/app/__init__.py                          |    1 -
 backend/app/api/__init__.py                      |    0
 backend/app/api/demo.py                          |   54 +
 backend/app/api/health.py                        |   38 +
 backend/app/config.py                            |   53 +
 backend/app/errors.py                            |   20 +
 backend/app/main.py                              |   76 +-
 backend/app/schemas.py                           |  302 +++++
 backend/data/sample_trios/radiology.json         |  146 ---
 backend/requirements.txt                         |   25 +-
 backend/scripts/__init__.py                      |    0
 backend/scripts/generate_placeholder_fixtures.py |  668 +++++++++++
 backend/tests/__init__.py                        |    0
 backend/tests/conftest.py                        |    7 +
 backend/tests/test_contract.py                   |   91 ++
 backend/tests/test_demo_api.py                   |   55 +
 docs/AI_ASSISTANCE.md                            |    2 +-
 docs/reviews/D1-review-bundle.md                 |  120 +++
 fixtures/demo_llm_quantization_6papers.json      | 1047 ++++++++++++++++++
 fixtures/demo_microgrids_6papers.json            | 1046 +++++++++++++++++
 fixtures/demo_radiology_8papers.json             | 1293 ++++++++++++++++++++++
 23 files changed, 4882 insertions(+), 229 deletions(-)
```

## 3. Code under review (Key Components)

### `backend/app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import demo, health
from app.config import get_settings
from app.errors import install_error_handlers

settings = get_settings()
app = FastAPI(title="Kairos API", version=settings.app_version)
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
```

### `backend/app/api/demo.py`
```python
import json
from pathlib import Path
from fastapi import APIRouter
from app.config import get_settings
from app.errors import KairosError
from app.schemas import AnalysisResult, DemoPresetSummary, ErrorCode

router = APIRouter(tags=["demo"])

PRESETS: dict[str, tuple[str, str, str, str]] = {
    "radiology": ("demo_radiology_8papers.json", "Deep learning in chest radiography", "8 papers on lab vs real-world performance", "Medical imaging"),
    "llm_quantization": ("demo_llm_quantization_6papers.json", "LLM quantization trade-offs", "6 papers on accuracy vs efficiency", "Machine learning"),
    "microgrids": ("demo_microgrids_6papers.json", "Solar micro-grid reliability", "6 papers on storage and stability", "Energy systems"),
    "contract_sample": ("contract_sample.json", "Contract sample (3 papers)", "Synthetic payload that illustrates the API contract", "Contract"),
}

def _resolve_fixture_path(filename: str) -> Path:
    settings = get_settings()
    candidate1 = Path(settings.fixtures_dir) / filename
    if candidate1.exists():
        return candidate1
    candidate2 = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / filename
    if candidate2.exists():
        return candidate2
    return candidate1

def _load(preset_id: str) -> AnalysisResult:
    if preset_id not in PRESETS:
        raise KairosError(ErrorCode.PRESET_NOT_FOUND, f"Unknown preset '{preset_id}'.", 404)
    path = _resolve_fixture_path(PRESETS[preset_id][0])
    if not path.exists():
        raise KairosError(ErrorCode.PRESET_NOT_FOUND, f"Preset file for '{preset_id}' is missing.", 404)
    return AnalysisResult.model_validate(json.loads(path.read_text(encoding="utf-8")))

@router.get("/demo", response_model=list[DemoPresetSummary])
def list_presets() -> list[DemoPresetSummary]:
    out = []
    for pid, (_, title, desc, domain) in PRESETS.items():
        try:
            r = _load(pid)
        except KairosError:
            continue
        out.append(DemoPresetSummary(preset_id=pid, title=title, description=desc, domain=domain,
                                     paper_count=len(r.papers), fixture_provenance=r.fixture_provenance))
    return out

@router.get("/demo/{preset_id}", response_model=AnalysisResult)
def get_preset(preset_id: str) -> AnalysisResult:
    return _load(preset_id)
```

## 4. Verification test output
```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
rootdir: C:\Users\USER\Documents\CODE\HACKATHONS\OPEN BUILD AI\backend
collected 10 items

tests/test_contract.py::test_fixture_schema_validation[contract_sample.json] PASSED [ 10%]
tests/test_contract.py::test_fixture_schema_validation[demo_llm_quantization_6papers.json] PASSED [ 20%]
tests/test_contract.py::test_fixture_schema_validation[demo_microgrids_6papers.json] PASSED [ 30%]
tests/test_contract.py::test_fixture_schema_validation[demo_radiology_8papers.json] PASSED [ 40%]
tests/test_demo_api.py::test_health_endpoint PASSED                      [ 50%]
tests/test_demo_api.py::test_list_demo_presets PASSED                    [ 60%]
tests/test_demo_api.py::test_get_demo_preset_radiology PASSED            [ 70%]
tests/test_demo_api.py::test_get_demo_preset_llm_quantization PASSED     [ 80%]
tests/test_demo_api.py::test_get_demo_preset_microgrids PASSED           [ 90%]
tests/test_demo_api.py::test_get_demo_preset_not_found PASSED            [100%]

============================= 10 passed in 0.67s ==============================
```

## 5. Security and secrets check
- `.env` committed: No (verified via `git status` and `.gitignore`).
- Hardcoded API keys or bearer tokens in code: None.
- Untrusted user input validation: `preset_id` checked against whitelist dictionary keys; unknown keys immediately raise 404 without disk path traversal vulnerability.

## 6. Questions for the reviewer (minimum 3)
1. **Fixture path resolution:** Does `_resolve_fixture_path` cover both local execution (`python -m uvicorn app.main:app` from `/backend`) and containerized/monorepo execution?
2. **Schema strictness:** Does Pydantic v2 `extra="forbid"` on all models sufficiently guard against client/server drift during async development with the frontend?
3. **Preset caching:** For Demo Day latency, should the loaded `AnalysisResult` objects in `demo.py` be cached in memory with `@lru_cache` to guarantee < 5ms response times?

## 7. Contract and rules compliance
- Matches `docs/shared/02-api-contracts.md` exactly: Yes (Pydantic schemas copied verbatim).
- Open-weight models only: Yes (Metadata disclosed: `meta-llama/Llama-3.1-8B-Instruct` and `BAAI/bge-small-en-v1.5`).
- Provenance preserved: Yes (every claim and edge carries complete `Provenance`).
- Secrets in diff: None.
