from __future__ import annotations

import asyncio
import numpy as np
import pytest

from app.schemas import (
    ClaimType,
    ExtractedClaim,
    PaperMetadata,
    PaperSource,
    Provenance,
    SectionName,
)
from app.services.embeddings import DeterministicStubEmbedder, FastEmbedEmbedder
from app.services.referee import evaluate_claim_pairs
from app.services.similarity import (
    build_clusters,
    build_research_gaps,
    calculate_pair_stats,
    candidate_pairs,
    claim_to_embed_text,
    cluster_claims,
    cosine_matrix,
    find_gaps,
)


def _make_dummy_paper(paper_id: str) -> PaperMetadata:
    num = int("".join(c for c in paper_id if c.isdigit()) or 1)
    return PaperMetadata(
        paper_id=paper_id,
        short_label=f"P{num}",
        citation_label=f"Author et al. ({paper_id})",
        palette_index=(num - 1) % 10,
        source=PaperSource.UPLOAD,
        title=f"Study on {paper_id}",
        authors=["Author One"],
        year=2024,
        page_count=10,
        dataset="ImageNet / ChestX-ray14",
        methodology="Deep Learning",
        primary_metric="AUROC",
        limitations="Sample size",
        core_conclusion="Empirical evidence demonstrated",
        sections_found=["RESULTS"],
        extraction_model="test-model",
    )


def _make_dummy_claim(
    paper_id: str,
    claim_id: str,
    topic_hint: str = "Test Topic",
    statement: str = "A valid empirical statement of sufficient length.",
) -> ExtractedClaim:
    return ExtractedClaim(
        claim_id=claim_id,
        paper_id=paper_id,
        statement=statement,
        claim_type=ClaimType.EMPIRICAL_RESULT,
        topic_hint=topic_hint,
        provenance=Provenance(
            paper_id=paper_id,
            paper_title=f"Title for {paper_id}",
            section=SectionName.RESULTS,
            page_number=1,
            verbatim_quote=f"Quote for {claim_id} with sufficient length.",
        ),
    )


def test_embedder_l2_normalisation():
    stub = DeterministicStubEmbedder(dim=384)
    texts = [
        "Topic 1: Deep learning for chest X-ray detection",
        "Topic 2: 4-bit quantization reduces memory by 75%",
        "Topic 3: Frequency nadir in low-inertia microgrids",
    ]
    emb = stub.embed(texts)
    assert emb.shape == (3, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)

    empty_emb = stub.embed([])
    assert empty_emb.shape == (0, 384)


def test_fastembed_embedder_normalisation():
    embedder = FastEmbedEmbedder(model_name="BAAI/bge-small-en-v1.5")
    texts = ["Quantization perplexity", "Radiology detection"]
    emb = embedder.embed(texts)
    assert emb.shape == (2, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


def test_claim_to_embed_text():
    claim = _make_dummy_claim("p1", "p1-c1", topic_hint="  AWQ 4-bit  ", statement="  Perplexity is preserved.  ")
    formatted = claim_to_embed_text(claim)
    assert formatted == "AWQ 4-bit: Perplexity is preserved."


def test_cosine_matrix_masks_same_paper_pairs():
    # 4 claims: 2 from paper 0, 2 from paper 1
    emb = np.array(
        [
            [1.0, 0.0, 0.0],  # claim 0 (paper 0)
            [1.0, 0.0, 0.0],  # claim 1 (paper 0)
            [0.8, 0.6, 0.0],  # claim 2 (paper 1)
            [0.0, 1.0, 0.0],  # claim 3 (paper 1)
        ],
        dtype=np.float32,
    )
    paper_idx = np.array([0, 0, 1, 1], dtype=int)

    sim = cosine_matrix(emb, paper_idx)
    assert sim.shape == (4, 4)

    # Same-paper entries must be masked to -1.0
    assert sim[0, 0] == -1.0
    assert sim[0, 1] == -1.0
    assert sim[1, 0] == -1.0
    assert sim[1, 1] == -1.0
    assert sim[2, 2] == -1.0
    assert sim[2, 3] == -1.0
    assert sim[3, 2] == -1.0
    assert sim[3, 3] == -1.0

    # Cross-paper similarities must be valid dot products
    assert np.isclose(sim[0, 2], 0.8)
    assert np.isclose(sim[0, 3], 0.0)


def test_find_gaps_before_capping():
    # Claim 0 has cross-paper max = 0.40 (< threshold 0.70) -> GAP
    # Claim 1 has cross-paper max = 0.85 (>= threshold 0.70) -> NOT GAP
    # Claim 2 has cross-paper max = 0.85 (>= threshold 0.70) -> NOT GAP
    sim = np.array(
        [
            [-1.0, -1.0, 0.40],
            [-1.0, -1.0, 0.85],
            [0.40, 0.85, -1.0],
        ],
        dtype=np.float32,
    )
    threshold = 0.70
    gaps = find_gaps(sim, threshold)
    assert gaps == [0]

    # Verify build_research_gaps constructs contract-compliant models and sets is_research_gap in-place (F-02)
    claims = [
        _make_dummy_claim("p1", "p1-c1", "Isolated Topic", "A claim without peers."),
        _make_dummy_claim("p1", "p1-c2", "Shared Topic", "A claim with peers."),
        _make_dummy_claim("p2", "p2-c1", "Shared Topic", "A peer claim."),
    ]
    gap_models = build_research_gaps(gaps, claims, sim)
    assert len(gap_models) == 1
    gap = gap_models[0]
    assert gap.signal == "RESEARCH_GAP"
    assert gap.gap_id == "gap-p1-c1"
    assert gap.claim_id == "p1-c1"
    assert gap.paper_id == "p1"
    assert gap.best_match_similarity == 0.40
    assert "0.40" in gap.reason

    # In-place mutation check (F-02)
    assert claims[0].is_research_gap is True
    assert claims[1].is_research_gap is False
    assert claims[2].is_research_gap is False


def test_candidate_pairs_selection_top_k_and_capping():
    # Paper 0 has claim 0
    # Paper 1 has claims 1, 2, 3 with similarities 0.90, 0.80, 0.60
    # Threshold = 0.70, top_k = 2, max_pairs = 1
    sim = np.array(
        [
            [-1.0, 0.90, 0.80, 0.60],
            [0.90, -1.0, -1.0, -1.0],
            [0.80, -1.0, -1.0, -1.0],
            [0.60, -1.0, -1.0, -1.0],
        ],
        dtype=np.float32,
    )
    paper_idx = np.array([0, 1, 1, 1], dtype=int)

    # With top_k=2, for claim 0 we only consider top 2 of paper 1 (claims 1 and 2, similarity 0.90 and 0.80)
    # Claim 3 is at 0.60 (< 0.70 threshold)
    # Total candidates before cap should be 2: (0, 1) and (0, 2)
    # With max_pairs=1, kept should be exactly [(0, 1)]
    kept, total_before_cap = candidate_pairs(
        sim, paper_idx, threshold=0.70, top_k=2, max_pairs=1
    )
    assert total_before_cap == 2
    assert kept == [(0, 1)]

    # With max_pairs=5, both (0, 1) and (0, 2) are kept, sorted descending by similarity
    kept_all, total_all = candidate_pairs(
        sim, paper_idx, threshold=0.70, top_k=2, max_pairs=5
    )
    assert total_all == 2
    assert kept_all == [(0, 1), (0, 2)]


def test_calculate_pair_stats():
    paper_idx = np.array([0, 0, 1, 1, 2], dtype=int)
    # Total pairs: C(5, 2) = 10
    # Same paper: (0, 1) is 1, (2, 3) is 1 -> 2 same paper
    # Cross paper: 10 - 2 = 8
    stats = calculate_pair_stats(paper_idx, candidate_pairs_count=2, evaluated_pairs_count=2)
    assert stats["cross_paper_pairs_total"] == 8
    assert stats["candidate_pairs"] == 2
    assert stats["referee_pairs_evaluated"] == 2
    # reduction = 100 * (1 - 2/8) = 75.0%
    assert stats["pair_reduction_pct"] == 75.0


def test_cluster_claims_discard_rules():
    # 6 claims with embeddings
    # Cluster A: claims 0, 1 (paper p1) and claim 2 (paper p2) -> 3 claims, 2 papers -> KEEP
    # Cluster B: claims 3, 4 (both paper p2) -> 2 claims, 1 paper -> DISCARD (< 2 papers)
    # Cluster C: claim 5 (paper p3) -> 1 claim -> DISCARD (< 2 claims)
    claims = [
        _make_dummy_claim("p1", "p1-c1", "Cluster A Central", "Topic A finding 1"),
        _make_dummy_claim("p1", "p1-c2", "Cluster A Other", "Topic A finding 2"),
        _make_dummy_claim("p2", "p2-c1", "Cluster A Match", "Topic A finding 3"),
        _make_dummy_claim("p2", "p2-c2", "Cluster B One", "Topic B intra-paper 1"),
        _make_dummy_claim("p2", "p2-c3", "Cluster B Two", "Topic B intra-paper 2"),
        _make_dummy_claim("p3", "p3-c1", "Isolated", "Topic C lone claim"),
    ]

    # Synthesize orthogonal/close embeddings
    emb = np.zeros((6, 10), dtype=np.float32)
    # Cluster A vectors all close to dimension 0
    emb[0, 0] = 1.0
    emb[1, 0] = 0.98; emb[1, 1] = 0.20
    emb[2, 0] = 0.98; emb[2, 2] = 0.20
    # Cluster B vectors close to dimension 3
    emb[3, 3] = 1.0
    emb[4, 3] = 0.99; emb[4, 4] = 0.14
    # Cluster C vector on dimension 7
    emb[5, 7] = 1.0

    # L2 normalise
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    topic_clusters, claim_id_to_cluster = build_clusters(
        emb, claims, distance_threshold=0.35
    )

    # Exactly 1 valid cluster retained (Cluster A)
    assert len(topic_clusters) == 1
    c1 = topic_clusters[0]
    assert c1.cluster_id == "cl-1"
    assert set(c1.claim_ids) == {"p1-c1", "p1-c2", "p2-c1"}
    assert set(c1.paper_ids) == {"p1", "p2"}
    assert c1.label == "Cluster A Central"
    assert 0.0 <= c1.mean_similarity <= 1.0

    # In-place claim.cluster_id check (F-02)
    assert claims[0].cluster_id == "cl-1"
    assert claims[1].cluster_id == "cl-1"
    assert claims[2].cluster_id == "cl-1"
    assert claims[3].cluster_id is None
    assert claims[4].cluster_id is None
    assert claims[5].cluster_id is None


def test_cluster_paper_ids_numeric_sorting():
    """Verify that paper IDs in TopicCluster are sorted numerically, e.g. ['p2', 'p10'] not ['p10', 'p2'] (F-05)."""
    claims = [
        _make_dummy_claim("p10", "p10-c1", "Cluster Topic", "Claim from paper 10"),
        _make_dummy_claim("p2", "p2-c1", "Cluster Topic", "Claim from paper 2"),
    ]
    emb = np.array([[1.0, 0.0], [0.99, 0.05]], dtype=np.float32)
    emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)

    topic_clusters, _ = build_clusters(emb, claims, distance_threshold=0.35)
    assert len(topic_clusters) == 1
    # Numeric sorting check: p2 must appear before p10!
    assert topic_clusters[0].paper_ids == ["p2", "p10"]


def test_end_to_end_claim_mutation_invariant():
    """Verify end-to-end mutation: build_gaps -> build_clusters -> evaluate_claim_pairs propagates flags and cluster_id (F-02)."""
    p1 = _make_dummy_paper("p1")
    p2 = _make_dummy_paper("p2")

    c1 = _make_dummy_claim("p1", "p1-c1", "Topic A", "Statement 1 in cluster A from paper 1.")
    c2 = _make_dummy_claim("p2", "p2-c1", "Topic A", "Statement 2 in cluster A from paper 2.")
    c3 = _make_dummy_claim("p1", "p1-c2", "Isolated", "Isolated statement with no peers in other papers.")

    claims = [c1, c2, c3]
    papers = [p1, p2]

    # Embeddings: c1 and c2 are identical (sim = 1.0), c3 is orthogonal
    emb = np.array(
        [
            [1.0, 0.0, 0.0],
            [1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=np.float32,
    )
    paper_idx = np.array([0, 1, 0], dtype=int)
    sim = cosine_matrix(emb, paper_idx)

    # 1. build_research_gaps
    gap_indices = find_gaps(sim, threshold=0.70)
    assert gap_indices == [2]
    build_research_gaps(gap_indices, claims, sim)

    assert claims[0].is_research_gap is False
    assert claims[1].is_research_gap is False
    assert claims[2].is_research_gap is True  # Mutated in place!

    # 2. build_clusters
    topic_clusters, _ = build_clusters(emb, claims, distance_threshold=0.35)
    assert len(topic_clusters) == 1
    assert claims[0].cluster_id == "cl-1"  # Mutated in place!
    assert claims[1].cluster_id == "cl-1"  # Mutated in place!
    assert claims[2].cluster_id is None

    # 3. evaluate_claim_pairs
    class DummyMockLLM:
        last_used_model = "test-model"
        async def complete_json(self, **kwargs):
            from app.services.referee import RawRefereeOutput
            fake_json = {
                "results": [
                    {
                        "pair_id": "e-p1c1-p2c1",
                        "relation": "AGREE",
                        "confidence": 0.95,
                        "explanation": "Both claims support the same empirical finding under comparable setups.",
                    }
                ]
            }
            return RawRefereeOutput.model_validate(fake_json), "mock-provider", "test-model"

    candidate_idx, _ = candidate_pairs(sim, paper_idx, threshold=0.70, top_k=2, max_pairs=10)
    edges = asyncio.run(
        evaluate_claim_pairs(
            candidate_indices=candidate_idx,
            claims=claims,
            papers=papers,
            sim=sim,
            llm_client=DummyMockLLM(),
        )
    )

    assert len(edges) == 1
    # Edge automatically inherited the shared cluster_id!
    assert edges[0].cluster_id == "cl-1"


def test_numerical_edge_cases():
    # N = 0
    emb_empty = np.empty((0, 384), dtype=np.float32)
    paper_idx_empty = np.array([], dtype=int)
    assert cosine_matrix(emb_empty, paper_idx_empty).shape == (0, 0)
    assert find_gaps(np.empty((0, 0)), 0.70) == []
    assert candidate_pairs(np.empty((0, 0)), paper_idx_empty, 0.70, 2, 10) == ([], 0)
    clusters, mapping = build_clusters(emb_empty, [], 0.35)
    assert clusters == []
    assert mapping == {}

    # N = 1
    emb_single = np.ones((1, 384), dtype=np.float32) / np.sqrt(384)
    paper_idx_single = np.array([0], dtype=int)
    sim_single = cosine_matrix(emb_single, paper_idx_single)
    assert sim_single[0, 0] == -1.0
    assert find_gaps(sim_single, 0.70) == [0]
    assert candidate_pairs(sim_single, paper_idx_single, 0.70, 2, 10) == ([], 0)
    claim_single = _make_dummy_claim("p1", "p1-c1")
    clusters_single, mapping_single = build_clusters(emb_single, [claim_single], 0.35)
    assert clusters_single == []
    assert mapping_single == {"p1-c1": None}
