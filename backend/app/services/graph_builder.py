from __future__ import annotations

from datetime import datetime, timezone
from typing import Sequence

from app.schemas import (
    SCHEMA_VERSION,
    AnalysisMode,
    AnalysisResult,
    AnalysisStats,
    ClaimComparisonEdge,
    ConsensusReport,
    ExtractedClaim,
    FixtureProvenance,
    ModelDisclosure,
    ModelRole,
    PaperMetadata,
    ResearchGap,
    StageLatency,
    TopicCluster,
)


def _resolve_model_metadata(model_id: str, provider: str) -> tuple[str, str, str]:
    """Resolve license, license_url, and parameter_count for standard open-weight models."""
    lowered = model_id.lower()
    if "bge-small" in lowered:
        return "MIT", "https://huggingface.co/BAAI/bge-small-en-v1.5/blob/main/LICENSE", "33M"
    if "llama-3.2-3b" in lowered or "llama3.2:3b" in lowered or "3.2-3b" in lowered:
        return "Llama 3.2 Community License", "https://llama.meta.com/llama3/license/", "3B"
    if "qwen" in lowered:
        return "Apache-2.0", "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/blob/main/LICENSE", "7B"
    # Default to Llama-3.1-8B metadata
    return "Meta Llama 3.1 Community License", "https://llama.meta.com/llama3/license/", "8B"


def build_model_disclosures(
    extraction_model: str = "llama-3.1-8b-instant",
    extraction_provider: str = "groq",
    embedding_model: str = "BAAI/bge-small-en-v1.5",
    embedding_provider: str = "fastembed-local",
    referee_model: str = "llama-3.1-8b-instant",
    referee_provider: str = "groq",
    consensus_model: str = "llama-3.1-8b-instant",
    consensus_provider: str = "groq",
) -> list[ModelDisclosure]:
    """Build ModelDisclosure entries for the 4 pipeline model roles."""
    roles_info = [
        (ModelRole.EXTRACTION, extraction_model, extraction_provider),
        (ModelRole.EMBEDDING, embedding_model, embedding_provider),
        (ModelRole.REFEREE, referee_model, referee_provider),
        (ModelRole.CONSENSUS_WRITER, consensus_model, consensus_provider),
    ]

    disclosures: list[ModelDisclosure] = []
    for role, m_id, prov in roles_info:
        lic, lic_url, params = _resolve_model_metadata(m_id, prov)
        disclosures.append(
            ModelDisclosure(
                role=role,
                model_id=m_id,
                provider=prov,
                license=lic,
                license_url=lic_url,
                parameter_count=params,
            )
        )
    return disclosures


def build_analysis_result(
    analysis_id: str,
    papers: Sequence[PaperMetadata],
    claims: Sequence[ExtractedClaim],
    clusters: Sequence[TopicCluster],
    edges: Sequence[ClaimComparisonEdge],
    gaps: Sequence[ResearchGap],
    consensus: ConsensusReport,
    cross_paper_pairs_total: int,
    candidate_pairs_count: int,
    referee_pairs_evaluated: int,
    referee_calls: int,
    pair_reduction_pct: float,
    stage_latencies: StageLatency,
    models: Sequence[ModelDisclosure],
    warnings: Sequence[str] | None = None,
    mode: AnalysisMode = AnalysisMode.LIVE,
    preset_id: str | None = None,
    fixture_provenance: FixtureProvenance = FixtureProvenance.NOT_APPLICABLE,
) -> AnalysisResult:
    """Construct and validate contract-compliant AnalysisResult."""
    stats = AnalysisStats(
        paper_count=len(papers),
        claim_count=len(claims),
        cross_paper_pairs_total=cross_paper_pairs_total,
        candidate_pairs=candidate_pairs_count,
        referee_pairs_evaluated=referee_pairs_evaluated,
        referee_calls=referee_calls,
        pair_reduction_pct=pair_reduction_pct,
        stage_latency_ms=stage_latencies,
    )

    final_warnings = list(warnings or [])

    return AnalysisResult(
        schema_version=SCHEMA_VERSION,
        analysis_id=analysis_id,
        mode=mode,
        preset_id=preset_id,
        fixture_provenance=fixture_provenance,
        generated_at=datetime.now(timezone.utc),
        papers=list(papers),
        claims=list(claims),
        clusters=list(clusters),
        edges=list(edges),
        gaps=list(gaps),
        consensus=consensus,
        stats=stats,
        models=list(models),
        warnings=final_warnings,
    )
