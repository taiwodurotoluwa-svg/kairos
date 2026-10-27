from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
import pytest

from app.schemas import (
    AnalysisMode,
    AnalysisResult,
    AnalysisStats,
    ConsensusReport,
    ErrorCode,
    FixtureProvenance,
    JobStatus,
    PaperMetadata,
    PaperSource,
    PipelineStage,
    ProgressEvent,
    SCHEMA_VERSION,
    SectionName,
    StageLatency,
)
from app.services.jobs import JobRecord, JobStore


def _make_dummy_paper(pid: str = "p1") -> PaperMetadata:
    num = int(pid[1:]) if len(pid) > 1 and pid[1:].isdigit() else 1
    return PaperMetadata(
        paper_id=pid,
        short_label=f"P{num}",
        citation_label="Smith et al., 2024",
        palette_index=num - 1,
        source=PaperSource.UPLOAD,
        title=f"Sample Research Paper {pid}",
        authors=["Author A", "Author B"],
        year=2024,
        page_count=5,
        sections_found=[SectionName.ABSTRACT, SectionName.RESULTS],
        dataset="Benchmark A",
        methodology="Transformer",
        primary_metric="Accuracy 95%",
        limitations="Not reported",
        core_conclusion="Transformer outperforms baseline.",
        extraction_model="meta-llama/Llama-3.1-8B-Instruct",
    )


def _make_dummy_result(analysis_id: str) -> AnalysisResult:
    return AnalysisResult(
        schema_version=SCHEMA_VERSION,
        analysis_id=analysis_id,
        mode=AnalysisMode.LIVE,
        fixture_provenance=FixtureProvenance.NOT_APPLICABLE,
        generated_at=datetime.now(timezone.utc),
        papers=[_make_dummy_paper("p1"), _make_dummy_paper("p2")],
        claims=[],
        clusters=[],
        edges=[],
        gaps=[],
        consensus=ConsensusReport(
            consensus_score=75,
            executive_summary="Summary",
            agreed_findings=[],
            top_contradictions=[],
            gap_ids=[],
            recommended_next_steps=[],
        ),
        stats=AnalysisStats(
            paper_count=2,
            claim_count=4,
            cross_paper_pairs_total=4,
            candidate_pairs=4,
            referee_pairs_evaluated=4,
            referee_calls=1,
            pair_reduction_pct=0.0,
            stage_latency_ms=StageLatency(
                ingestion_ms=10,
                extraction_ms=20,
                embedding_ms=5,
                clustering_ms=5,
                referee_ms=30,
                consensus_ms=15,
                total_ms=85,
            ),
        ),
        models=[],
        warnings=[],
    )


@pytest.mark.anyio
async def test_job_store_lifecycle_and_sse_fanout():
    """Verify JobStore creation, progress updates, late subscriber replay, and completion fanout."""
    store = JobStore()
    aid = store.generate_analysis_id()
    record = store.create_job(aid)

    assert record.state.status == JobStatus.QUEUED
    assert record.state.stage == PipelineStage.INGESTION
    assert record.state.progress_pct == 0

    # Subscribe before any progress
    q1 = store.subscribe(aid)
    assert q1 is not None

    # First event received is the initial QUEUED event
    evt1 = await q1.get()
    assert evt1 is not None
    assert evt1.status == JobStatus.QUEUED

    # Publish progress
    record.publish_progress(
        stage=PipelineStage.REFEREE,
        status=JobStatus.RUNNING,
        progress_pct=80,
        message="Evaluating pairs...",
    )

    evt2 = await q1.get()
    assert evt2 is not None
    assert evt2.status == JobStatus.RUNNING
    assert evt2.stage == PipelineStage.REFEREE
    assert evt2.progress_pct == 80

    # Late subscriber subscribes: should receive replay of last event!
    q2 = store.subscribe(aid)
    assert q2 is not None
    evt_replayed = await q2.get()
    assert evt_replayed is not None
    assert evt_replayed.status == JobStatus.RUNNING
    assert evt_replayed.progress_pct == 80

    # Complete job
    dummy_result = _make_dummy_result(aid)
    record.complete(dummy_result)

    assert record.state.status == JobStatus.COMPLETED
    assert record.state.result is not None

    # Both subscribers receive complete event followed by None (end of stream)
    evt_q1_comp = await q1.get()
    assert evt_q1_comp is not None
    assert evt_q1_comp.status == JobStatus.COMPLETED
    assert evt_q1_comp.progress_pct == 100
    assert await q1.get() is None

    evt_q2_comp = await q2.get()
    assert evt_q2_comp is not None
    assert evt_q2_comp.status == JobStatus.COMPLETED
    assert await q2.get() is None

    # Unsubscribe
    store.unsubscribe(aid, q1)
    store.unsubscribe(aid, q2)
    assert len(record.subscribers) == 0


@pytest.mark.anyio
async def test_job_store_failure_and_cleanup():
    """Verify job failure handling and TTL cleanup."""
    store = JobStore()
    aid = store.generate_analysis_id()
    record = store.create_job(aid)

    q = store.subscribe(aid)
    assert q is not None
    _ = await q.get()  # initial QUEUED event

    from app.schemas import ErrorBody
    err = ErrorBody(code=ErrorCode.PDF_PARSE_FAILED, message="Corrupt PDF payload")
    record.fail(err)

    assert record.state.status == JobStatus.FAILED
    assert record.state.error is not None
    assert record.state.error.code == ErrorCode.PDF_PARSE_FAILED

    evt_failed = await q.get()
    assert evt_failed is not None
    assert evt_failed.status == JobStatus.FAILED
    assert await q.get() is None

    # TTL cleanup test
    assert store.cleanup_expired(ttl_minutes=60) == 0

    # Manually backdate created_at
    record.created_at = datetime.now(timezone.utc) - timedelta(minutes=120)
    cleaned = store.cleanup_expired(ttl_minutes=60)
    assert cleaned == 1
    assert store.get_job(aid) is None
