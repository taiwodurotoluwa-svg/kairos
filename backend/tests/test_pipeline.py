from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np
import pytest

from app.config import Settings
from app.errors import KairosError
from app.schemas import (
    AnalysisMode,
    AnalysisResult,
    ClaimType,
    ErrorCode,
    ExtractedClaim,
    JobStatus,
    PaperMetadata,
    PaperSource,
    PipelineStage,
    Provenance,
    RelationType,
    SectionName,
)
from app.services.embeddings import DeterministicStubEmbedder
from app.services.ingestion.models import IngestedBatch, SectionedPaper
from app.services.jobs import JobStore
from app.services.pipeline import run_pipeline


def _make_dummy_sectioned_paper(pid: str) -> SectionedPaper:
    return SectionedPaper(
        paper_id=pid,
        title=f"Sample Research Paper {pid}",
        text_for_llm=f"Full text content for paper {pid}. Findings: Method yields 95% accuracy.",
        sections_found=[SectionName.ABSTRACT, SectionName.RESULTS],
        page_texts={1: f"Full text content for paper {pid}. Findings: Method yields 95% accuracy."},
        page_count=1,
        source=PaperSource.UPLOAD,
        filename=f"{pid}.pdf",
    )


@pytest.mark.anyio
async def test_pipeline_happy_path_mocked():
    """Verify complete 5-stage synthesis pipeline happy path with fakes."""
    settings = Settings(
        groq_api_key="gsk-test",
        similarity_threshold=0.60,
        max_referee_pairs=20,
        referee_pairs_per_call=4,
        job_timeout_seconds=30,
        embedding_backend="fastembed",
    )
    store = JobStore()
    aid = store.generate_analysis_id()
    record = store.create_job(aid)

    # Mock ingestion
    mock_batch = IngestedBatch(
        papers=[
            _make_dummy_sectioned_paper("p1"),
            _make_dummy_sectioned_paper("p2"),
        ],
        warnings=["Test ingestion warning"],
    )

    # Mock extraction return values with full PaperMetadata
    p1_meta = PaperMetadata(
        paper_id="p1",
        short_label="P1",
        citation_label="Smith et al., 2024",
        palette_index=0,
        source=PaperSource.UPLOAD,
        title="Sample Research Paper p1",
        authors=["Smith, J.", "Doe, A."],
        year=2024,
        page_count=1,
        sections_found=[SectionName.ABSTRACT, SectionName.RESULTS],
        dataset="Benchmark A",
        sample_size="n=500",
        methodology="Transformer",
        primary_metric="Accuracy 95%",
        limitations="Not evaluated on out-of-distribution data.",
        core_conclusion="Transformer architecture demonstrates high accuracy.",
        extraction_model="meta-llama/Llama-3.1-8B-Instruct",
    )
    p1_claims = [
        ExtractedClaim(
            claim_id="p1-c1",
            paper_id="p1",
            claim_type=ClaimType.EMPIRICAL_RESULT,
            statement="Method achieves 95% accuracy on benchmark A.",
            topic_hint="model accuracy",
            provenance=Provenance(
                paper_id="p1",
                paper_title="Sample Research Paper p1",
                section=SectionName.RESULTS,
                page_number=1,
                verbatim_quote="Method yields 95% accuracy.",
            ),
        )
    ]

    p2_meta = PaperMetadata(
        paper_id="p2",
        short_label="P2",
        citation_label="Jones et al., 2024",
        palette_index=1,
        source=PaperSource.UPLOAD,
        title="Sample Research Paper p2",
        authors=["Jones, M."],
        year=2024,
        page_count=1,
        sections_found=[SectionName.ABSTRACT, SectionName.RESULTS],
        dataset="Benchmark B",
        sample_size="n=300",
        methodology="CNN",
        primary_metric="Accuracy 88%",
        limitations="Small sample size.",
        core_conclusion="CNN baseline is computationally efficient.",
        extraction_model="meta-llama/Llama-3.1-8B-Instruct",
    )
    p2_claims = [
        ExtractedClaim(
            claim_id="p2-c1",
            paper_id="p2",
            claim_type=ClaimType.EMPIRICAL_RESULT,
            statement="CNN baseline yields 88% accuracy on benchmark B.",
            topic_hint="baseline performance",
            provenance=Provenance(
                paper_id="p2",
                paper_title="Sample Research Paper p2",
                section=SectionName.RESULTS,
                page_number=1,
                verbatim_quote="Findings: Method yields 95% accuracy.",
            ),
        )
    ]

    async def mock_extract(sec_paper, llm_client, settings=None):
        if sec_paper.paper_id == "p1":
            return p1_meta, p1_claims, []
        return p2_meta, p2_claims, []

    embedder = DeterministicStubEmbedder(dim=384)

    mock_llm = MagicMock()
    mock_llm.last_used_model = "meta-llama/Llama-3.1-8B-Instruct"
    mock_llm.last_used_provider = "groq"
    mock_llm.call_count = 0

    with patch("app.services.pipeline.ingest_all", AsyncMock(return_value=mock_batch)), \
         patch("app.services.pipeline.extract_claims_from_paper", side_effect=mock_extract):

        result = await run_pipeline(
            analysis_id=aid,
            raw_files=[("p1.pdf", b"%PDF-1.4 test"), ("p2.pdf", b"%PDF-1.4 test2")],
            arxiv_ids=[],
            job_store=store,
            settings=settings,
            llm_client=mock_llm,
            embedder=embedder,
        )

    # Validations
    assert isinstance(result, AnalysisResult)
    assert result.analysis_id == aid
    assert result.mode == AnalysisMode.LIVE
    assert len(result.papers) == 2
    assert len(result.claims) == 2
    assert len(result.models) == 4
    assert result.stats.paper_count == 2
    assert result.stats.claim_count == 2
    assert result.stats.stage_latency_ms.total_ms >= 0

    # Pydantic contract validation
    validated = AnalysisResult.model_validate(result.model_dump())
    assert validated.analysis_id == aid

    # Check job state in store
    rec = store.get_job(aid)
    assert rec is not None
    assert rec.state.status == JobStatus.COMPLETED
    assert rec.state.progress_pct == 100
    assert rec.state.result is not None


@pytest.mark.anyio
async def test_pipeline_timeout_handling():
    """Verify job timeout enforces 504 and marks job FAILED."""
    settings = Settings(
        groq_api_key="gsk-test",
        job_timeout_seconds=1,  # Short 1-second timeout
    )
    store = JobStore()
    aid = store.generate_analysis_id()
    store.create_job(aid)

    # Mock ingest_all to hang for 3 seconds
    async def slow_ingest(*args, **kwargs):
        await asyncio.sleep(3)
        return IngestedBatch(papers=[], warnings=[])

    with patch("app.services.pipeline.ingest_all", side_effect=slow_ingest):
        with pytest.raises(KairosError) as exc_info:
            await run_pipeline(
                analysis_id=aid,
                raw_files=[("p1.pdf", b"%PDF-1.4 test"), ("p2.pdf", b"%PDF-1.4 test2")],
                arxiv_ids=[],
                job_store=store,
                settings=settings,
            )

        err = exc_info.value
        assert err.status_code == 504
        assert err.code == ErrorCode.INTERNAL_ERROR

    # Check job in store is marked FAILED
    rec = store.get_job(aid)
    assert rec is not None
    assert rec.state.status == JobStatus.FAILED
    assert rec.state.error is not None
    assert rec.state.error.code == ErrorCode.INTERNAL_ERROR
