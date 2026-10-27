from __future__ import annotations

import asyncio
from typing import Any
import numpy as np
import pytest

from app.schemas import (
    ClaimComparisonEdge,
    ClaimType,
    ExtractedClaim,
    PaperMetadata,
    PaperSource,
    Provenance,
    RelationType,
    SectionName,
)
from app.services.referee import (
    RawRefereeItem,
    RawRefereeOutput,
    evaluate_claim_pairs,
    format_pair_payload,
)


class MockRefereeLLMClient:
    def __init__(self, responses: list[dict | Exception]) -> None:
        self.responses = list(responses)
        self.calls: list[dict] = []
        self.last_used_model = "test-referee-model"

    async def complete_json(self, system_prompt: str, user_prompt: str, output_schema: Any = None):
        self.calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        if not self.responses:
            return RawRefereeOutput(results=[])

        resp = self.responses.pop(0)
        if isinstance(resp, Exception):
            raise resp

        if output_schema:
            return output_schema.model_validate(resp)
        return resp


def _make_paper(paper_id: str, label: str = "Author et al. (2024)") -> PaperMetadata:
    num = int("".join(c for c in paper_id if c.isdigit()) or 1)
    return PaperMetadata(
        paper_id=paper_id,
        short_label=f"P{num}",
        citation_label=label,
        palette_index=(num - 1) % 10,
        source=PaperSource.UPLOAD,
        title=f"Study on {paper_id}",
        authors=["Author One", "Author Two"],
        year=2024,
        page_count=10,
        dataset="ImageNet / ChestX-ray14",
        methodology="Deep Convolutional Network",
        primary_metric="AUROC",
        limitations="Small sample size",
        core_conclusion="Accurate diagnostics demonstrated",
        sections_found=["RESULTS"],
        extraction_model="test-model",
    )


def _make_claim(paper_id: str, claim_id: str, statement: str, cluster_id: str | None = None) -> ExtractedClaim:
    return ExtractedClaim(
        claim_id=claim_id,
        paper_id=paper_id,
        statement=statement,
        claim_type=ClaimType.EMPIRICAL_RESULT,
        topic_hint="Empirical finding",
        cluster_id=cluster_id,
        provenance=Provenance(
            paper_id=paper_id,
            paper_title=f"Study on {paper_id}",
            section=SectionName.RESULTS,
            page_number=1,
            verbatim_quote=f"Verbatim quote supporting claim {claim_id} in paper {paper_id}.",
        ),
    )


def test_format_pair_payload_numeric_paper_ordering():
    paper_map = {
        "p2": _make_paper("p2", "Beta et al. (2023)"),
        "p10": _make_paper("p10", "Kappa et al. (2025)"),
        "p1": _make_paper("p1", "Alpha et al. (2024)"),
    }
    c_p10 = _make_claim("p10", "p10-c1", "Claim from paper 10 of sufficient length.")
    c_p2 = _make_claim("p2", "p2-c1", "Claim from paper 2 of sufficient length.")

    # Paper 2 is numerically lower than Paper 10
    edge_id, src, tgt, payload = format_pair_payload(c_p10, c_p2, paper_map)
    assert edge_id == "e-p2c1-p10c1"
    assert src.claim_id == "p2-c1"
    assert tgt.claim_id == "p10-c1"
    assert payload["pair_id"] == "e-p2c1-p10c1"
    assert payload["paper_a"]["citation_label"] == "Beta et al. (2023)"
    assert payload["paper_b"]["citation_label"] == "Kappa et al. (2025)"


def test_evaluate_claim_pairs_success_and_unrelated_drop():
    p1 = _make_paper("p1")
    p2 = _make_paper("p2")
    c1 = _make_claim("p1", "p1-c1", "Statement 1 with sufficient length.")
    c2 = _make_claim("p2", "p2-c1", "Statement 2 with sufficient length.")
    c3 = _make_claim("p2", "p2-c2", "Statement 3 unrelated with sufficient length.")

    claims = [c1, c2, c3]
    papers = [p1, p2]
    sim = np.array(
        [
            [-1.0, 0.85, 0.72],
            [0.85, -1.0, -1.0],
            [0.72, -1.0, -1.0],
        ]
    )
    candidate_indices = [(0, 1), (0, 2)]

    # Mock LLM returning 1 AGREE and 1 UNRELATED
    mock_response = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c1",
                "relation": "AGREE",
                "confidence": 0.95,
                "explanation": "Both papers find consistent diagnostic improvements across datasets.",
            },
            {
                "pair_id": "e-p1c1-p2c2",
                "relation": "UNRELATED",
                "confidence": 0.90,
                "explanation": "The claims evaluate entirely distinct tasks and domains.",
            },
        ]
    }
    client = MockRefereeLLMClient([mock_response])

    edges = asyncio.run(
        evaluate_claim_pairs(
            candidate_indices=candidate_indices,
            claims=claims,
            papers=papers,
            sim=sim,
            llm_client=client,
            batch_size=4,
        )
    )

    # UNRELATED edge must be dropped
    assert len(edges) == 1
    edge = edges[0]
    assert edge.edge_id == "e-p1c1-p2c1"
    assert edge.relation == RelationType.AGREE
    assert edge.confidence == 0.95
    assert edge.cosine_similarity == 0.85
    assert edge.source_claim_id == "p1-c1"
    assert edge.target_claim_id == "p2-c1"
    assert edge.referee_model == "test-referee-model"


def test_evaluate_claim_pairs_missing_pair_retry_recovery():
    p1 = _make_paper("p1")
    p2 = _make_paper("p2")
    c1 = _make_claim("p1", "p1-c1", "Statement 1 with sufficient length.")
    c2 = _make_claim("p2", "p2-c1", "Statement 2 with sufficient length.")
    c3 = _make_claim("p2", "p2-c2", "Statement 3 with sufficient length.")

    claims = [c1, c2, c3]
    papers = [p1, p2]
    sim = np.array([[-1.0, 0.88, 0.80], [0.88, -1.0, -1.0], [0.80, -1.0, -1.0]])
    candidate_indices = [(0, 1), (0, 2)]

    # Batch response only returns pair 1 (pair 2 is missing)
    batch_resp = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c1",
                "relation": "AGREE",
                "confidence": 0.92,
                "explanation": "Both studies confirm 4-bit quantization preserves perplexity.",
            }
        ]
    }
    # Single-pair retry for pair 2
    retry_resp = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c2",
                "relation": "CONTRADICT",
                "confidence": 0.88,
                "explanation": "P1 reports accuracy gains while P2 reports significant degradation.",
            }
        ]
    }
    client = MockRefereeLLMClient([batch_resp, retry_resp])

    edges = asyncio.run(
        evaluate_claim_pairs(
            candidate_indices=candidate_indices,
            claims=claims,
            papers=papers,
            sim=sim,
            llm_client=client,
            batch_size=4,
        )
    )

    assert len(edges) == 2
    edge_ids = {e.edge_id for e in edges}
    assert edge_ids == {"e-p1c1-p2c1", "e-p1c1-p2c2"}


def test_evaluate_claim_pairs_invalid_confidence_and_unknown_relation_retry():
    p1 = _make_paper("p1")
    p2 = _make_paper("p2")
    c1 = _make_claim("p1", "p1-c1", "Statement 1 with sufficient length.")
    c2 = _make_claim("p2", "p2-c1", "Statement 2 with sufficient length.")

    claims = [c1, c2]
    papers = [p1, p2]
    sim = np.array([[-1.0, 0.85], [0.85, -1.0]])
    candidate_indices = [(0, 1)]

    # Batch response returns invalid relation
    batch_resp = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c1",
                "relation": "INVALID_RELATION",
                "confidence": 0.90,
                "explanation": "Testing invalid relation parsing.",
            }
        ]
    }
    # Single-pair retry returns valid METHODOLOGY_DELTA
    retry_resp = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c1",
                "relation": "METHODOLOGY_DELTA",
                "confidence": 0.84,
                "explanation": "Difference in hardware explains the observed inference latency delta.",
            }
        ]
    }
    client = MockRefereeLLMClient([batch_resp, retry_resp])

    edges = asyncio.run(
        evaluate_claim_pairs(
            candidate_indices=candidate_indices,
            claims=claims,
            papers=papers,
            sim=sim,
            llm_client=client,
            batch_size=4,
        )
    )

    assert len(edges) == 1
    assert edges[0].relation == RelationType.METHODOLOGY_DELTA
    assert edges[0].confidence == 0.84


def test_evaluate_claim_pairs_contract_tie_breaking_order():
    # Contract §4: Descending confidence, with CONTRADICT before METHODOLOGY_DELTA before AGREE on ties
    p1 = _make_paper("p1")
    p2 = _make_paper("p2")
    p3 = _make_paper("p3")

    c1 = _make_claim("p1", "p1-c1", "Valid statement for Claim 1 of paper 1.")
    c2 = _make_claim("p2", "p2-c1", "Valid statement for Claim 2 of paper 2.")
    c3 = _make_claim("p2", "p2-c2", "Valid statement for Claim 3 of paper 2.")
    c4 = _make_claim("p3", "p3-c1", "Valid statement for Claim 4 of paper 3.")

    claims = [c1, c2, c3, c4]
    papers = [p1, p2, p3]
    sim = np.ones((4, 4)) * 0.8
    np.fill_diagonal(sim, -1.0)
    candidate_indices = [(0, 1), (0, 2), (0, 3)]

    # Responses all with confidence 0.85, but different relations
    resp = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c1",
                "relation": "AGREE",
                "confidence": 0.85,
                "explanation": "Agreement between P1 and P2.",
            },
            {
                "pair_id": "e-p1c1-p2c2",
                "relation": "CONTRADICT",
                "confidence": 0.85,
                "explanation": "Contradiction between P1 and P2.",
            },
            {
                "pair_id": "e-p1c1-p3c1",
                "relation": "METHODOLOGY_DELTA",
                "confidence": 0.85,
                "explanation": "Methodology difference between P1 and P3.",
            },
        ]
    }
    client = MockRefereeLLMClient([resp])

    edges = asyncio.run(
        evaluate_claim_pairs(
            candidate_indices=candidate_indices,
            claims=claims,
            papers=papers,
            sim=sim,
            llm_client=client,
            batch_size=4,
        )
    )

    assert len(edges) == 3
    # Tie-break check: CONTRADICT first, then METHODOLOGY_DELTA, then AGREE
    assert edges[0].relation == RelationType.CONTRADICT
    assert edges[1].relation == RelationType.METHODOLOGY_DELTA
    assert edges[2].relation == RelationType.AGREE


def test_evaluate_claim_pairs_cluster_id_propagation_and_explanation_bounds():
    p1 = _make_paper("p1")
    p2 = _make_paper("p2")

    # Both claims in cluster cl-1
    c1 = _make_claim("p1", "p1-c1", "Valid statement for Claim 1 of paper 1.", cluster_id="cl-1")
    c2 = _make_claim("p2", "p2-c1", "Valid statement for Claim 2 of paper 2.", cluster_id="cl-1")

    claims = [c1, c2]
    papers = [p1, p2]
    sim = np.array([[-1.0, 0.90], [0.90, -1.0]])
    candidate_indices = [(0, 1)]

    long_explanation = "A" * 600
    resp = {
        "results": [
            {
                "pair_id": "e-p1c1-p2c1",
                "relation": "AGREE",
                "confidence": 0.90,
                "explanation": long_explanation,
            }
        ]
    }
    client = MockRefereeLLMClient([resp])

    edges = asyncio.run(
        evaluate_claim_pairs(
            candidate_indices=candidate_indices,
            claims=claims,
            papers=papers,
            sim=sim,
            llm_client=client,
            batch_size=4,
        )
    )

    assert len(edges) == 1
    edge = edges[0]
    # Cluster ID must be propagated when both claims share the cluster
    assert edge.cluster_id == "cl-1"
    # Explanation must be clamped to 500 characters
    assert len(edge.explanation) == 500
