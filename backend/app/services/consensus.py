from __future__ import annotations

import json
import logging
from typing import Any, Sequence
from pydantic import BaseModel, ConfigDict, Field

from app.schemas import (
    ClaimComparisonEdge,
    ConsensusReport,
    PaperMetadata,
    RelationType,
    ResearchGap,
    TopContradiction,
)
from app.services.llm.client import LLMClient
from app.services.prompts.consensus import (
    CONSENSUS_SYSTEM_PROMPT,
    CONSENSUS_USER_PROMPT_TEMPLATE,
)

logger = logging.getLogger("kairos.consensus")


def compute_consensus_score(edges: Sequence[ClaimComparisonEdge]) -> int:
    """Compute deterministic consensus score per contract §6:

    Let A, C, D be the counts of AGREE, CONTRADICT, METHODOLOGY_DELTA edges.
    consensus_score = 0 if A + C + D == 0
    consensus_score = round(100 * (A + 0.5 * D) / (A + C + D)) otherwise
    """
    a = sum(1 for e in edges if e.relation == RelationType.AGREE)
    c = sum(1 for e in edges if e.relation == RelationType.CONTRADICT)
    d = sum(1 for e in edges if e.relation == RelationType.METHODOLOGY_DELTA)
    total = a + c + d
    if total == 0:
        return 0
    return round(100.0 * (a + 0.5 * d) / total)


class RawContradiction(BaseModel):
    model_config = ConfigDict(extra="ignore")
    edge_id: str
    headline: str = ""


class RawConsensusOutput(BaseModel):
    model_config = ConfigDict(extra="ignore")
    executive_summary: str = ""
    agreed_findings: list[str] = Field(default_factory=list)
    top_contradictions: list[RawContradiction] = Field(default_factory=list)
    recommended_next_steps: list[str] = Field(default_factory=list)


def build_fallback_consensus(
    papers: Sequence[PaperMetadata],
    edges: Sequence[ClaimComparisonEdge],
    gaps: Sequence[ResearchGap],
) -> ConsensusReport:
    """Construct a high-quality deterministic fallback consensus report when LLM call fails."""
    score = compute_consensus_score(edges)
    a_edges = [e for e in edges if e.relation == RelationType.AGREE]
    c_edges = [e for e in edges if e.relation == RelationType.CONTRADICT]
    d_edges = [e for e in edges if e.relation == RelationType.METHODOLOGY_DELTA]

    summary = (
        f"Comparative literature synthesis across {len(papers)} papers identified {len(a_edges)} points of agreement, "
        f"{len(c_edges)} empirical contradictions, and {len(d_edges)} methodology-driven divergences. "
        f"Overall consensus score is calculated at {score}%. "
        f"{len(gaps)} isolated research claim(s) represent potential gaps in peer literature."
    )

    agreed = [
        f"{e.explanation}"
        for e in a_edges[:5]
    ]
    if not agreed:
        agreed = ["No direct empirical consensus was established across the analyzed papers."]

    top_contra: list[TopContradiction] = []
    for e in c_edges[:3]:
        headline = f"Conflicting empirical outcomes observed between {e.source_claim_id} and {e.target_claim_id}."
        top_contra.append(TopContradiction(edge_id=e.edge_id, headline=headline[:200]))

    next_steps = [
        "Harmonize evaluation metrics and benchmark datasets to isolate true variance from setup deltas.",
        "Replicate conflicting experiments under standardized environmental and hardware configurations.",
    ]
    if gaps:
        next_steps.append("Address identified research gaps through focused empirical trials.")

    return ConsensusReport(
        consensus_score=score,
        executive_summary=summary[:1200],
        agreed_findings=agreed[:5],
        top_contradictions=top_contra,
        gap_ids=[g.gap_id for g in gaps],
        recommended_next_steps=next_steps[:4],
    )


async def generate_consensus_report(
    papers: Sequence[PaperMetadata],
    edges: Sequence[ClaimComparisonEdge],
    gaps: Sequence[ResearchGap],
    llm_client: LLMClient,
) -> tuple[ConsensusReport, str, str]:
    """Generate Stage 4 consensus report via open-weight model with ID validation and fallback.

    Returns:
        (ConsensusReport, provider_name, model_id)
    """
    score = compute_consensus_score(edges)
    gap_ids = [g.gap_id for g in gaps]
    valid_contradiction_ids = {e.edge_id for e in edges if e.relation == RelationType.CONTRADICT}

    data_payload = {
        "papers": [
            {
                "citation_label": p.citation_label,
                "title": p.title,
                "dataset": p.dataset,
                "methodology": p.methodology,
                "primary_metric": p.primary_metric,
            }
            for p in papers
        ],
        "edges": [
            {
                "edge_id": e.edge_id,
                "relation": e.relation.value,
                "confidence": e.confidence,
                "explanation": e.explanation,
                "source_claim": e.source_claim_id,
                "target_claim": e.target_claim_id,
            }
            for e in edges
        ],
        "gaps": [
            {
                "gap_id": g.gap_id,
                "paper": g.paper_id,
                "statement": g.statement,
            }
            for g in gaps
        ],
    }

    user_prompt = CONSENSUS_USER_PROMPT_TEMPLATE.format(
        data_json=json.dumps(data_payload, indent=2)
    )

    try:
        raw_output, provider_name, model_id = await llm_client.complete_json(
            system=CONSENSUS_SYSTEM_PROMPT,
            user=user_prompt,
            max_tokens=700,
            temperature=0.3,
            validate=RawConsensusOutput.model_validate,
        )

        # Validate top contradictions: must match a real CONTRADICT edge_id
        filtered_contradictions: list[TopContradiction] = []
        for it in raw_output.top_contradictions:
            if it.edge_id in valid_contradiction_ids:
                hl = it.headline.strip() or f"Contradiction identified on edge {it.edge_id}."
                filtered_contradictions.append(TopContradiction(edge_id=it.edge_id, headline=hl[:200]))
                if len(filtered_contradictions) >= 3:
                    break

        # Fallback bullets if LLM returned empty lists
        agreed = [s.strip() for s in raw_output.agreed_findings if s.strip()][:5]
        if not agreed:
            a_edges = [e for e in edges if e.relation == RelationType.AGREE]
            agreed = [e.explanation for e in a_edges[:5]] or ["No uniform consensus emerged from the claim pairs."]

        next_steps = [s.strip() for s in raw_output.recommended_next_steps if s.strip()][:4]
        if not next_steps:
            next_steps = [
                "Harmonize evaluation metrics and benchmark datasets across research groups.",
                "Replicate boundary-condition experiments to resolve methodological differences.",
            ]

        summary = raw_output.executive_summary.strip()
        if not summary:
            summary = (
                f"Multi-paper synthesis across {len(papers)} papers identified {score}% consensus. "
                f"Examined {len(edges)} cross-paper relationships and {len(gaps)} potential literature gaps."
            )

        report = ConsensusReport(
            consensus_score=score,
            executive_summary=summary[:1200],
            agreed_findings=agreed,
            top_contradictions=filtered_contradictions,
            gap_ids=gap_ids,
            recommended_next_steps=next_steps,
        )
        return report, provider_name, model_id

    except Exception as exc:
        logger.warning("Stage 4 consensus generation failed (%s), using template fallback", exc)
        fallback = build_fallback_consensus(papers, edges, gaps)
        model = getattr(llm_client, "last_used_model", "fallback-template") or "fallback-template"
        provider = getattr(llm_client, "last_used_provider", "template") or "template"
        return fallback, provider, model
