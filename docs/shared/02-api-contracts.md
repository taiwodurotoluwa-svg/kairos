# 02 — API Contracts (Single Source of Truth)

> **Backend Lead:** Durotoluwa Taiwo (`@taiwodurotoluwa-svg`). **Frontend Lead:** Oluwanifemi Ojewusi (`@Peaceyy28`).
> **Schema version:** `1.0.0`. Any schema change requires a synchronized `schema_version` update in `backend/app/schemas.py` and `frontend/js/api.js`.

## 0. Conventions (read before anything else)

1. **JSON keys are `snake_case` everywhere** (Python, wire format, and TypeScript). The frontend MUST NOT convert to camelCase.
2. **Enums are `UPPER_SNAKE_CASE` strings.** They are identical in Python and TypeScript. Never invent new values on one side only.
3. **Every claim and every edge carries a `Provenance`** object (`paper_id`, `paper_title`, `section`, `page_number`, `verbatim_quote`). No exceptions. The backend drops any claim whose quote cannot be verified against the source PDF text (see `03-open-weight-models.md` §6).
4. **Pydantic models use `extra="forbid"`.** Unknown keys are validation errors. Fixtures must match exactly.
5. **Four semantic signals** are bound to enums and must stay visually distinct in the UI: `AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA` (edge relations) and `RESEARCH_GAP` (the `signal` field of a `ResearchGap`).
6. **Fixtures are honest.** Every `AnalysisResult` has `fixture_provenance`:
   - `SYNTHETIC_PLACEHOLDER` — invented data used only to unblock development. The UI MUST show a visible "Synthetic placeholder data" banner. Never shown at Demo Day.
   - `REAL_PIPELINE_OUTPUT` — produced by running the real pipeline on real, openly licensed papers, with quotes verified. Only these may be used at Demo Day.
   - `NOT_APPLICABLE` — live analysis of user-supplied papers.
7. **Limits:** min 2 papers, max 10 papers, max 20 MB per PDF, max 80 MB per request. Demo presets contain 6–8 papers.

---

## 1. Pydantic v2 models (Python 3.11+)

Canonical Pydantic v2 contract implemented in `backend/app/schemas.py`. A validation script in the repo (`backend/tests/test_contract.py`) loads `fixtures/contract_sample.json` through `AnalysisResult` on every test run.

```python
# backend/app/schemas.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

SCHEMA_VERSION = "1.0.0"


class ContractModel(BaseModel):
    """Base class: unknown keys are rejected so fixtures and API never drift."""

    model_config = ConfigDict(extra="forbid", use_enum_values=False)


# ----------------------------------------------------------------------------
# Enums
# ----------------------------------------------------------------------------
class RelationType(str, Enum):
    AGREE = "AGREE"
    CONTRADICT = "CONTRADICT"
    METHODOLOGY_DELTA = "METHODOLOGY_DELTA"


class SectionName(str, Enum):
    ABSTRACT = "ABSTRACT"
    METHODOLOGY = "METHODOLOGY"
    EXPERIMENTAL_SETUP = "EXPERIMENTAL_SETUP"
    RESULTS = "RESULTS"
    DISCUSSION = "DISCUSSION"
    CONCLUSION = "CONCLUSION"
    LIMITATIONS = "LIMITATIONS"
    OTHER = "OTHER"


class PaperSource(str, Enum):
    UPLOAD = "UPLOAD"
    ARXIV = "ARXIV"
    DEMO = "DEMO"


class ClaimType(str, Enum):
    EMPIRICAL_RESULT = "EMPIRICAL_RESULT"
    METHOD = "METHOD"
    LIMITATION = "LIMITATION"
    CONCLUSION = "CONCLUSION"


class AnalysisMode(str, Enum):
    LIVE = "LIVE"
    DEMO = "DEMO"


class FixtureProvenance(str, Enum):
    SYNTHETIC_PLACEHOLDER = "SYNTHETIC_PLACEHOLDER"
    REAL_PIPELINE_OUTPUT = "REAL_PIPELINE_OUTPUT"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ModelRole(str, Enum):
    EXTRACTION = "EXTRACTION"
    EMBEDDING = "EMBEDDING"
    REFEREE = "REFEREE"
    CONSENSUS_WRITER = "CONSENSUS_WRITER"


class PipelineStage(str, Enum):
    INGESTION = "INGESTION"
    EXTRACTION = "EXTRACTION"
    EMBEDDING = "EMBEDDING"
    CLUSTERING = "CLUSTERING"
    REFEREE = "REFEREE"
    CONSENSUS = "CONSENSUS"
    DONE = "DONE"


class JobStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ErrorCode(str, Enum):
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    TOO_FEW_PAPERS = "TOO_FEW_PAPERS"
    TOO_MANY_PAPERS = "TOO_MANY_PAPERS"
    INVALID_ARXIV_ID = "INVALID_ARXIV_ID"
    ARXIV_FETCH_FAILED = "ARXIV_FETCH_FAILED"
    PDF_PARSE_FAILED = "PDF_PARSE_FAILED"
    NO_TEXT_LAYER = "NO_TEXT_LAYER"
    LLM_PROVIDER_UNAVAILABLE = "LLM_PROVIDER_UNAVAILABLE"
    LLM_INVALID_JSON = "LLM_INVALID_JSON"
    ANALYSIS_NOT_FOUND = "ANALYSIS_NOT_FOUND"
    PRESET_NOT_FOUND = "PRESET_NOT_FOUND"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# ----------------------------------------------------------------------------
# Core data models
# ----------------------------------------------------------------------------
class Provenance(ContractModel):
    paper_id: str
    paper_title: str
    section: SectionName
    page_number: int = Field(ge=1)
    verbatim_quote: str = Field(min_length=10, max_length=600)


class PaperMetadata(ContractModel):
    paper_id: str = Field(pattern=r"^p[0-9]{1,2}$")  # "p1".."p10", stable order of upload
    short_label: str = Field(pattern=r"^P[0-9]{1,2}$")  # "P1".."P10"
    citation_label: str  # e.g. "Smith et al. (2024)"; "Example A (2024)" in placeholders
    palette_index: int = Field(ge=0, le=9)  # index into the 10-colour paper palette
    source: PaperSource
    arxiv_id: Optional[str] = None
    filename: Optional[str] = None
    title: str
    authors: list[str]
    year: Optional[int] = Field(default=None, ge=1900, le=2100)
    page_count: int = Field(ge=1)
    sections_found: list[SectionName]
    dataset: str  # "Not reported" when absent
    sample_size: Optional[str] = None  # free text, e.g. "n=1,200 scans"
    methodology: str
    primary_metric: str
    limitations: str
    core_conclusion: str
    extraction_model: str


class ExtractedClaim(ContractModel):
    claim_id: str  # "{paper_id}-c{n}", e.g. "p3-c2"
    paper_id: str
    claim_type: ClaimType
    topic_hint: str = Field(max_length=80)  # short topic phrase from the extractor
    statement: str = Field(min_length=10, max_length=300)
    metric_value: Optional[str] = None  # e.g. "94.2% accuracy"
    cluster_id: Optional[str] = None  # None when unclustered
    is_research_gap: bool = False
    provenance: Provenance


class TopicCluster(ContractModel):
    cluster_id: str  # "cl-1", "cl-2", ...
    label: str  # topic_hint of the claim closest to the cluster centroid
    claim_ids: list[str] = Field(min_length=2)
    paper_ids: list[str] = Field(min_length=2)
    mean_similarity: float = Field(ge=0.0, le=1.0)


class ClaimComparisonEdge(ContractModel):
    edge_id: str  # "e-{source_claim_id without dash}-{target_claim_id without dash}"
    source_claim_id: str  # claim from the lower-numbered paper
    target_claim_id: str
    source: Provenance
    target: Provenance
    relation: RelationType
    confidence: float = Field(ge=0.0, le=1.0)
    cosine_similarity: float = Field(ge=0.0, le=1.0)
    explanation: str = Field(min_length=10, max_length=500)
    cluster_id: Optional[str] = None
    referee_model: str


class ResearchGap(ContractModel):
    signal: Literal["RESEARCH_GAP"] = "RESEARCH_GAP"
    gap_id: str  # "gap-{claim_id}"
    claim_id: str
    paper_id: str
    statement: str
    provenance: Provenance
    best_match_similarity: float = Field(ge=0.0, le=1.0)
    reason: str


class TopContradiction(ContractModel):
    edge_id: str
    headline: str = Field(max_length=200)


class ConsensusReport(ContractModel):
    consensus_score: int = Field(ge=0, le=100)  # computed deterministically, see §6
    executive_summary: str = Field(max_length=1200)
    agreed_findings: list[str]
    top_contradictions: list[TopContradiction]
    gap_ids: list[str]
    recommended_next_steps: list[str]


class StageLatency(ContractModel):
    ingestion_ms: int = Field(ge=0)
    extraction_ms: int = Field(ge=0)
    embedding_ms: int = Field(ge=0)
    clustering_ms: int = Field(ge=0)
    referee_ms: int = Field(ge=0)
    consensus_ms: int = Field(ge=0)
    total_ms: int = Field(ge=0)


class AnalysisStats(ContractModel):
    paper_count: int = Field(ge=0)
    claim_count: int = Field(ge=0)
    cross_paper_pairs_total: int = Field(ge=0)  # claim pairs from different papers
    candidate_pairs: int = Field(ge=0)  # pairs surviving the cosine pre-filter
    referee_pairs_evaluated: int = Field(ge=0)  # after MAX_REFEREE_PAIRS cap
    referee_calls: int = Field(ge=0)  # LLM calls actually made (pairs are batched)
    pair_reduction_pct: float = Field(ge=0.0, le=100.0)
    stage_latency_ms: StageLatency


class ModelDisclosure(ContractModel):
    role: ModelRole
    model_id: str
    provider: str  # "groq" | "huggingface" | "ollama" | "fastembed-local" | "hf-inference-api"
    license: str
    license_url: str
    parameter_count: str


class AnalysisResult(ContractModel):
    schema_version: str = SCHEMA_VERSION
    analysis_id: str
    mode: AnalysisMode
    preset_id: Optional[str] = None
    fixture_provenance: FixtureProvenance
    generated_at: datetime
    papers: list[PaperMetadata] = Field(min_length=2, max_length=10)
    claims: list[ExtractedClaim]
    clusters: list[TopicCluster]
    edges: list[ClaimComparisonEdge]
    gaps: list[ResearchGap]
    consensus: ConsensusReport
    stats: AnalysisStats
    models: list[ModelDisclosure]
    warnings: list[str] = []


# ----------------------------------------------------------------------------
# Job / transport models
# ----------------------------------------------------------------------------
class ErrorBody(ContractModel):
    code: ErrorCode
    message: str
    details: Optional[dict] = None


class ErrorResponse(ContractModel):
    error: ErrorBody


class ProgressEvent(ContractModel):
    analysis_id: str
    stage: PipelineStage
    status: JobStatus
    progress_pct: int = Field(ge=0, le=100)
    message: str
    timestamp: datetime


class JobCreated(ContractModel):
    analysis_id: str
    status: JobStatus
    events_url: str  # "/api/v1/analyze/{analysis_id}/events"
    result_url: str  # "/api/v1/analyze/{analysis_id}"


class JobState(ContractModel):
    analysis_id: str
    status: JobStatus
    stage: PipelineStage
    progress_pct: int = Field(ge=0, le=100)
    error: Optional[ErrorBody] = None
    result: Optional[AnalysisResult] = None  # populated only when status == COMPLETED


class DemoPresetSummary(ContractModel):
    preset_id: str  # "radiology" | "llm_quantization" | "microgrids" | "contract_sample"
    title: str
    description: str
    domain: str
    paper_count: int
    fixture_provenance: FixtureProvenance


class ProviderHealth(ContractModel):
    configured: bool
    model_id: Optional[str] = None


class HealthResponse(ContractModel):
    status: Literal["ok", "degraded"]
    version: str
    schema_version: str
    providers: dict[str, ProviderHealth]  # keys: groq, huggingface, ollama
    embedding_backend: str
    presets_loaded: list[str]
```

---

## 2. TypeScript interfaces

Copy verbatim into `frontend/src/lib/types.ts` (Milestone P1). Field names, optionality and enum values mirror §1 exactly.

```ts
// frontend/src/lib/types.ts
export const SCHEMA_VERSION = "1.0.0" as const;

export type RelationType = "AGREE" | "CONTRADICT" | "METHODOLOGY_DELTA";
export type SemanticSignal = RelationType | "RESEARCH_GAP";

export type SectionName =
  | "ABSTRACT"
  | "METHODOLOGY"
  | "EXPERIMENTAL_SETUP"
  | "RESULTS"
  | "DISCUSSION"
  | "CONCLUSION"
  | "LIMITATIONS"
  | "OTHER";

export type PaperSource = "UPLOAD" | "ARXIV" | "DEMO";
export type ClaimType = "EMPIRICAL_RESULT" | "METHOD" | "LIMITATION" | "CONCLUSION";
export type AnalysisMode = "LIVE" | "DEMO";
export type FixtureProvenance = "SYNTHETIC_PLACEHOLDER" | "REAL_PIPELINE_OUTPUT" | "NOT_APPLICABLE";
export type ModelRole = "EXTRACTION" | "EMBEDDING" | "REFEREE" | "CONSENSUS_WRITER";
export type PipelineStage =
  | "INGESTION"
  | "EXTRACTION"
  | "EMBEDDING"
  | "CLUSTERING"
  | "REFEREE"
  | "CONSENSUS"
  | "DONE";
export type JobStatus = "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED";
export type ErrorCode =
  | "INVALID_FILE_TYPE"
  | "FILE_TOO_LARGE"
  | "TOO_FEW_PAPERS"
  | "TOO_MANY_PAPERS"
  | "INVALID_ARXIV_ID"
  | "ARXIV_FETCH_FAILED"
  | "PDF_PARSE_FAILED"
  | "NO_TEXT_LAYER"
  | "LLM_PROVIDER_UNAVAILABLE"
  | "LLM_INVALID_JSON"
  | "ANALYSIS_NOT_FOUND"
  | "PRESET_NOT_FOUND"
  | "RATE_LIMITED"
  | "INTERNAL_ERROR";

export interface Provenance {
  paper_id: string;
  paper_title: string;
  section: SectionName;
  page_number: number; // >= 1
  verbatim_quote: string; // 10..600 chars
}

export interface PaperMetadata {
  paper_id: string; // "p1".."p10"
  short_label: string; // "P1".."P10"
  citation_label: string;
  palette_index: number; // 0..9
  source: PaperSource;
  arxiv_id: string | null;
  filename: string | null;
  title: string;
  authors: string[];
  year: number | null;
  page_count: number;
  sections_found: SectionName[];
  dataset: string;
  sample_size: string | null;
  methodology: string;
  primary_metric: string;
  limitations: string;
  core_conclusion: string;
  extraction_model: string;
}

export interface ExtractedClaim {
  claim_id: string; // "p3-c2"
  paper_id: string;
  claim_type: ClaimType;
  topic_hint: string;
  statement: string;
  metric_value: string | null;
  cluster_id: string | null;
  is_research_gap: boolean;
  provenance: Provenance;
}

export interface TopicCluster {
  cluster_id: string; // "cl-1"
  label: string;
  claim_ids: string[];
  paper_ids: string[];
  mean_similarity: number; // 0..1
}

export interface ClaimComparisonEdge {
  edge_id: string;
  source_claim_id: string;
  target_claim_id: string;
  source: Provenance;
  target: Provenance;
  relation: RelationType;
  confidence: number; // 0..1
  cosine_similarity: number; // 0..1
  explanation: string;
  cluster_id: string | null;
  referee_model: string;
}

export interface ResearchGap {
  signal: "RESEARCH_GAP";
  gap_id: string;
  claim_id: string;
  paper_id: string;
  statement: string;
  provenance: Provenance;
  best_match_similarity: number;
  reason: string;
}

export interface TopContradiction {
  edge_id: string;
  headline: string;
}

export interface ConsensusReport {
  consensus_score: number; // 0..100
  executive_summary: string;
  agreed_findings: string[];
  top_contradictions: TopContradiction[];
  gap_ids: string[];
  recommended_next_steps: string[];
}

export interface StageLatency {
  ingestion_ms: number;
  extraction_ms: number;
  embedding_ms: number;
  clustering_ms: number;
  referee_ms: number;
  consensus_ms: number;
  total_ms: number;
}

export interface AnalysisStats {
  paper_count: number;
  claim_count: number;
  cross_paper_pairs_total: number;
  candidate_pairs: number;
  referee_pairs_evaluated: number;
  referee_calls: number;
  pair_reduction_pct: number;
  stage_latency_ms: StageLatency;
}

export interface ModelDisclosure {
  role: ModelRole;
  model_id: string;
  provider: string;
  license: string;
  license_url: string;
  parameter_count: string;
}

export interface AnalysisResult {
  schema_version: string;
  analysis_id: string;
  mode: AnalysisMode;
  preset_id: string | null;
  fixture_provenance: FixtureProvenance;
  generated_at: string; // ISO-8601 UTC
  papers: PaperMetadata[]; // 2..10
  claims: ExtractedClaim[];
  clusters: TopicCluster[];
  edges: ClaimComparisonEdge[];
  gaps: ResearchGap[];
  consensus: ConsensusReport;
  stats: AnalysisStats;
  models: ModelDisclosure[];
  warnings: string[];
}

export interface ErrorBody {
  code: ErrorCode;
  message: string;
  details: Record<string, unknown> | null;
}

export interface ErrorResponse {
  error: ErrorBody;
}

export interface ProgressEvent {
  analysis_id: string;
  stage: PipelineStage;
  status: JobStatus;
  progress_pct: number; // 0..100
  message: string;
  timestamp: string; // ISO-8601 UTC
}

export interface JobCreated {
  analysis_id: string;
  status: JobStatus;
  events_url: string;
  result_url: string;
}

export interface JobState {
  analysis_id: string;
  status: JobStatus;
  stage: PipelineStage;
  progress_pct: number;
  error: ErrorBody | null;
  result: AnalysisResult | null;
}

export interface DemoPresetSummary {
  preset_id: string;
  title: string;
  description: string;
  domain: string;
  paper_count: number;
  fixture_provenance: FixtureProvenance;
}

export interface ProviderHealth {
  configured: boolean;
  model_id: string | null;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  version: string;
  schema_version: string;
  providers: Record<string, ProviderHealth>;
  embedding_backend: string;
  presets_loaded: string[];
}
```

> **Serialization note (backend):** FastAPI must serialize with `response_model_exclude_none=False` so optional fields appear as `null` (the TypeScript types above declare `T | null`, not `T | undefined`). Datetimes serialize as ISO-8601 UTC with a trailing `Z`.

---

## 3. REST endpoints

Base path: `/api/v1`. All responses are `application/json` unless stated. CORS allows the origins listed in `CORS_ALLOW_ORIGINS`.

### 3.1 `GET /api/v1/health`
- **200** → `HealthResponse`. `status` is `"degraded"` when no LLM provider is configured **and** Ollama is unreachable; presets still work in that state.

### 3.2 `GET /api/v1/demo`
- **200** → `DemoPresetSummary[]`. Always includes `contract_sample` until real presets replace it; at Demo Day the list contains exactly `radiology`, `llm_quantization`, `microgrids` (all `REAL_PIPELINE_OUTPUT`).

### 3.3 `GET /api/v1/demo/{preset_id}`
- **200** → `AnalysisResult` read from `fixtures/{preset_id}.json` (no network calls, target < 100 ms).
- **404** → `ErrorResponse` with `PRESET_NOT_FOUND`.

### 3.4 `POST /api/v1/analyze`
Starts an analysis job. `Content-Type: multipart/form-data`.

| Field | Type | Required | Notes |
| :--- | :--- | :--- | :--- |
| `files` | file[] (repeatable) | no | PDFs only (`application/pdf`, `.pdf`). |
| `arxiv_ids` | string (JSON array encoded as a string) | no | e.g. `["2401.01234","https://arxiv.org/abs/2305.14314v2"]`. Accepts bare ids, `abs`/`pdf` URLs, old-style ids (`cs.CL/0501001`). |

- Total papers (`files` + `arxiv_ids`, after de-duplication) MUST be 2–10.
- **202** → `JobCreated`.
- **400** → `ErrorResponse`: `INVALID_FILE_TYPE`, `TOO_FEW_PAPERS`, `TOO_MANY_PAPERS`, `INVALID_ARXIV_ID`.
- **413** → `ErrorResponse`: `FILE_TOO_LARGE`.
- **429** → `ErrorResponse`: `RATE_LIMITED` (per-IP limit `ANALYZE_RATE_LIMIT_PER_MINUTE`, default 6).

### 3.5 `GET /api/v1/analyze/{analysis_id}/events`
Server-Sent Events (`Content-Type: text/event-stream`). Each event:

```
event: progress
data: {"analysis_id":"a1b2","stage":"EXTRACTION","status":"RUNNING","progress_pct":35,"message":"Extracting claims from paper 3 of 8","timestamp":"2026-10-28T10:15:03Z"}

```

Event names: `progress` (payload `ProgressEvent`), `complete` (payload `ProgressEvent` with `stage="DONE"`, `status="COMPLETED"`, `progress_pct=100`), `failed` (payload `ErrorResponse`). The stream closes after `complete` or `failed`. A `: keep-alive` comment line is sent every 15 s. If the job already finished when the client connects, the server immediately emits the terminal event.

Stage → progress ranges: `INGESTION` 0–15, `EXTRACTION` 15–55, `EMBEDDING` 55–62, `CLUSTERING` 62–68, `REFEREE` 68–90, `CONSENSUS` 90–99, `DONE` 100.

### 3.6 `GET /api/v1/analyze/{analysis_id}`
- **200** → `JobState` (`result` populated only when `status == "COMPLETED"`).
- **404** → `ErrorResponse` with `ANALYSIS_NOT_FOUND`.
- Jobs are kept in memory for `JOB_TTL_MINUTES` (default 60).

### 3.7 Error semantics
All non-2xx bodies are `ErrorResponse`. Failures that happen *inside* a running job are delivered via the SSE `failed` event and `JobState.error`, never as HTTP errors.

| Code | HTTP | Meaning |
| :--- | :--- | :--- |
| `INVALID_FILE_TYPE` | 400 | Non-PDF upload (checked by magic bytes `%PDF-`, not only extension). |
| `FILE_TOO_LARGE` | 413 | A file exceeds `MAX_FILE_MB` or the request exceeds `MAX_TOTAL_MB`. |
| `TOO_FEW_PAPERS` | 400 | Fewer than 2 papers after de-duplication. |
| `TOO_MANY_PAPERS` | 400 | More than 10 papers. |
| `INVALID_ARXIV_ID` | 400 | An `arxiv_ids` entry cannot be normalised. |
| `ARXIV_FETCH_FAILED` | job | arXiv PDF download failed (timeout, 404, non-PDF response). |
| `PDF_PARSE_FAILED` | job | PyMuPDF could not open the file. |
| `NO_TEXT_LAYER` | job | PDF is scanned (fewer than 200 extractable characters per page on average). OCR is out of scope. |
| `LLM_PROVIDER_UNAVAILABLE` | job | Every provider in `LLM_PROVIDER_CHAIN` failed. |
| `LLM_INVALID_JSON` | job | Model output was not valid after `LLM_MAX_RETRIES` retries. |
| `ANALYSIS_NOT_FOUND` | 404 | Unknown or expired `analysis_id`. |
| `PRESET_NOT_FOUND` | 404 | Unknown `preset_id`. |
| `RATE_LIMITED` | 429 | Too many analyze requests. |
| `INTERNAL_ERROR` | 500 | Unhandled exception (message is generic; details only in server logs). |

A paper that fails individually (e.g. `NO_TEXT_LAYER`) does **not** fail the whole job if at least 2 papers remain: it is skipped and an explanatory string is appended to `AnalysisResult.warnings`.

---

## 4. Identifier and ordering rules

| Item | Rule |
| :--- | :--- |
| `paper_id` | `p{n}` in submission order (uploads first in the order received, then arXiv ids). `short_label = P{n}`; `palette_index = n-1`. |
| `claim_id` | `{paper_id}-c{k}`, `k` starting at 1 in extraction order, e.g. `p3-c2`. |
| `cluster_id` | `cl-{k}`, `k` starting at 1, ordered by descending `len(claim_ids)` then ascending first `claim_id`. |
| `edge_id` | `e-` + `source_claim_id` + `-` + `target_claim_id` with dashes removed inside each claim id, e.g. `e-p1c2-p2c2`. The source is always the claim from the lower-numbered paper. |
| `gap_id` | `gap-{claim_id}`. |
| Edge ordering | Descending `confidence`, with `CONTRADICT` before `METHODOLOGY_DELTA` before `AGREE` on ties. |

---

## 5. Pre-filter and gap semantics (shared understanding)

- `cross_paper_pairs_total` = number of claim pairs whose `paper_id` values differ.
- `candidate_pairs` = pairs with cosine similarity `>= SIMILARITY_THRESHOLD` after keeping at most `TOP_K_PER_PAPER` neighbours per claim per other paper.
- `referee_pairs_evaluated` = `min(candidate_pairs, MAX_REFEREE_PAIRS)`; truncation keeps the highest-similarity pairs and adds a string to `warnings`.
- `pair_reduction_pct = round(100 * (1 - candidate_pairs / cross_paper_pairs_total), 1)` (0.0 when the denominator is 0).
- A claim is a **research gap** when it has **no** cross-paper neighbour with cosine similarity `>= SIMILARITY_THRESHOLD`, evaluated **before** the `TOP_K` and `MAX_REFEREE_PAIRS` caps. `best_match_similarity` is its highest cross-paper similarity.

## 6. Consensus score (deterministic, not LLM-generated)

Let `A`, `C`, `D` be the counts of `AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA` edges.

```
consensus_score = 0                      if A + C + D == 0
consensus_score = round(100 * (A + 0.5 * D) / (A + C + D))   otherwise
```

The LLM writes only the prose fields (`executive_summary`, `agreed_findings`, `top_contradictions[].headline`, `recommended_next_steps`). Every `edge_id` / `gap_id` it returns is validated against the real lists; unknown ids are discarded.

---

## 7. Complete sample payload

This is the exact content of [`fixtures/contract_sample.json`](../../fixtures/contract_sample.json). It is **synthetic** (`fixture_provenance = "SYNTHETIC_PLACEHOLDER"`) and exists only to illustrate the contract and unblock the frontend. It is valid against the Pydantic models in §1.

```json
{
  "schema_version": "1.0.0",
  "analysis_id": "demo-contract_sample",
  "mode": "DEMO",
  "preset_id": "contract_sample",
  "fixture_provenance": "SYNTHETIC_PLACEHOLDER",
  "generated_at": "2026-10-26T21:00:00Z",
  "papers": [
    {
      "paper_id": "p1",
      "short_label": "P1",
      "citation_label": "Example A (2024)",
      "palette_index": 0,
      "source": "DEMO",
      "arxiv_id": null,
      "filename": "example_paper_a.pdf",
      "title": "Example Paper A: 4-bit Quantization Preserves Instruction-Following",
      "authors": ["Example Author A"],
      "year": 2024,
      "page_count": 12,
      "sections_found": ["ABSTRACT", "METHODOLOGY", "RESULTS", "CONCLUSION"],
      "dataset": "MMLU 5-shot and Alpaca-Eval (synthetic placeholder)",
      "sample_size": "n=14,042 MMLU questions",
      "methodology": "GPTQ 4-bit weight-only quantization of a 7B decoder model",
      "primary_metric": "MMLU accuracy drop of 0.8 points vs FP16",
      "limitations": "English-only evaluation; context length up to 2k tokens",
      "core_conclusion": "4-bit weight-only quantization preserves accuracy within one point.",
      "extraction_model": "meta-llama/Llama-3.1-8B-Instruct"
    },
    {
      "paper_id": "p2",
      "short_label": "P2",
      "citation_label": "Example B (2025)",
      "palette_index": 1,
      "source": "DEMO",
      "arxiv_id": null,
      "filename": "example_paper_b.pdf",
      "title": "Example Paper B: Quantization Degrades Long-Context Reasoning",
      "authors": ["Example Author B", "Example Author C"],
      "year": 2025,
      "page_count": 14,
      "sections_found": ["ABSTRACT", "EXPERIMENTAL_SETUP", "RESULTS", "CONCLUSION"],
      "dataset": "LongBench subset (synthetic placeholder)",
      "sample_size": "n=3,750 long-context prompts",
      "methodology": "AWQ 4-bit quantization evaluated at 32k context",
      "primary_metric": "Average LongBench score drop of 7.9 points",
      "limitations": "Single model family; no calibration ablation",
      "core_conclusion": "Quantization materially degrades long-context reasoning.",
      "extraction_model": "meta-llama/Llama-3.1-8B-Instruct"
    },
    {
      "paper_id": "p3",
      "short_label": "P3",
      "citation_label": "Example C (2025)",
      "palette_index": 2,
      "source": "DEMO",
      "arxiv_id": null,
      "filename": "example_paper_c.pdf",
      "title": "Example Paper C: Calibration Data Explains Quantization Variance",
      "authors": ["Example Author D"],
      "year": 2025,
      "page_count": 10,
      "sections_found": ["ABSTRACT", "METHODOLOGY", "RESULTS", "LIMITATIONS", "CONCLUSION"],
      "dataset": "MMLU and LongBench with three calibration corpora (synthetic placeholder)",
      "sample_size": "3 calibration sets x 2 benchmarks",
      "methodology": "GPTQ 4-bit with varied calibration corpora",
      "primary_metric": "Up to 6.1 point accuracy variance across calibration sets",
      "limitations": "English-only calibration corpora",
      "core_conclusion": "Calibration choice, not bit-width alone, drives accuracy variance.",
      "extraction_model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  ],
  "claims": [
    {
      "claim_id": "p1-c1",
      "paper_id": "p1",
      "claim_type": "EMPIRICAL_RESULT",
      "topic_hint": "short-context accuracy",
      "statement": "4-bit GPTQ loses under one point of MMLU accuracy versus FP16.",
      "metric_value": "0.8 points",
      "cluster_id": "cl-1",
      "is_research_gap": false,
      "provenance": {
        "paper_id": "p1",
        "paper_title": "Example Paper A: 4-bit Quantization Preserves Instruction-Following",
        "section": "RESULTS",
        "page_number": 6,
        "verbatim_quote": "4-bit GPTQ quantization reduced MMLU accuracy by only 0.8 points relative to the FP16 baseline."
      }
    },
    {
      "claim_id": "p1-c2",
      "paper_id": "p1",
      "claim_type": "CONCLUSION",
      "topic_hint": "deployment recommendation",
      "statement": "4-bit weight-only quantization is safe for general-purpose deployment.",
      "metric_value": null,
      "cluster_id": "cl-2",
      "is_research_gap": false,
      "provenance": {
        "paper_id": "p1",
        "paper_title": "Example Paper A: 4-bit Quantization Preserves Instruction-Following",
        "section": "CONCLUSION",
        "page_number": 9,
        "verbatim_quote": "We conclude that 4-bit weight-only quantization is safe for general-purpose deployment."
      }
    },
    {
      "claim_id": "p2-c1",
      "paper_id": "p2",
      "claim_type": "EMPIRICAL_RESULT",
      "topic_hint": "long-context accuracy",
      "statement": "AWQ 4-bit loses 7.9 LongBench points at 32k context.",
      "metric_value": "7.9 points",
      "cluster_id": "cl-1",
      "is_research_gap": false,
      "provenance": {
        "paper_id": "p2",
        "paper_title": "Example Paper B: Quantization Degrades Long-Context Reasoning",
        "section": "RESULTS",
        "page_number": 7,
        "verbatim_quote": "At 32k context, AWQ 4-bit models lost 7.9 points on average on LongBench."
      }
    },
    {
      "claim_id": "p2-c2",
      "paper_id": "p2",
      "claim_type": "CONCLUSION",
      "topic_hint": "deployment recommendation",
      "statement": "4-bit quantization is not safe to assume for long-context deployment.",
      "metric_value": null,
      "cluster_id": "cl-2",
      "is_research_gap": false,
      "provenance": {
        "paper_id": "p2",
        "paper_title": "Example Paper B: Quantization Degrades Long-Context Reasoning",
        "section": "CONCLUSION",
        "page_number": 10,
        "verbatim_quote": "4-bit quantization should not be assumed safe for long-context deployment."
      }
    },
    {
      "claim_id": "p3-c1",
      "paper_id": "p3",
      "claim_type": "EMPIRICAL_RESULT",
      "topic_hint": "calibration sensitivity",
      "statement": "LongBench accuracy varies by up to 6.1 points depending on the calibration corpus.",
      "metric_value": "6.1 points",
      "cluster_id": "cl-1",
      "is_research_gap": false,
      "provenance": {
        "paper_id": "p3",
        "paper_title": "Example Paper C: Calibration Data Explains Quantization Variance",
        "section": "RESULTS",
        "page_number": 5,
        "verbatim_quote": "Switching the calibration corpus changed LongBench accuracy by up to 6.1 points at identical bit-width."
      }
    },
    {
      "claim_id": "p3-c2",
      "paper_id": "p3",
      "claim_type": "LIMITATION",
      "topic_hint": "multilingual coverage",
      "statement": "Only English calibration corpora were tested, so multilingual behavior is untested.",
      "metric_value": null,
      "cluster_id": null,
      "is_research_gap": true,
      "provenance": {
        "paper_id": "p3",
        "paper_title": "Example Paper C: Calibration Data Explains Quantization Variance",
        "section": "LIMITATIONS",
        "page_number": 8,
        "verbatim_quote": "All calibration corpora in this study were English-only; multilingual behavior is untested."
      }
    }
  ],
  "clusters": [
    {
      "cluster_id": "cl-1",
      "label": "Accuracy impact of 4-bit quantization",
      "claim_ids": ["p1-c1", "p2-c1", "p3-c1"],
      "paper_ids": ["p1", "p2", "p3"],
      "mean_similarity": 0.72
    },
    {
      "cluster_id": "cl-2",
      "label": "Deployment safety of 4-bit quantization",
      "claim_ids": ["p1-c2", "p2-c2"],
      "paper_ids": ["p1", "p2"],
      "mean_similarity": 0.91
    }
  ],
  "edges": [
    {
      "edge_id": "e-p1c1-p2c1",
      "source_claim_id": "p1-c1",
      "target_claim_id": "p2-c1",
      "source": {
        "paper_id": "p1",
        "paper_title": "Example Paper A: 4-bit Quantization Preserves Instruction-Following",
        "section": "RESULTS",
        "page_number": 6,
        "verbatim_quote": "4-bit GPTQ quantization reduced MMLU accuracy by only 0.8 points relative to the FP16 baseline."
      },
      "target": {
        "paper_id": "p2",
        "paper_title": "Example Paper B: Quantization Degrades Long-Context Reasoning",
        "section": "RESULTS",
        "page_number": 7,
        "verbatim_quote": "At 32k context, AWQ 4-bit models lost 7.9 points on average on LongBench."
      },
      "relation": "METHODOLOGY_DELTA",
      "confidence": 0.86,
      "cosine_similarity": 0.78,
      "explanation": "Example A (2024) measured short-context MMLU with GPTQ while Example B (2025) measured 32k-context LongBench with AWQ, so the 0.8 vs 7.9 point gaps reflect different benchmarks, context lengths and quantizers rather than a true conflict.",
      "cluster_id": "cl-1",
      "referee_model": "meta-llama/Llama-3.1-8B-Instruct"
    },
    {
      "edge_id": "e-p1c2-p2c2",
      "source_claim_id": "p1-c2",
      "target_claim_id": "p2-c2",
      "source": {
        "paper_id": "p1",
        "paper_title": "Example Paper A: 4-bit Quantization Preserves Instruction-Following",
        "section": "CONCLUSION",
        "page_number": 9,
        "verbatim_quote": "We conclude that 4-bit weight-only quantization is safe for general-purpose deployment."
      },
      "target": {
        "paper_id": "p2",
        "paper_title": "Example Paper B: Quantization Degrades Long-Context Reasoning",
        "section": "CONCLUSION",
        "page_number": 10,
        "verbatim_quote": "4-bit quantization should not be assumed safe for long-context deployment."
      },
      "relation": "CONTRADICT",
      "confidence": 0.93,
      "cosine_similarity": 0.91,
      "explanation": "Example A (2024) concludes 4-bit quantization is safe for general deployment while Example B (2025) warns it should not be assumed safe for long-context deployment; both answer the same deployment-safety question with opposite recommendations.",
      "cluster_id": "cl-2",
      "referee_model": "meta-llama/Llama-3.1-8B-Instruct"
    },
    {
      "edge_id": "e-p2c1-p3c1",
      "source_claim_id": "p2-c1",
      "target_claim_id": "p3-c1",
      "source": {
        "paper_id": "p2",
        "paper_title": "Example Paper B: Quantization Degrades Long-Context Reasoning",
        "section": "RESULTS",
        "page_number": 7,
        "verbatim_quote": "At 32k context, AWQ 4-bit models lost 7.9 points on average on LongBench."
      },
      "target": {
        "paper_id": "p3",
        "paper_title": "Example Paper C: Calibration Data Explains Quantization Variance",
        "section": "RESULTS",
        "page_number": 5,
        "verbatim_quote": "Switching the calibration corpus changed LongBench accuracy by up to 6.1 points at identical bit-width."
      },
      "relation": "AGREE",
      "confidence": 0.74,
      "cosine_similarity": 0.71,
      "explanation": "Example B (2025) and Example C (2025) both report multi-point LongBench score changes tied to 4-bit quantization setup, consistent with long-context accuracy being sensitive to quantization choices.",
      "cluster_id": "cl-1",
      "referee_model": "meta-llama/Llama-3.1-8B-Instruct"
    }
  ],
  "gaps": [
    {
      "signal": "RESEARCH_GAP",
      "gap_id": "gap-p3-c2",
      "claim_id": "p3-c2",
      "paper_id": "p3",
      "statement": "Only English calibration corpora were tested, so multilingual behavior is untested.",
      "provenance": {
        "paper_id": "p3",
        "paper_title": "Example Paper C: Calibration Data Explains Quantization Variance",
        "section": "LIMITATIONS",
        "page_number": 8,
        "verbatim_quote": "All calibration corpora in this study were English-only; multilingual behavior is untested."
      },
      "best_match_similarity": 0.41,
      "reason": "No claim in any other uploaded paper addresses multilingual quantization behavior (best cross-paper cosine similarity 0.41 is below the 0.65 threshold)."
    }
  ],
  "consensus": {
    "consensus_score": 50,
    "executive_summary": "The three papers agree that 4-bit quantization changes accuracy by a measurable amount, but they disagree on how safe it is. Example A (2024) finds negligible loss on short-context MMLU and calls 4-bit safe; Example B (2025) finds a 7.9 point LongBench drop at 32k context and warns against assuming safety. Example C (2025) suggests calibration data explains much of the variance. Multilingual behavior is untested in every paper.",
    "agreed_findings": [
      "Long-context accuracy is sensitive to 4-bit quantization choices (Example B 2025, Example C 2025)."
    ],
    "top_contradictions": [
      {
        "edge_id": "e-p1c2-p2c2",
        "headline": "Is 4-bit quantization safe to deploy? Example A says yes, Example B says not for long context."
      }
    ],
    "gap_ids": ["gap-p3-c2"],
    "recommended_next_steps": [
      "Re-run Example A's short-context benchmark at 32k context with the same quantizer.",
      "Repeat Example B's evaluation with multiple calibration corpora as in Example C.",
      "Add multilingual calibration and evaluation sets."
    ]
  },
  "stats": {
    "paper_count": 3,
    "claim_count": 6,
    "cross_paper_pairs_total": 12,
    "candidate_pairs": 3,
    "referee_pairs_evaluated": 3,
    "referee_calls": 1,
    "pair_reduction_pct": 75.0,
    "stage_latency_ms": {
      "ingestion_ms": 410,
      "extraction_ms": 3120,
      "embedding_ms": 38,
      "clustering_ms": 6,
      "referee_ms": 1480,
      "consensus_ms": 1210,
      "total_ms": 6264
    }
  },
  "models": [
    {
      "role": "EXTRACTION",
      "model_id": "meta-llama/Llama-3.1-8B-Instruct",
      "provider": "groq",
      "license": "Llama 3.1 Community License",
      "license_url": "https://www.llama.com/llama3_1/license/",
      "parameter_count": "8B"
    },
    {
      "role": "EMBEDDING",
      "model_id": "BAAI/bge-small-en-v1.5",
      "provider": "fastembed-local",
      "license": "MIT",
      "license_url": "https://huggingface.co/BAAI/bge-small-en-v1.5",
      "parameter_count": "33M"
    },
    {
      "role": "REFEREE",
      "model_id": "meta-llama/Llama-3.1-8B-Instruct",
      "provider": "groq",
      "license": "Llama 3.1 Community License",
      "license_url": "https://www.llama.com/llama3_1/license/",
      "parameter_count": "8B"
    },
    {
      "role": "CONSENSUS_WRITER",
      "model_id": "meta-llama/Llama-3.1-8B-Instruct",
      "provider": "groq",
      "license": "Llama 3.1 Community License",
      "license_url": "https://www.llama.com/llama3_1/license/",
      "parameter_count": "8B"
    }
  ],
  "warnings": [
    "SYNTHETIC_PLACEHOLDER: this payload is invented to illustrate the contract. Do not present it as real research."
  ]
}

```
