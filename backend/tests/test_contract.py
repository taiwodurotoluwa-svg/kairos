import json, glob, re
from pathlib import Path
import pytest
from app import schemas

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "fixtures"

APPROVED_OPEN_WEIGHT_MODELS = {
    "llama-3.1-8b-instant",
    "meta-llama/Llama-3.1-8B-Instruct",
    "Qwen/Qwen2.5-7B-Instruct",
    "qwen/qwen3.8-27b",
    "llama3.2:3b",
    "BAAI/bge-small-en-v1.5",
}


def get_fixture_files():
    return [p for p in FIXTURES_DIR.glob("*.json") if p.name != "presets_manifest.json"]


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


@pytest.mark.parametrize("fixture_path", get_fixture_files(), ids=lambda p: p.name)
def test_deep_referential_and_provenance_invariants(fixture_path):
    """Enforces Argon 4 invariants: full provenance object equality, lower-numbered paper ordering, gap invariants."""
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = schemas.AnalysisResult.model_validate(raw)
    claims_by_id = {c.claim_id: c for c in result.claims}

    for edge in result.edges:
        s_claim = claims_by_id[edge.source_claim_id]
        t_claim = claims_by_id[edge.target_claim_id]

        # Full provenance object identity
        assert edge.source.model_dump() == s_claim.provenance.model_dump()
        assert edge.target.model_dump() == t_claim.provenance.model_dump()

        # Strict ordering: source must be from lower-numbered paper than target
        s_num = int(re.match(r"^p([0-9]+)", s_claim.paper_id).group(1))
        t_num = int(re.match(r"^p([0-9]+)", t_claim.paper_id).group(1))
        assert s_num < t_num, f"Edge {edge.edge_id} has invalid paper ordering p{s_num} >= p{t_num}"

    for gap in result.gaps:
        claim = claims_by_id[gap.claim_id]
        assert claim.is_research_gap is True, f"Claim {gap.claim_id} pointed by gap must have is_research_gap=True"
        assert gap.gap_id == f"gap-{gap.claim_id}"
        assert gap.provenance.model_dump() == claim.provenance.model_dump()


@pytest.mark.parametrize("fixture_path", get_fixture_files(), ids=lambda p: p.name)
def test_open_weight_models_and_synthetic_provenance(fixture_path):
    """Enforces Rule 1 (Open-weight models only) and Rule 4 (Synthetic fixture labeling)."""
    raw = json.loads(fixture_path.read_text(encoding="utf-8"))
    result = schemas.AnalysisResult.model_validate(raw)

    assert result.fixture_provenance == schemas.FixtureProvenance.SYNTHETIC_PLACEHOLDER

    assert len(result.models) >= 2, "Every preset must disclose at least LLM and embedding models"
    for m in result.models:
        assert m.model_id in APPROVED_OPEN_WEIGHT_MODELS, f"Forbidden non-open model found: {m.model_id}"
        assert bool(m.license.strip()), f"Model {m.model_id} must have non-empty open-weight license"
        assert m.parameter_count is not None

def test_presets_manifest_valid():
    """Validate fixtures/presets_manifest.json structure and alignment with demo.py."""
    manifest_path = FIXTURES_DIR / "presets_manifest.json"
    assert manifest_path.exists(), "presets_manifest.json must exist in fixtures/"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "presets" in data and len(data["presets"]) >= 3
    from app.api.demo import PRESETS

    for item in data["presets"]:
        pid = item.get("preset_id")
        assert pid in PRESETS, f"Unknown preset_id in manifest: {pid}"
        assert item.get("title"), f"Missing title in preset {pid}"
        papers = item.get("papers", [])
        assert len(papers) >= 2, f"Preset {pid} must have >= 2 papers"
        for p in papers:
            assert re.match(r"^\d{4}\.\d{4,5}$", p.get("arxiv_id", "")), f"Invalid arXiv ID: {p.get('arxiv_id')}"
            assert "license" in p and "CC" in p["license"]
            assert p.get("url", "").startswith("https://arxiv.org/abs/")

