from __future__ import annotations

import io
from unittest.mock import patch
from datetime import datetime, timezone
from fastapi.testclient import TestClient
import pytest

from app.main import app
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
    SCHEMA_VERSION,
    SectionName,
    StageLatency,
)
from app.services.jobs import get_job_store
from app.services.rate_limit import get_rate_limiter

client = TestClient(app)


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


def _make_dummy_analysis_result(aid: str) -> AnalysisResult:
    return AnalysisResult(
        schema_version=SCHEMA_VERSION,
        analysis_id=aid,
        mode=AnalysisMode.LIVE,
        fixture_provenance=FixtureProvenance.NOT_APPLICABLE,
        generated_at=datetime.now(timezone.utc),
        papers=[_make_dummy_paper("p1"), _make_dummy_paper("p2")],
        claims=[],
        clusters=[],
        edges=[],
        gaps=[],
        consensus=ConsensusReport(
            consensus_score=80,
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


def test_submit_analysis_validation_errors():
    get_rate_limiter().reset()

    # 1. Too few papers (only 1 PDF)
    files = [("files", ("paper1.pdf", b"%PDF-1.4 test", "application/pdf"))]
    res = client.post("/api/v1/analyze", files=files)
    assert res.status_code == 400
    assert res.json()["error"]["code"] == ErrorCode.TOO_FEW_PAPERS.value

    # 2. Invalid file type (text file instead of PDF)
    files_invalid = [
        ("files", ("paper1.txt", b"plain text content", "text/plain")),
        ("files", ("paper2.pdf", b"%PDF-1.4 test", "application/pdf")),
    ]
    res_inv = client.post("/api/v1/analyze", files=files_invalid)
    assert res_inv.status_code == 400
    assert res_inv.json()["error"]["code"] == ErrorCode.INVALID_FILE_TYPE.value


def test_submit_analysis_rate_limiting():
    get_rate_limiter().reset()
    limiter = get_rate_limiter()
    limiter.limit = 2  # Set low limit for testing

    files = [
        ("files", ("paper1.pdf", b"%PDF-1.4 test1", "application/pdf")),
        ("files", ("paper2.pdf", b"%PDF-1.4 test2", "application/pdf")),
    ]

    with patch("app.api.analyze.run_pipeline"):
        res1 = client.post("/api/v1/analyze", files=files)
        assert res1.status_code == 202

        res2 = client.post("/api/v1/analyze", files=files)
        assert res2.status_code == 202

        # 3rd request should hit 429 RATE_LIMITED
        res3 = client.post("/api/v1/analyze", files=files)
        assert res3.status_code == 429
        assert res3.json()["error"]["code"] == ErrorCode.RATE_LIMITED.value

    limiter.reset()


def test_submit_analysis_happy_path_202():
    get_rate_limiter().reset()
    files = [
        ("files", ("p1.pdf", b"%PDF-1.4 sample content 1", "application/pdf")),
        ("files", ("p2.pdf", b"%PDF-1.4 sample content 2", "application/pdf")),
    ]

    with patch("app.api.analyze.run_pipeline"):
        res = client.post("/api/v1/analyze", files=files)
        assert res.status_code == 202
        data = res.json()
        assert "analysis_id" in data
        assert data["status"] == "QUEUED"
        assert data["events_url"].startswith("/api/v1/analyze/")
        assert data["result_url"].startswith("/api/v1/analyze/")


def test_get_analysis_status_and_result():
    store = get_job_store()
    aid = store.generate_analysis_id()

    # 1. Non-existent job
    res_404 = client.get("/api/v1/analyze/ana-unknown-123")
    assert res_404.status_code == 404
    assert res_404.json()["error"]["code"] == ErrorCode.ANALYSIS_NOT_FOUND.value

    # 2. Queued / Running job
    rec = store.create_job(aid)
    rec.publish_progress(
        stage=PipelineStage.REFEREE,
        status=JobStatus.RUNNING,
        progress_pct=85,
        message="Evaluating referee pairs...",
    )
    res_running = client.get(f"/api/v1/analyze/{aid}")
    assert res_running.status_code == 200
    state = res_running.json()
    assert state["status"] == "RUNNING"
    assert state["stage"] == "REFEREE"
    assert state["progress_pct"] == 85

    # 3. Completed job
    dummy_res = _make_dummy_analysis_result(aid)
    rec.complete(dummy_res)
    res_complete = client.get(f"/api/v1/analyze/{aid}")
    assert res_complete.status_code == 200
    comp_data = res_complete.json()
    assert comp_data["analysis_id"] == aid
    assert comp_data["mode"] == "LIVE"
    assert comp_data["consensus"]["consensus_score"] == 80


def test_stream_events_sse_unknown_job():
    res = client.get("/api/v1/analyze/ana-nonexistent/events")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == ErrorCode.ANALYSIS_NOT_FOUND.value
