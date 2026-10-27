import json, glob
from pathlib import Path
import pytest
from app import schemas

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

def get_fixture_files():
    return list(FIXTURES_DIR.glob("*.json"))

@pytest.mark.parametrize("fixture_path", get_fixture_files(), ids=lambda p: p.name)
def test_fixture_schema_validation(fixture_path):
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = schemas.AnalysisResult.model_validate(raw)
    assert result.schema_version == schemas.SCHEMA_VERSION
    assert result.mode == schemas.AnalysisMode.DEMO
    
    # 1. Check claim paper_ids resolve
    paper_ids = {p.paper_id for p in result.papers}
    for claim in result.claims:
        assert claim.paper_id in paper_ids
        assert claim.provenance.paper_id == claim.paper_id
        
    # 2. Check cluster references
    claims_by_id = {c.claim_id: c for c in result.claims}
    for cluster in result.clusters:
        for cid in cluster.claim_ids:
            assert cid in claims_by_id
        for pid in cluster.paper_ids:
            assert pid in paper_ids
            
    # 3. Check edge references and quote parity
    edges_by_id = {}
    rel_counts = {"AGREE": 0, "CONTRADICT": 0, "METHODOLOGY_DELTA": 0}
    for edge in result.edges:
        edges_by_id[edge.edge_id] = edge
        assert edge.source_claim_id in claims_by_id
        assert edge.target_claim_id in claims_by_id
        
        # Edge quotes equal claim quotes
        s_claim = claims_by_id[edge.source_claim_id]
        t_claim = claims_by_id[edge.target_claim_id]
        assert edge.source.verbatim_quote == s_claim.provenance.verbatim_quote
        assert edge.target.verbatim_quote == t_claim.provenance.verbatim_quote
        
        # Check edge_id naming rule: "e-{source_clean}-{target_clean}"
        clean_src = edge.source_claim_id.replace("-", "")
        clean_tgt = edge.target_claim_id.replace("-", "")
        expected_eid = f"e-{clean_src}-{clean_tgt}"
        assert edge.edge_id == expected_eid
        
        rel_counts[edge.relation.value] += 1
        
    # 4. Check gap references
    gaps_by_id = {}
    for gap in result.gaps:
        gaps_by_id[gap.gap_id] = gap
        assert gap.claim_id in claims_by_id
        assert gap.paper_id in paper_ids
        assert gap.signal == "RESEARCH_GAP"
        
    # 5. Check consensus references
    for top_c in result.consensus.top_contradictions:
        assert top_c.edge_id in edges_by_id
    for gid in result.consensus.gap_ids:
        assert gid in gaps_by_id
        
    # 6. Check consensus score formula: round(100 * (A + 0.5 * D) / (A + C + D))
    a = rel_counts["AGREE"]
    c = rel_counts["CONTRADICT"]
    d = rel_counts["METHODOLOGY_DELTA"]
    total_edges = a + c + d
    if total_edges > 0:
        expected_score = round(100 * (a + 0.5 * d) / total_edges)
        assert result.consensus.consensus_score == expected_score
    else:
        assert result.consensus.consensus_score == 0
        
    # 7. Check stats arithmetic
    stats = result.stats
    assert stats.paper_count == len(result.papers)
    assert stats.claim_count == len(result.claims)
    if stats.cross_paper_pairs_total > 0:
        expected_reduction = round(100 * (1 - stats.candidate_pairs / stats.cross_paper_pairs_total), 1)
        assert abs(stats.pair_reduction_pct - expected_reduction) < 0.01
        
    # 8. Check latency breakdown sums to total_ms
    lat = stats.stage_latency_ms
    expected_total = (lat.ingestion_ms + lat.extraction_ms + lat.embedding_ms +
                      lat.clustering_ms + lat.referee_ms + lat.consensus_ms)
    assert lat.total_ms == expected_total
