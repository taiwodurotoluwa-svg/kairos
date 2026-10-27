# Backend Execution Playbook — DuroT

**Developer:** Durotoluwa Taiwo (`taiwodurotoluwa-svg`, `taiwodurotoluwa@gmail.com`)
**Workspace:** `/backend`, `/fixtures`, `/docs/duro` · **Stack:** Python 3.11+, FastAPI, PyMuPDF, httpx, OpenAI-compatible SDK (Groq / Hugging Face / Ollama), FastEmbed (`BAAI/bge-small-en-v1.5`), NumPy, scikit-learn, rapidfuzz, Pydantic v2, pytest.

Agents: read `AGENTS.md` first, confirm you are working for **DuroT**, then execute exactly one milestone at a time. Contract: `docs/shared/02-api-contracts.md`. Prompts: `docs/shared/03-open-weight-models.md`.

> The repo already contains an **early starter** (`backend/app/main.py`, `backend/requirements.txt`, `backend/.env.example`, `backend/data/sample_trios/radiology.json`) written before the contract existed. **D1 replaces all of it.** Delete `backend/data/` (its radiology file invents papers and does not match the contract).

---

## Final backend directory tree (target after D5)

```
backend/
├── Dockerfile
├── .env.example
├── pytest.ini
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI app, CORS, routers, startup preload
│   ├── config.py                  # Settings (env)
│   ├── errors.py                  # KairosError + exception handler
│   ├── schemas.py                 # Pydantic contract (copied from 02-api-contracts.md §1)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py              # GET /api/v1/health
│   │   ├── demo.py                # GET /api/v1/demo, /demo/{preset_id}
│   │   └── analyze.py             # POST /analyze, GET /analyze/{id}, GET /analyze/{id}/events
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── extraction.py          # Stage 1 system/user prompt builders (verbatim from 03 §3)
│   │   ├── referee.py             # Stage 3 prompts (03 §5.1-5.2)
│   │   └── consensus.py           # Stage 4 prompt (03 §5.4)
│   └── services/
│       ├── __init__.py
│       ├── ingestion/
│       │   ├── __init__.py
│       │   ├── validators.py      # counts, %PDF- magic, size, de-duplication
│       │   ├── pdf_parser.py      # PyMuPDF → page_texts
│       │   ├── sectioner.py       # headings → sections → budgeted text with markers
│       │   └── arxiv_fetcher.py   # id normalisation + async download
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── providers.py       # Provider dataclass + chain builder
│       │   ├── client.py          # complete_json() with retry + fail-over
│       │   └── json_utils.py      # robust JSON object parsing
│       ├── extraction.py          # Stage 1
│       ├── quote_verifier.py      # 03 §6
│       ├── embeddings.py          # Stage 2 backends
│       ├── similarity.py          # matrix, candidates, gaps, clustering
│       ├── referee.py             # Stage 3
│       ├── consensus.py           # score + Stage 4 + fallback summary
│       ├── graph_builder.py       # ids, ordering, AnalysisResult assembly
│       ├── jobs.py                # in-memory job store + SSE pub/sub
│       ├── rate_limit.py          # per-IP sliding window
│       └── pipeline.py            # orchestration
├── scripts/
│   ├── generate_placeholder_fixtures.py   # D1
│   ├── tune_threshold.py                  # D4
│   ├── bake_presets.py                    # D5
│   └── verify_fixture_quotes.py           # D5
└── tests/
    ├── conftest.py
    ├── data/                       # tiny test PDFs generated in tests, tuning_pairs.json
    ├── test_contract.py            # D1
    ├── test_demo_api.py            # D1
    ├── test_ingestion.py           # D2
    ├── test_arxiv.py               # D2
    ├── test_llm_client.py          # D3
    ├── test_extraction.py          # D3
    ├── test_quote_verifier.py      # D3
    ├── test_similarity.py          # D4
    ├── test_referee.py             # D4
    ├── test_consensus.py           # D5
    ├── test_pipeline.py            # D5
    └── test_analyze_api.py         # D5
fixtures/
├── contract_sample.json            # already committed (synthetic, 3 papers)
├── demo_radiology_8papers.json
├── demo_llm_quantization_6papers.json
├── demo_microgrids_6papers.json
└── presets_manifest.json           # D5
```

## Environment variables (`backend/.env.example`)

```ini
# --- App ---
APP_ENV=development
APP_VERSION=1.0.0
CORS_ALLOW_ORIGINS=http://localhost:3000
FIXTURES_DIR=../fixtures

# --- Limits ---
MIN_PAPERS=2
MAX_PAPERS=10
MAX_FILE_MB=20
MAX_TOTAL_MB=80
MAX_PAPER_CHARS=24000
ANALYZE_RATE_LIMIT_PER_MINUTE=6
JOB_TTL_MINUTES=60
JOB_TIMEOUT_SECONDS=90
ARXIV_CONCURRENCY=3

# --- LLM providers (fill at least one; presets work with none) ---
LLM_PROVIDER_CHAIN=groq,huggingface,ollama
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-8b-instant
GROQ_BASE_URL=https://api.groq.com/openai/v1
HF_TOKEN=
HF_MODEL=meta-llama/Llama-3.1-8B-Instruct
HF_BASE_URL=https://router.huggingface.co/v1
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2:3b
LLM_TIMEOUT_SECONDS=45
LLM_MAX_RETRIES=2
LLM_MAX_CONCURRENCY=6
LLM_MAX_RPM=0

# --- Embeddings ---
EMBEDDING_BACKEND=fastembed
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5

# --- Similarity / referee ---
SIMILARITY_THRESHOLD=0.65
TOP_K_PER_PAPER=2
MAX_REFEREE_PAIRS=60
REFEREE_PAIRS_PER_CALL=4
CLUSTER_DISTANCE_THRESHOLD=0.35
```

`backend/requirements.txt`:

```
fastapi>=0.110
uvicorn[standard]>=0.29
pydantic>=2.6
pydantic-settings>=2.2
python-multipart>=0.0.9
pymupdf>=1.24
httpx>=0.27
openai>=1.30
numpy>=1.26
scikit-learn>=1.4
fastembed>=0.3
rapidfuzz>=3.6
sse-starlette>=2.1
pytest>=8.0
pytest-asyncio>=0.23
respx>=0.21
```

---

## Milestone D1 — Scaffold, contracts, demo endpoints, placeholder fixtures

**Branch:** `feat/d1-scaffold-contracts` · **Depends on:** none · **Goal:** the frontend can build against real endpoints and 8/6/6-paper fixtures within the first session.

### Steps
1. Delete the early starter: `backend/app/main.py`, `backend/data/`. Create the tree above (empty `__init__.py` files where shown).
2. Write `requirements.txt` and `.env.example` exactly as above.
3. Copy the Pydantic block from `docs/shared/02-api-contracts.md` §1 **verbatim** into `app/schemas.py`.
4. Implement `app/config.py`, `app/errors.py`, `app/main.py`, `app/api/health.py`, `app/api/demo.py` (skeletons below).
5. Create `.github/pull_request_template.md` (checklist from `AGENTS.md` §6) and `docs/AI_ASSISTANCE.md` rows for D1 later.
6. Write `scripts/generate_placeholder_fixtures.py` and run it to create the three placeholder fixtures (spec below).
7. Write `tests/test_contract.py` and `tests/test_demo_api.py`.
8. Push **early**: open the D1 PR (and notify Peace via `docs/requests.md`) as soon as fixtures + demo endpoints pass tests, then finish remaining polish in follow-up commits. Peace is blocked on P3 until the fixtures exist.

### Code skeletons

```python
# app/config.py
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_version: str = "1.0.0"
    cors_allow_origins: str = "http://localhost:3000"
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
```

```python
# app/errors.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.schemas import ErrorBody, ErrorCode, ErrorResponse


class KairosError(Exception):
    def __init__(self, code: ErrorCode, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code, self.message, self.status_code, self.details = code, message, status_code, details

    def to_body(self) -> ErrorBody:
        return ErrorBody(code=self.code, message=self.message, details=self.details)


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(KairosError)
    async def _handle(_: Request, exc: KairosError) -> JSONResponse:
        body = ErrorResponse(error=exc.to_body()).model_dump(mode="json")
        return JSONResponse(status_code=exc.status_code, content=body)
```

```python
# app/main.py
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
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
install_error_handlers(app)
app.include_router(health.router, prefix="/api/v1")
app.include_router(demo.router, prefix="/api/v1")
# analyze router is added in D5
```

```python
# app/api/demo.py
import json
from pathlib import Path

from fastapi import APIRouter

from app.config import get_settings
from app.errors import KairosError
from app.schemas import AnalysisResult, DemoPresetSummary, ErrorCode

router = APIRouter(tags=["demo"])

# preset_id -> (file name, title, description, domain)
PRESETS: dict[str, tuple[str, str, str, str]] = {
    "radiology": ("demo_radiology_8papers.json", "Deep learning in chest radiography", "8 papers on lab vs real-world performance", "Medical imaging"),
    "llm_quantization": ("demo_llm_quantization_6papers.json", "LLM quantization trade-offs", "6 papers on accuracy vs efficiency", "Machine learning"),
    "microgrids": ("demo_microgrids_6papers.json", "Solar micro-grid reliability", "6 papers on storage and stability", "Energy systems"),
    "contract_sample": ("contract_sample.json", "Contract sample (3 papers)", "Synthetic payload that illustrates the API contract", "Contract"),
}


def _load(preset_id: str) -> AnalysisResult:
    if preset_id not in PRESETS:
        raise KairosError(ErrorCode.PRESET_NOT_FOUND, f"Unknown preset '{preset_id}'.", 404)
    path = Path(get_settings().fixtures_dir) / PRESETS[preset_id][0]
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
            continue  # skip presets whose file is not there yet
        out.append(DemoPresetSummary(preset_id=pid, title=title, description=desc, domain=domain,
                                     paper_count=len(r.papers), fixture_provenance=r.fixture_provenance))
    return out


@router.get("/demo/{preset_id}", response_model=AnalysisResult)
def get_preset(preset_id: str) -> AnalysisResult:
    return _load(preset_id)
```

### `scripts/generate_placeholder_fixtures.py` — specification
Deterministic (seeded) generator producing `demo_radiology_8papers.json` (8 papers), `demo_llm_quantization_6papers.json` (6) and `demo_microgrids_6papers.json` (6). Requirements:
- `fixture_provenance = "SYNTHETIC_PLACEHOLDER"`, `mode = "DEMO"`, a `warnings` entry saying the data is synthetic, and **obviously fake paper titles** ("Placeholder Paper 3: …"). Never invent real-looking citations.
- 5 claims per paper (types mixed, ≥ 1 `CONCLUSION`), each with a complete `Provenance` (quote 10–600 chars, plausible `page_number` within `page_count`).
- 4–6 clusters; ≥ 8 edges including **at least 2 of each** `AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA`; ≥ 2 `ResearchGap` entries.
- Stats arithmetic consistent (`cross_paper_pairs_total`, `pair_reduction_pct`, `consensus_score` per contract §5–6, latency parts sum to `total_ms`).
- Output validates against `AnalysisResult` and passes the cross-reference checks below.

### Acceptance criteria (D1)
- [x] `schemas.py` identical to contract §1; `SCHEMA_VERSION == "1.0.0"`.
- [x] `pytest` passes, including `test_contract.py`: every file in `fixtures/*.json` validates against `AnalysisResult`; every `claim.paper_id`, `cluster_id`, `edge.*_claim_id`, `gap.claim_id`, `consensus.*_ids` resolves; edge quotes equal claim quotes; `edge_id` follows the contract rule; `cross_paper_pairs_total` and `pair_reduction_pct` recompute correctly; `consensus_score` equals the formula; latency parts sum to `total_ms`.
- [x] `GET /api/v1/health`, `GET /api/v1/demo`, `GET /api/v1/demo/{id}` work; unknown id → 404 `PRESET_NOT_FOUND` with `ErrorResponse` shape.
- [x] Three placeholder fixtures exist (8/6/6 papers) and are valid.
- [x] CORS allows `http://localhost:3000`.
- [x] Early starter files removed; no secrets committed; `.env.example` complete.
- [x] PR template and Argon 4 files committed.

### Argon 4 checklist (D1)
Contract parity with the doc (field by field), fixture honesty banners, cross-reference test strength, CORS/headers, error shape, startup with missing fixtures, settings defaults vs `.env.example`.

---

## Milestone D2 — Multi-PDF and arXiv ingestion

**Branch:** `feat/d2-ingestion` · **Depends on:** D1

### Steps
1. `validators.py`: `validate_inputs(files, arxiv_ids, settings)` → counts (2–10 after de-duplication by SHA-256 / normalised arXiv id), magic bytes `%PDF-`, size limits → raise `KairosError` with contract codes.
2. `pdf_parser.py`: `parse_pdf(data: bytes) -> ParsedPdf(page_texts: dict[int,str], page_count: int, meta_title: str|None)`; use `pymupdf.open(stream=data, filetype="pdf")`, `page.get_text("text", sort=True)`, dehyphenate, normalise paragraph breaks; raise `NO_TEXT_LAYER` when mean chars/page < 200; wrap open errors as `PDF_PARSE_FAILED`.
3. `sectioner.py`: implement heading regex, mapping, stop-at-references and budgets from `01-architecture.md` §2.4–2.6; produce `SectionedPaper(text_for_llm: str, sections_found: list[SectionName], page_texts)` with `[[SECTION: X]]` / `[[PAGE n]]` markers.
4. `arxiv_fetcher.py`: `normalize_arxiv_id()` (all accepted forms) and `async fetch_arxiv_pdfs(ids, settings)` with semaphore, timeout 30 s, `%PDF-` check → `ARXIV_FETCH_FAILED` per id.
5. Parallel ingestion helper `ingest_all()` using `asyncio.gather` + `asyncio.to_thread` for parsing; individual failures become warnings; fail with `TOO_FEW_PAPERS` if < 2 survive.
6. Tests: generate small PDFs in-test with PyMuPDF (`doc.new_page(); page.insert_text(...)`) including multi-page and heading cases; mock arXiv with `respx`.

### Key skeleton

```python
# app/services/ingestion/sectioner.py (core idea)
import re
from app.schemas import SectionName

HEADING_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?|[IVX]+\.)?\s*(abstract|introduction|related work|background|method(?:s|ology)?|approach|"
    r"materials and methods|experimental setup|experiments?|implementation details|results?|evaluation|discussion|"
    r"conclusions?|limitations?|future work|references|bibliography|acknowledg(?:e)?ments?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)
STOP = {"references", "bibliography", "acknowledgement", "acknowledgements", "acknowledgment", "acknowledgments"}
```

### Acceptance criteria (D2)
- [ ] 8 PDFs parsed concurrently in < 2 s on a laptop (test uses generated PDFs).
- [ ] Page numbers are correct and 1-indexed in `page_texts`.
- [ ] Sections detected for numbered and unnumbered headings; references excluded; budgets enforced (`len(text_for_llm) <= MAX_PAPER_CHARS`).
- [ ] No-heading fallback (head/tail) works and is tested.
- [ ] Non-PDF bytes → `INVALID_FILE_TYPE`; scanned-like PDF → `NO_TEXT_LAYER`; corrupt → `PDF_PARSE_FAILED`.
- [ ] arXiv forms normalise correctly (all five formats); failures isolated per id.
- [ ] Duplicate files/ids are de-duplicated.

### Argon 4 checklist (D2)
Regex false positives (e.g. "Results" inside body text), huge-PDF memory use, thread-safety of PyMuPDF usage, temp file handling (none left), budget truncation correctness, encoding issues.

---

## Milestone D3 — Open-weight LLM client, extraction, quote verifier

**Branch:** `feat/d3-llm-extraction` · **Depends on:** D1, D2 · First do the model-id verification checklist in `03-open-weight-models.md` §8.

### Steps
1. `llm/providers.py`: `Provider(name, base_url, api_key, model, license info)`; `build_provider_chain(settings)` skips unconfigured providers.
2. `llm/json_utils.py`: `parse_json_object(text)` — strip code fences, find the outermost `{...}`, `json.loads`, raise `InvalidJSON` otherwise.
3. `llm/client.py`: `LLMClient.complete_json(...)` (skeleton below) with semaphore, timeout, retries, fail-over, `Retry-After` once, 401/403 disable.
4. `prompts/extraction.py`: prompts **copied verbatim** from `03` §3.
5. `extraction.py`: call per paper (concurrent), validate with a Pydantic `RawExtraction` model, map to `PaperMetadata` + `ExtractedClaim`, run verifier.
6. `quote_verifier.py` implementing `03` §6 (skeleton below).
7. Tests with a **fake provider** (no network): valid JSON, fenced JSON, invalid JSON then corrective retry, 429 fail-over, 401 disabling, hallucinated quote dropped, fuzzy-matched quote repaired.

### Key skeletons

```python
# app/services/llm/client.py (essential logic)
import asyncio
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError, AuthenticationError

class LLMClient:
    def __init__(self, settings, providers):
        self.s, self.providers = settings, providers
        self.sem = asyncio.Semaphore(settings.llm_max_concurrency)
        self.disabled: set[str] = set()

    async def complete_json(self, *, system: str, user: str, max_tokens: int, temperature: float, validate):
        """Return (validated_obj, provider_name, model_id). `validate(dict) -> T` raises on bad shape."""
        last_error = "no provider configured"
        for p in self.providers:
            if p.name in self.disabled:
                continue
            client = AsyncOpenAI(base_url=p.base_url, api_key=p.api_key or "none", timeout=self.s.llm_timeout_seconds)
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            for attempt in range(self.s.llm_max_retries):
                try:
                    async with self.sem:
                        resp = await client.chat.completions.create(
                            model=p.model, messages=messages, temperature=temperature,
                            max_tokens=max_tokens, response_format={"type": "json_object"})
                    text = resp.choices[0].message.content or ""
                    return validate(parse_json_object(text)), p.name, p.model
                except (InvalidJSON, ValueError) as e:        # pydantic ValidationError subclasses ValueError
                    last_error = f"invalid output: {e}"
                    messages = messages + [{"role": "assistant", "content": text},
                                           {"role": "user", "content": f"Your previous reply was rejected: {e}. Reply again with ONLY the corrected JSON object that satisfies the schema. Do not apologise or explain."}]
                except AuthenticationError:
                    self.disabled.add(p.name); last_error = f"{p.name}: auth failed"; break
                except RateLimitError as e:
                    last_error = f"{p.name}: rate limited"
                    if attempt == 0:
                        await asyncio.sleep(_retry_after(e))   # honour Retry-After once (cap at 5 s)
                        continue
                    break
                except (APITimeoutError, APIConnectionError):
                    last_error = f"{p.name}: network/timeout"; break
                except APIStatusError as e:
                    last_error = f"{p.name}: HTTP {e.status_code}"; break
        raise KairosError(ErrorCode.LLM_PROVIDER_UNAVAILABLE, f"All providers failed ({last_error}). Use a demo preset.", 503)
```

```python
# app/services/quote_verifier.py (core)
import unicodedata
from rapidfuzz import fuzz

_MAP = {ord(c): "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2212"} | {0x2018: "'", 0x2019: "'", 0x201C: '"', 0x201D: '"'}

def normalize_with_map(text: str) -> tuple[str, list[int]]:
    out: list[str] = []; idx: list[int] = []; prev_space = True
    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKC", ch).translate(_MAP):
            if c.isspace():
                if prev_space: continue
                c, prev_space = " ", True
            else:
                prev_space = False
            for cc in c.casefold():
                out.append(cc); idx.append(i)
    return "".join(out), idx

def verify_quote(quote: str, pages: dict[int, str], claimed_page: int, fuzzy_min: int = 92):
    """Return (true_quote, page_number) or None. true_quote is a real substring of pages[page_number]."""
    nq, _ = normalize_with_map(quote); nq = nq.strip()
    if len(nq) < 10 or "[[page" in nq or "[[section" in nq: return None
    order = sorted(pages, key=lambda p: (abs(p - claimed_page), p))
    cache = {p: normalize_with_map(pages[p]) for p in order}
    for p in order:                                   # exact pass
        nt, im = cache[p]; pos = nt.find(nq)
        if pos >= 0: return _slice(pages[p], im, pos, pos + len(nq)), p
    best = None
    for p in order:                                   # fuzzy pass
        nt, im = cache[p]; al = fuzz.partial_ratio_alignment(nq, nt)
        if al and al.score >= fuzzy_min and (best is None or al.score > best[0]):
            best = (al.score, p, im, al.dest_start, al.dest_end)
    if best: return _slice(pages[best[1]], best[2], best[3], best[4]), best[1]
    return None

def _slice(original: str, idx: list[int], start: int, end: int):
    text = original[idx[start]: idx[end - 1] + 1].strip()
    return text if 10 <= len(text) <= 600 else None
```

(`_slice` returning `None` must be handled by the caller as a failed verification. Guard against `None` before unpacking.)

### Acceptance criteria (D3)
- [ ] Prompts match `03` §3 character-for-character (a test asserts the system prompt contains the numbered rules).
- [ ] Fake-provider tests cover: success, code-fenced JSON, corrective retry, 429 fail-over, 401 disabling, timeout fail-over, all-providers-fail → `LLM_PROVIDER_UNAVAILABLE`.
- [ ] Quote verifier: exact match, whitespace/hyphenation differences, curly quotes, fuzzy repair returns a true substring, page correction, hallucinated quote dropped, markers rejected.
- [ ] A real smoke run (`python -m scripts.smoke_extract <pdf>`, optional script) extracts ≥ 4 verified claims from a real paper with a real provider; output pasted in the review bundle (redact keys).
- [ ] No API key in logs or exceptions.

### Argon 4 checklist (D3)
Prompt-injection from PDF text ("ignore previous instructions"), JSON parser robustness, semaphore/deadlock risks, retry storms, fuzzy threshold false accepts, quote length rules, provider chain edge cases, secret leakage in errors.

---

## Milestone D4 — Embeddings, pre-filter, clustering, gaps, referee

**Branch:** `feat/d4-embeddings-referee` · **Depends on:** D3

### Steps
1. `embeddings.py`: `Embedder` protocol with `embed(texts) -> np.ndarray` (L2-normalised). `FastEmbedEmbedder` (default) and `HFApiEmbedder`. Preload at startup in `main.py` (lifespan) when `EMBEDDING_BACKEND=fastembed`.
2. `similarity.py` (skeleton below): matrix, candidate pairs, gaps, clustering with the discard rules from `01-architecture.md` §4.
3. `prompts/referee.py` from `03` §5; `referee.py`: batching by `REFEREE_PAIRS_PER_CALL`, concurrent calls, validation/retry rules from `03` §5.3, produce `ClaimComparisonEdge` list.
4. `scripts/tune_threshold.py` and `tests/data/tuning_pairs.json` (≥ 30 labelled pairs from real papers, chosen by the humans); record the chosen threshold in `03` §4.1.
5. Tests: deterministic embedding stub for unit tests; cluster discard rules; gap detection before capping; cap/warning; referee parsing incl. `UNRELATED` drop and missing-pair retry.

### Key skeleton

```python
# app/services/similarity.py
import numpy as np
from sklearn.cluster import AgglomerativeClustering

def cosine_matrix(emb: np.ndarray, paper_idx: np.ndarray) -> np.ndarray:
    sim = emb @ emb.T                                   # emb is L2-normalised
    sim[paper_idx[:, None] == paper_idx[None, :]] = -1.0   # mask same-paper pairs
    return sim

def find_gaps(sim: np.ndarray, threshold: float) -> list[int]:
    return [i for i in range(sim.shape[0]) if sim[i].max() < threshold]   # BEFORE top-k and caps

def candidate_pairs(sim, paper_idx, threshold, top_k, max_pairs):
    chosen: set[tuple[int, int]] = set()
    papers = np.unique(paper_idx)
    for i in range(sim.shape[0]):
        for p in papers:
            if p == paper_idx[i]: continue
            cols = np.where(paper_idx == p)[0]
            scores = sim[i, cols]
            for o in np.argsort(-scores)[:top_k]:
                if scores[o] >= threshold:
                    j = int(cols[o]); chosen.add((min(i, j), max(i, j)))
    ordered = sorted(chosen, key=lambda ij: -sim[ij[0], ij[1]])
    return ordered[:max_pairs], len(ordered)            # (kept, total_before_cap)

def cluster_claims(emb: np.ndarray, distance_threshold: float) -> np.ndarray:
    if len(emb) < 2: return np.zeros(len(emb), dtype=int)
    return AgglomerativeClustering(n_clusters=None, metric="cosine", linkage="average",
                                   distance_threshold=distance_threshold).fit_predict(emb)
```

### Acceptance criteria (D4)
- [ ] Embeddings are L2-normalised (test: norms ≈ 1).
- [ ] Same-paper pairs never appear; pairs are unordered-unique and sorted by similarity.
- [ ] Gap detection matches the contract definition and is computed before caps (test with a tiny cap).
- [ ] Clusters have ≥ 2 claims and ≥ 2 papers; labels from the central claim's `topic_hint`.
- [ ] Referee: batches of 4, handles `UNRELATED`, missing ids (single retry), invalid labels, confidence clamping; edges follow id/ordering rules.
- [ ] Threshold tuned on ≥ 30 real pairs; chosen value + precision/recall recorded in `03` §4.1.
- [ ] Measured `pair_reduction_pct` on a real 6–8 paper set is reported in the review bundle (do not claim a number that was not measured).

### Argon 4 checklist (D4)
Numerical edge cases (N < 2, identical vectors), O(N²) memory for N ≤ 60, threshold justification, clustering instability, referee prompt injection through claim text, ordering determinism, fairness of the cap across paper pairs.

---

## Milestone D5 — Orchestration, SSE, consensus, deploy, real presets

**Branch:** `feat/d5-orchestration` · **Depends on:** D4

### Steps
1. `consensus.py`: `compute_score(edges)` per contract §6; Stage 4 call with id validation; template fallback summary.
2. `graph_builder.py`: apply id rules (contract §4), assemble `AnalysisResult` (`mode=LIVE`, `fixture_provenance=NOT_APPLICABLE`, `models[]` disclosure from the providers actually used, `warnings`).
3. `jobs.py`: `Job` with status/stage/progress, `asyncio.Queue` fan-out for SSE, last-event replay, TTL cleanup.
4. `rate_limit.py`: per-IP sliding window (`ANALYZE_RATE_LIMIT_PER_MINUTE`).
5. `pipeline.py`: orchestrate stages with the progress ranges from contract §3.5 and timing into `StageLatency`; enforce `JOB_TIMEOUT_SECONDS`.
6. `api/analyze.py`: `POST /analyze` (multipart, validation, 202 `JobCreated`), `GET /analyze/{id}`, `GET /analyze/{id}/events` (SSE via `sse-starlette`; events `progress` / `complete` / `failed`, keep-alive 15 s). Add router in `main.py`.
7. **Real presets:** humans pick real, openly licensed papers per topic and fill `fixtures/presets_manifest.json` (`preset_id`, `title`, `papers: [{arxiv_id, license, url}]`). **Do not invent arXiv ids.** Run `scripts/bake_presets.py` (calls the live pipeline) to overwrite the three preset files with `REAL_PIPELINE_OUTPUT`; then `scripts/verify_fixture_quotes.py` re-downloads each PDF and re-verifies every quote/page. Commit only manifests and outputs, **not PDFs** unless their licence allows it.
8. `Dockerfile` (build from repo root: `docker build -f backend/Dockerfile .`) and deploy to a free host (Render Docker or Hugging Face Spaces). Pre-download the embedding model during build.
9. Write `backend/README.md` (setup, env, endpoints, deploy, troubleshooting) and update `docs/AI_ASSISTANCE.md`.
10. Run a **live 8-paper end-to-end test**; record timings and the measured pair reduction in the review bundle.

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
COPY backend/requirements.txt ./requirements.txt
RUN pip install -r requirements.txt
# bake the embedding model into the image so the first request is fast
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('BAAI/bge-small-en-v1.5')"
COPY backend/app ./app
COPY fixtures ./fixtures
ENV FIXTURES_DIR=/app/fixtures
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Acceptance criteria (D5)
- [ ] `POST /analyze` with 3 real PDFs returns 202; SSE streams ordered progress to `complete`; `GET /analyze/{id}` returns a valid `AnalysisResult` (validated by `AnalysisResult.model_validate`).
- [ ] 8-paper live run completes in < 15 s on an unthrottled provider tier (report actual timings, including any rate-limit effects).
- [ ] Failure paths: invalid file, too few/many papers, provider outage (fake), job timeout → correct codes/events.
- [ ] Rate limiting returns 429 `RATE_LIMITED`.
- [ ] Consensus score formula tested; fallback summary tested; unknown ids from the LLM are discarded.
- [ ] Three presets are `REAL_PIPELINE_OUTPUT` with all quotes verified by `verify_fixture_quotes.py`; `GET /demo/{id}` < 100 ms.
- [ ] Docker image builds; container serves `/api/v1/health` and presets with **no** API keys.
- [ ] Deployed URL recorded in `docs/requests.md` for Peace (CORS origin added).
- [ ] Full `pytest` green; coverage of the pipeline happy path with fakes.

### Argon 4 checklist (D5)
Race conditions in the job store/SSE, memory growth (jobs/uploads), timeout and cancellation behaviour, secrets in logs/images, CORS, rate-limit bypass, Docker image size and startup, honesty of preset provenance and licences.

---

## Parking lot
(Agents: record out-of-scope ideas here and in `docs/requests.md`; do not implement them.)
