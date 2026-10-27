from __future__ import annotations

from collections import defaultdict
from typing import Sequence
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from app.schemas import ExtractedClaim, ResearchGap, TopicCluster


def claim_to_embed_text(claim: ExtractedClaim) -> str:
    """Format claim for embedding: '{topic_hint}: {statement}'."""
    return f"{claim.topic_hint.strip()}: {claim.statement.strip()}"


def cosine_matrix(emb: np.ndarray, paper_idx: np.ndarray) -> np.ndarray:
    """Compute N x N cosine similarity matrix, masking same-paper pairs with -1.0.

    Args:
        emb: L2-normalised (N, D) embeddings array.
        paper_idx: 1D array of length N with integer paper identifiers.
    """
    if emb.shape[0] == 0:
        return np.empty((0, 0), dtype=np.float32)

    sim = emb @ emb.T
    # Mask same-paper pairs so they are never considered cross-paper candidates
    sim[paper_idx[:, None] == paper_idx[None, :]] = -1.0
    return sim


def find_gaps(sim: np.ndarray, threshold: float) -> list[int]:
    """Find claim indices with no cross-paper match >= threshold.

    IMPORTANT: Evaluated BEFORE top-k and max-pair caps per contract §5.
    """
    if sim.shape[0] == 0:
        return []

    gaps: list[int] = []
    for i in range(sim.shape[0]):
        max_sim = float(sim[i].max())
        if max_sim < threshold:
            gaps.append(i)
    return gaps


def build_research_gaps(
    gap_indices: Sequence[int],
    claims: Sequence[ExtractedClaim],
    sim: np.ndarray,
) -> list[ResearchGap]:
    """Construct contract-compliant ResearchGap models from gap claim indices."""
    result: list[ResearchGap] = []
    for idx in gap_indices:
        claim = claims[idx]
        max_cross_sim = float(sim[idx].max()) if sim.shape[0] > 0 else 0.0
        best_sim = max(0.0, min(1.0, max_cross_sim))
        result.append(
            ResearchGap(
                signal="RESEARCH_GAP",
                gap_id=f"gap-{claim.claim_id}",
                claim_id=claim.claim_id,
                paper_id=claim.paper_id,
                statement=claim.statement,
                provenance=claim.provenance,
                best_match_similarity=round(best_sim, 4),
                reason=f"No cross-paper claim exceeds similarity threshold (best match: {best_sim:.2f}).",
            )
        )
    return result


def candidate_pairs(
    sim: np.ndarray,
    paper_idx: np.ndarray,
    threshold: float,
    top_k: int,
    max_pairs: int,
) -> tuple[list[tuple[int, int]], int]:
    """Select cross-paper candidate pairs applying top-k per paper and similarity threshold.

    Returns:
        (kept_pairs, total_candidates_before_cap)
    """
    if sim.shape[0] < 2:
        return [], 0

    chosen: set[tuple[int, int]] = set()
    papers = np.unique(paper_idx)

    for i in range(sim.shape[0]):
        for p in papers:
            if p == paper_idx[i]:
                continue
            cols = np.where(paper_idx == p)[0]
            scores = sim[i, cols]
            # Top-k indices for this other paper
            sorted_order = np.argsort(-scores)[:top_k]
            for o in sorted_order:
                if scores[o] >= threshold:
                    j = int(cols[o])
                    chosen.add((min(i, j), max(i, j)))

    # Sort descending by cosine similarity with deterministic tie-breaking
    ordered = sorted(
        chosen,
        key=lambda ij: (-float(sim[ij[0], ij[1]]), ij[0], ij[1]),
    )
    total_candidates = len(ordered)
    return ordered[:max_pairs], total_candidates


def calculate_pair_stats(
    paper_idx: np.ndarray,
    candidate_pairs_count: int,
    evaluated_pairs_count: int,
) -> dict[str, float | int]:
    """Calculate pair reduction statistics per contract §5."""
    n = len(paper_idx)
    cross_paper_total = 0
    for i in range(n):
        for j in range(i + 1, n):
            if paper_idx[i] != paper_idx[j]:
                cross_paper_total += 1

    if cross_paper_total > 0:
        reduction_pct = round(100.0 * (1.0 - candidate_pairs_count / cross_paper_total), 1)
    else:
        reduction_pct = 0.0

    return {
        "cross_paper_pairs_total": cross_paper_total,
        "candidate_pairs": candidate_pairs_count,
        "referee_pairs_evaluated": evaluated_pairs_count,
        "pair_reduction_pct": reduction_pct,
    }


def cluster_claims(emb: np.ndarray, distance_threshold: float) -> np.ndarray:
    """Perform average linkage agglomerative clustering using cosine distance."""
    if len(emb) < 2:
        return np.zeros(len(emb), dtype=int)

    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric="cosine",
        linkage="average",
        distance_threshold=distance_threshold,
    )
    return clustering.fit_predict(emb)


def build_clusters(
    emb: np.ndarray,
    claims: Sequence[ExtractedClaim],
    distance_threshold: float,
) -> tuple[list[TopicCluster], dict[str, str | None]]:
    """Cluster claims and apply contract discard rules.

    Discard rules:
    - Clusters containing fewer than 2 claims OR fewer than 2 distinct papers are discarded.
    - Discarded claims get cluster_id = None.

    Cluster ordering:
    - Ordered by descending len(claim_ids), then ascending first claim_id.
    - Assigned cluster_id = 'cl-{k}'.
    - Label is the topic_hint of the claim closest to the cluster centroid.
    - mean_similarity is the mean pairwise cosine similarity within the cluster.
    """
    n = len(claims)
    claim_id_to_cluster: dict[str, str | None] = {c.claim_id: None for c in claims}

    if n < 2 or emb.shape[0] < 2:
        return [], claim_id_to_cluster

    raw_labels = cluster_claims(emb, distance_threshold)
    groups: dict[int, list[int]] = defaultdict(list)
    for idx, lbl in enumerate(raw_labels):
        groups[lbl].append(idx)

    candidate_clusters: list[dict] = []

    for _, indices in groups.items():
        if len(indices) < 2:
            continue

        cluster_claims_list = [claims[i] for i in indices]
        distinct_papers = sorted(list({c.paper_id for c in cluster_claims_list}))

        # Contract discard rule: cluster must span >= 2 distinct papers
        if len(distinct_papers) < 2:
            continue

        # Compute centroid and find closest claim
        sub_emb = emb[indices]
        centroid = sub_emb.mean(axis=0)
        c_norm = np.linalg.norm(centroid)
        if c_norm > 1e-12:
            centroid = centroid / c_norm

        sims_to_centroid = sub_emb @ centroid
        best_sub_idx = int(np.argmax(sims_to_centroid))
        label = cluster_claims_list[best_sub_idx].topic_hint.strip()

        # Compute mean pairwise cosine similarity
        m = len(indices)
        sub_sim = sub_emb @ sub_emb.T
        off_diag_sum = np.sum(sub_sim) - np.trace(sub_sim)
        mean_sim = float(off_diag_sum / (m * (m - 1)))
        mean_sim = max(0.0, min(1.0, mean_sim))

        claim_ids = [c.claim_id for c in cluster_claims_list]
        candidate_clusters.append(
            {
                "label": label,
                "claim_ids": claim_ids,
                "paper_ids": distinct_papers,
                "mean_sim": mean_sim,
            }
        )

    # Sort clusters: descending len(claim_ids), ascending first claim_id
    candidate_clusters.sort(key=lambda c: (-len(c["claim_ids"]), c["claim_ids"][0]))

    topic_clusters: list[TopicCluster] = []
    for k, item in enumerate(candidate_clusters, start=1):
        c_id = f"cl-{k}"
        topic_cluster = TopicCluster(
            cluster_id=c_id,
            label=item["label"],
            claim_ids=item["claim_ids"],
            paper_ids=item["paper_ids"],
            mean_similarity=round(item["mean_sim"], 4),
        )
        topic_clusters.append(topic_cluster)
        for cid in item["claim_ids"]:
            claim_id_to_cluster[cid] = c_id

    return topic_clusters, claim_id_to_cluster
