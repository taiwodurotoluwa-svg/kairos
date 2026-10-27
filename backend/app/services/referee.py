from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Sequence
import numpy as np
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.config import Settings, get_settings
from app.schemas import (
    ClaimComparisonEdge,
    ExtractedClaim,
    PaperMetadata,
    RelationType,
)
from app.services.llm.client import LLMClient
from app.services.prompts.referee import (
    REFEREE_SYSTEM_PROMPT,
    REFEREE_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger("kairos.referee")

VALID_RELATIONS = {"AGREE", "CONTRADICT", "METHODOLOGY_DELTA", "UNRELATED"}


class RawRefereeItem(BaseModel):
    model_config = ConfigDict(extra="ignore")

    pair_id: str
    relation: str = ""
    confidence: float | None = None
    explanation: str = ""

    @field_validator("relation", mode="before")
    @classmethod
    def clean_relation(cls, v: Any) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return ""

    @field_validator("confidence", mode="before")
    @classmethod
    def clean_confidence(cls, v: Any) -> float | None:
        if v is None:
            return None
        try:
            val = float(v)
            return max(0.0, min(1.0, val))
        except (ValueError, TypeError):
            return None


class RawRefereeOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")

    results: list[RawRefereeItem] = Field(default_factory=list)


def _get_paper_num(paper_id: str) -> int:
    """Extract numeric suffix from paper_id (e.g. 'p3' -> 3)."""
    digits = "".join(c for c in paper_id if c.isdigit())
    return int(digits) if digits else 0


def format_pair_payload(
    claim_a: ExtractedClaim,
    claim_b: ExtractedClaim,
    paper_map: dict[str, PaperMetadata],
) -> tuple[str, ExtractedClaim, ExtractedClaim, dict[str, Any]]:
    """Format pair payload guaranteeing source is from the lower-numbered paper.

    Returns:
        (edge_id, source_claim, target_claim, payload_dict)
    """
    num_a = _get_paper_num(claim_a.paper_id)
    num_b = _get_paper_num(claim_b.paper_id)

    if num_a < num_b:
        source_claim, target_claim = claim_a, claim_b
    elif num_b < num_a:
        source_claim, target_claim = claim_b, claim_a
    else:
        # Same paper number tie-break by claim_id
        if claim_a.claim_id <= claim_b.claim_id:
            source_claim, target_claim = claim_a, claim_b
        else:
            source_claim, target_claim = claim_b, claim_a

    # Contract §4: e-{source without dash}-{target without dash}
    source_clean = source_claim.claim_id.replace("-", "")
    target_clean = target_claim.claim_id.replace("-", "")
    edge_id = f"e-{source_clean}-{target_clean}"

    p_source = paper_map.get(source_claim.paper_id)
    p_target = paper_map.get(target_claim.paper_id)

    citation_a = p_source.citation_label if p_source else source_claim.paper_id
    dataset_a = p_source.dataset if p_source else "Not reported"
    method_a = p_source.methodology if p_source else "Not reported"

    citation_b = p_target.citation_label if p_target else target_claim.paper_id
    dataset_b = p_target.dataset if p_target else "Not reported"
    method_b = p_target.methodology if p_target else "Not reported"

    payload = {
        "pair_id": edge_id,
        "paper_a": {
            "citation_label": citation_a,
            "dataset": dataset_a,
            "methodology": method_a,
        },
        "claim_a": {
            "statement": source_claim.statement,
            "verbatim_quote": source_claim.provenance.verbatim_quote,
        },
        "paper_b": {
            "citation_label": citation_b,
            "dataset": dataset_b,
            "methodology": method_b,
        },
        "claim_b": {
            "statement": target_claim.statement,
            "verbatim_quote": target_claim.provenance.verbatim_quote,
        },
    }

    return edge_id, source_claim, target_claim, payload


async def evaluate_claim_pairs(
    candidate_indices: Sequence[tuple[int, int]],
    claims: Sequence[ExtractedClaim],
    papers: Sequence[PaperMetadata],
    sim: np.ndarray,
    llm_client: LLMClient,
    batch_size: int | None = None,
    settings: Settings | None = None,
) -> list[ClaimComparisonEdge]:
    """Run Stage 3 strict NLI referee across candidate claim pairs.

    Features:
    - Batches pairs by batch_size (default from settings).
    - Runs concurrent calls via LLMClient semaphore.
    - Drops UNRELATED pairs per contract §5.3.
    - Retries missing, malformed, or invalid pairs once as single-pair calls.
    - Produces contract-compliant ClaimComparisonEdge objects ordered by confidence descending.
    """
    if not candidate_indices:
        return []

    if settings is None:
        settings = get_settings()

    if batch_size is None:
        batch_size = settings.referee_pairs_per_call

    paper_map = {p.paper_id: p for p in papers}

    # Prepare pair records
    pair_meta: dict[str, dict[str, Any]] = {}
    pair_order: list[str] = []

    for i, j in candidate_indices:
        edge_id, src, tgt, payload = format_pair_payload(claims[i], claims[j], paper_map)
        pair_order.append(edge_id)
        pair_meta[edge_id] = {
            "source_claim": src,
            "target_claim": tgt,
            "cosine_similarity": float(sim[i, j]),
            "payload": payload,
        }

    # Group into batches
    batches: list[list[str]] = []
    for k in range(0, len(pair_order), batch_size):
        batches.append(pair_order[k : k + batch_size])

    async def _run_batch(batch_edge_ids: list[str]) -> tuple[list[str], Any]:
        batch_payloads = [pair_meta[eid]["payload"] for eid in batch_edge_ids]
        user_prompt = REFEREE_USER_PROMPT_TEMPLATE.format(
            pairs_json=json.dumps(batch_payloads, indent=2)
        )
        try:
            res = await llm_client.complete_json(
                system_prompt=REFEREE_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                output_schema=RawRefereeOutput,
            )
            return batch_edge_ids, res
        except Exception as exc:
            logger.warning("Batch referee call failed (%s): %s", batch_edge_ids, exc)
            return batch_edge_ids, exc

    batch_tasks = [_run_batch(b) for b in batches]
    batch_outputs = await asyncio.gather(*batch_tasks)

    # Process first-pass results
    resolved_items: dict[str, RawRefereeItem] = {}
    pairs_to_retry: set[str] = set()

    for batch_edge_ids, result in batch_outputs:
        if isinstance(result, Exception):
            pairs_to_retry.update(batch_edge_ids)
            continue

        raw_output: RawRefereeOutput = result
        returned_map = {item.pair_id: item for item in raw_output.results}

        for eid in batch_edge_ids:
            item = returned_map.get(eid)
            if item is None:
                pairs_to_retry.add(eid)
            elif item.relation not in VALID_RELATIONS or item.confidence is None:
                pairs_to_retry.add(eid)
            else:
                resolved_items[eid] = item

    # Single-pair retry for failed / missing / invalid items
    if pairs_to_retry:
        logger.info("Retrying %d referee pairs individually", len(pairs_to_retry))

        async def _retry_single(eid: str) -> tuple[str, RawRefereeItem | None]:
            single_payload = [pair_meta[eid]["payload"]]
            user_prompt = REFEREE_USER_PROMPT_TEMPLATE.format(
                pairs_json=json.dumps(single_payload, indent=2)
            )
            try:
                res: RawRefereeOutput = await llm_client.complete_json(
                    system_prompt=REFEREE_SYSTEM_PROMPT,
                    user_prompt=user_prompt,
                    output_schema=RawRefereeOutput,
                )
                for it in res.results:
                    if it.pair_id == eid and it.relation in VALID_RELATIONS and it.confidence is not None:
                        return eid, it
                return eid, None
            except Exception as exc:
                logger.warning("Single-pair retry failed for %s: %s", eid, exc)
                return eid, None

        retry_tasks = [_retry_single(eid) for eid in sorted(pairs_to_retry)]
        retry_results = await asyncio.gather(*retry_tasks)
        for eid, item in retry_results:
            if item is not None:
                resolved_items[eid] = item

    # Assemble edges
    edges: list[ClaimComparisonEdge] = []
    model_name = getattr(llm_client, "last_used_model", "open-weight-referee")

    for eid in pair_order:
        item = resolved_items.get(eid)
        if item is None:
            continue

        # Drop UNRELATED results per contract §5.3
        if item.relation == "UNRELATED":
            continue

        meta = pair_meta[eid]
        src: ExtractedClaim = meta["source_claim"]
        tgt: ExtractedClaim = meta["target_claim"]
        sim_val = meta["cosine_similarity"]

        # Ensure explanation conforms to contract length limits (10..500 chars)
        explanation = item.explanation.strip()
        if len(explanation) > 500:
            explanation = explanation[:500]
        elif len(explanation) < 10:
            p_a = paper_map.get(src.paper_id)
            p_b = paper_map.get(tgt.paper_id)
            lbl_a = p_a.citation_label if p_a else src.paper_id
            lbl_b = p_b.citation_label if p_b else tgt.paper_id
            explanation = f"Referee comparison between {lbl_a} and {lbl_b} regarding empirical claim."[:500]

        # Determine cluster_id if both claims share the same cluster
        edge_cluster_id = src.cluster_id if (src.cluster_id and src.cluster_id == tgt.cluster_id) else None

        edge = ClaimComparisonEdge(
            edge_id=eid,
            source_claim_id=src.claim_id,
            target_claim_id=tgt.claim_id,
            source=src.provenance,
            target=tgt.provenance,
            relation=RelationType(item.relation),
            confidence=round(item.confidence, 4),
            cosine_similarity=round(max(0.0, min(1.0, sim_val)), 4),
            explanation=explanation,
            cluster_id=edge_cluster_id,
            referee_model=model_name,
        )
        edges.append(edge)

    # Order edges per contract §4: Descending confidence, with CONTRADICT before
    # METHODOLOGY_DELTA before AGREE on ties
    relation_rank = {
        RelationType.CONTRADICT: 0,
        RelationType.METHODOLOGY_DELTA: 1,
        RelationType.AGREE: 2,
    }
    edges.sort(
        key=lambda e: (
            -e.confidence,
            relation_rank.get(e.relation, 99),
            -e.cosine_similarity,
            e.edge_id,
        )
    )

    return edges
