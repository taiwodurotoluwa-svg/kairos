from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from app.schemas import (
    ClaimComparisonEdge,
    ConsensusReport,
    ExtractedClaim,
    PaperMetadata,
    PaperSource,
    Provenance,
    RelationType,
    ResearchGap,
    SectionName,
)
from app.services.consensus import (
    compute_consensus_score,
    build_fallback_consensus,
    generate_consensus_report,
    RawConsensusOutput,
    RawContradiction,
)


def _make_dummy_edge(edge_id: str, relation: RelationType) -> ClaimComparisonEdge:
    return ClaimComparisonEdge(
        edge_id=edge_id,
        source_claim_id="p1-c1",
        target_claim_id="p2-c1",
        source=Provenance(
            paper_id="p1",
            paper_title="Sample Research Paper 1",
            section=SectionName.RESULTS,
            page_number=1,
            verbatim_quote="Method yields 95% accuracy.",
        ),
        target=Provenance(
            paper_id="p2",
            paper_title="Sample Research Paper 2",
            section=SectionName.RESULTS,
            page_number=1,
            verbatim_quote="Baseline yields 88% accuracy.",
        ),
        relation=relation,
        confidence=0.9,
        cosine_similarity=0.85,
        explanation=f"Valid explanation of the comparison for {edge_id}",
        referee_model="meta-llama/Llama-3.1-8B-Instruct",
    )


def _make_dummy_paper(pid: str = "p1") -> PaperMetadata:
    num = int(pid[1:]) if len(pid) > 1 and pid[1:].isdigit() else 1
    return PaperMetadata(
        paper_id=pid,
        short_label=f"P{num}",
        citation_label="Smith et al., 2024",
        palette_index=num - 1,
        source=PaperSource.UPLOAD,
        title="Sample Paper Title",
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


def test_compute_consensus_score_formula():
    """Verify deterministic consensus score per contract §6:
    score = 0 if A + C + D == 0
    score = round(100 * (A + 0.5 * D) / (A + C + D))
    """
    # Empty edges
    assert compute_consensus_score([]) == 0

    # All AGREE
    e_agree = [_make_dummy_edge(f"e-p1c{i}-p2c{i}", RelationType.AGREE) for i in range(5)]
    assert compute_consensus_score(e_agree) == 100

    # All CONTRADICT
    e_contra = [_make_dummy_edge(f"e-p1c{i}-p2c{i}", RelationType.CONTRADICT) for i in range(4)]
    assert compute_consensus_score(e_contra) == 0

    # All METHODOLOGY_DELTA
    e_delta = [_make_dummy_edge(f"e-p1c{i}-p2c{i}", RelationType.METHODOLOGY_DELTA) for i in range(4)]
    assert compute_consensus_score(e_delta) == 50

    # Mixed: A=3, C=1, D=2 -> total=6, 100 * (3 + 1) / 6 = 400/6 = 66.666... -> 67
    mixed = (
        [_make_dummy_edge(f"ea{i}", RelationType.AGREE) for i in range(3)]
        + [_make_dummy_edge("ec0", RelationType.CONTRADICT)]
        + [_make_dummy_edge(f"ed{i}", RelationType.METHODOLOGY_DELTA) for i in range(2)]
    )
    assert compute_consensus_score(mixed) == 67

    # Mixed: A=1, C=2, D=1 -> total=4, 100 * (1 + 0.5) / 4 = 150/4 = 37.5 -> 38
    mixed2 = (
        [_make_dummy_edge("ea0", RelationType.AGREE)]
        + [_make_dummy_edge(f"ec{i}", RelationType.CONTRADICT) for i in range(2)]
        + [_make_dummy_edge("ed0", RelationType.METHODOLOGY_DELTA)]
    )
    assert compute_consensus_score(mixed2) == 38


@pytest.mark.anyio
async def test_stage4_top_contradiction_id_filtering():
    """Verify Stage 4 LLM output strips unknown IDs or non-CONTRADICT edges."""
    edges = [
        _make_dummy_edge("e-real-contra-1", RelationType.CONTRADICT),
        _make_dummy_edge("e-real-contra-2", RelationType.CONTRADICT),
        _make_dummy_edge("e-real-agree-1", RelationType.AGREE),
    ]
    papers = [_make_dummy_paper("p1")]
    gaps = [
        ResearchGap(
            gap_id="gap-p1-c1",
            paper_id="p1",
            claim_id="p1-c1",
            statement="Isolated claim statement",
            provenance=Provenance(
                paper_id="p1",
                paper_title="Sample Research Paper 1",
                section=SectionName.RESULTS,
                page_number=1,
                verbatim_quote="Method yields 95% accuracy.",
            ),
            best_match_similarity=0.45,
            reason="No claim from another paper exceeds similarity threshold 0.70.",
        )
    ]

    mock_llm = MagicMock()
    # LLM returns 1 valid contradiction, 1 unknown edge_id, and 1 edge_id that is AGREE
    mock_llm.complete_json = AsyncMock(
        return_value=(
            RawConsensusOutput(
                executive_summary="Empirical synthesis overview.",
                agreed_findings=["Finding 1"],
                top_contradictions=[
                    RawContradiction(edge_id="e-real-contra-1", headline="Real contradiction 1"),
                    RawContradiction(edge_id="e-hallucinated-id", headline="Hallucinated contradiction"),
                    RawContradiction(edge_id="e-real-agree-1", headline="This is an agree edge not contradict!"),
                ],
                recommended_next_steps=["Step 1"],
            ),
            "groq",
            "meta-llama/Llama-3.1-8B-Instruct",
        )
    )

    report, prov, model = await generate_consensus_report(papers, edges, gaps, mock_llm)

    assert report.consensus_score == compute_consensus_score(edges)
    # Only e-real-contra-1 should be retained!
    assert len(report.top_contradictions) == 1
    assert report.top_contradictions[0].edge_id == "e-real-contra-1"
    assert report.top_contradictions[0].headline == "Real contradiction 1"
    assert report.gap_ids == ["gap-p1-c1"]
    assert prov == "groq"
    assert model == "meta-llama/Llama-3.1-8B-Instruct"


@pytest.mark.anyio
async def test_consensus_fallback_on_llm_failure():
    """Verify that when Stage 4 LLM fails, deterministic academic fallback is generated."""
    edges = [
        _make_dummy_edge("e1", RelationType.AGREE),
        _make_dummy_edge("e2", RelationType.CONTRADICT),
    ]
    papers = [_make_dummy_paper("p1")]
    gaps = [
        ResearchGap(
            gap_id="gap-p1-c1",
            paper_id="p1",
            claim_id="p1-c1",
            statement="Isolated claim statement",
            provenance=Provenance(
                paper_id="p1",
                paper_title="Sample Research Paper 1",
                section=SectionName.RESULTS,
                page_number=1,
                verbatim_quote="Method yields 95% accuracy.",
            ),
            best_match_similarity=0.45,
            reason="No claim from another paper exceeds similarity threshold 0.70.",
        )
    ]

    mock_llm = MagicMock()
    mock_llm.complete_json = AsyncMock(side_effect=RuntimeError("Provider 503 Service Unavailable"))
    mock_llm.last_used_model = "meta-llama/Llama-3.1-8B-Instruct"
    mock_llm.last_used_provider = "groq"

    report, prov, model = await generate_consensus_report(papers, edges, gaps, mock_llm)

    assert isinstance(report, ConsensusReport)
    assert report.consensus_score == 50
    assert len(report.agreed_findings) > 0
    assert len(report.top_contradictions) == 1
    assert report.top_contradictions[0].edge_id == "e2"
    assert report.gap_ids == ["gap-p1-c1"]
    assert len(report.recommended_next_steps) > 0
