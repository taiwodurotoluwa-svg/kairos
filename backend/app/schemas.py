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
