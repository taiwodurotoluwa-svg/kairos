from __future__ import annotations

import inspect

import asyncio
import logging
import time
from typing import Sequence
import numpy as np

from app.config import Settings, get_settings
from app.errors import KairosError
from app.schemas import (
    AnalysisMode,
    AnalysisResult,
    ErrorCode,
    ExtractedClaim,
    JobStatus,
    PaperMetadata,
    PipelineStage,
    StageLatency,
)
from app.services.consensus import generate_consensus_report
from app.services.embeddings import FastEmbedEmbedder, get_embedder
from app.services.extraction import extract_claims_from_paper
from app.services.graph_builder import build_analysis_result, build_model_disclosures
from app.services.ingestion.coordinator import ingest_all
from app.services.jobs import JobRecord, JobStore
from app.services.llm.client import LLMClient
from app.services.referee import evaluate_claim_pairs
from app.services.similarity import (
    build_clusters,
    build_research_gaps,
    calculate_pair_stats,
    candidate_pairs,
    claim_to_embed_text,
    cosine_matrix,
    find_gaps,
)

logger = logging.getLogger("kairos.pipeline")


async def run_pipeline(
    analysis_id: str,
    raw_files: list[tuple[str, bytes]],
    arxiv_ids: list[str],
    job_store: JobStore,
    settings: Settings | None = None,
    llm_client: LLMClient | None = None,
    embedder: FastEmbedEmbedder | None = None,
) -> AnalysisResult:
    """Execute the end-to-end 5-stage synthesis pipeline:

    Stage 0: Ingestion & parsing (0% -> 20%)
    Stage 1: LLM claim extraction & quote verification (20% -> 55%)
    Stage 2: Embeddings, cosine matrix, pre-cap gaps & clustering (55% -> 75%)
    Stage 3: Strict NLI referee (75% -> 90%)
    Stage 4: Consensus report, graph assembly & final validation (90% -> 100%)
    """
    if settings is None:
        settings = get_settings()

    job_record = job_store.get_job(analysis_id)
    if job_record is None:
        raise KairosError(
            ErrorCode.ANALYSIS_NOT_FOUND,
            f"Job {analysis_id} not found in store.",
            status_code=404,
        )

    pipeline_start = time.perf_counter()
    warnings: list[str] = []

    async def _execute() -> AnalysisResult:
        nonlocal llm_client, embedder
        if llm_client is None:
            llm_client = LLMClient(settings)
        if embedder is None:
            embedder = get_embedder(settings)

        # =========================================================================
        # Stage 0: Ingestion (0% -> 20%)
        # =========================================================================
        t0 = time.perf_counter()
        job_record.publish_progress(
            stage=PipelineStage.INGESTION,
            status=JobStatus.RUNNING,
            progress_pct=5,
            message="Ingesting paper sources (PDF uploads and arXiv metadata)...",
        )

        ingested_batch = await ingest_all(
            files=raw_files,
            arxiv_ids=arxiv_ids,
            settings=settings,
        )
        raw_files.clear()  # Opt 3: release raw PDF bytes from RAM immediately

        sectioned_papers = ingested_batch.papers
        warnings.extend(ingested_batch.warnings)

        job_record.publish_progress(
            stage=PipelineStage.INGESTION,
            status=JobStatus.RUNNING,
            progress_pct=20,
            message=f"Ingested and parsed {len(sectioned_papers)} papers successfully.",
        )
        ingestion_ms = int((time.perf_counter() - t0) * 1000)

        # =========================================================================
        # Stage 1: LLM Claim Extraction & Quote Verification (20% -> 55%)
        # =========================================================================
        t1 = time.perf_counter()
        job_record.publish_progress(
            stage=PipelineStage.EXTRACTION,
            status=JobStatus.RUNNING,
            progress_pct=25,
            message="Extracting scientific claims and verifying quotes against source text...",
        )

        completed_count = 0
        total_papers = len(sectioned_papers)

        async def _extract_with_progress(sec):
            nonlocal completed_count
            try:
                res = await extract_claims_from_paper(
                    sec_paper=sec,
                    llm_client=llm_client,
                    settings=settings,
                )
                completed_count += 1
                pct = 25 + int(28 * (completed_count / max(1, total_papers)))
                job_record.publish_progress(
                    stage=PipelineStage.EXTRACTION,
                    status=JobStatus.RUNNING,
                    progress_pct=pct,
                    message=f"Extracted {len(res[1])} verified claims from {res[0].citation_label} ({completed_count}/{total_papers}).",
                )
                return res
            except Exception as exc:
                completed_count += 1
                return exc

        extraction_results = await asyncio.gather(
            *[_extract_with_progress(sec) for sec in sectioned_papers]
        )

        all_papers: list[PaperMetadata] = []
        all_claims: list[ExtractedClaim] = []
        all_provider_unavailable = True

        for idx, item in enumerate(extraction_results):
            if isinstance(item, Exception):
                if not (isinstance(item, KairosError) and item.code == ErrorCode.LLM_PROVIDER_UNAVAILABLE):
                    all_provider_unavailable = False
                warnings.append(f"Excluded paper p{idx + 1} due to extraction error: {item}")
                continue
            all_provider_unavailable = False
            paper_meta, claims, paper_warnings = item
            warnings.extend(paper_warnings)
            if len(claims) == 0:
                warnings.append(
                    f"Excluded paper '{paper_meta.citation_label}' ({paper_meta.paper_id}): zero verified claims survived quote verification."
                )
                continue
            all_papers.append(paper_meta)
            all_claims.extend(claims)

        # If every paper failed due to provider unavailable, re-raise it
        if len(all_papers) == 0 and all_provider_unavailable and extraction_results:
            first_err = extraction_results[0]
            if isinstance(first_err, KairosError):
                raise first_err

        sectioned_papers.clear()  # Opt 3: release sectioned paper text from RAM

        # Guard surviving counts per 03-open-weight-models.md §6
        if len(all_papers) < settings.min_papers or len(all_claims) < 2:
            raise KairosError(
                ErrorCode.TOO_FEW_PAPERS,
                f"Insufficient verified claims extracted across papers ({len(all_papers)} papers and {len(all_claims)} claims survived; minimum is {settings.min_papers} papers and 2 claims).",
                status_code=400,
            )

        job_record.publish_progress(
            stage=PipelineStage.EXTRACTION,
            status=JobStatus.RUNNING,
            progress_pct=55,
            message=f"Extracted {len(all_claims)} verified claims across {len(all_papers)} surviving papers.",
        )
        extraction_ms = int((time.perf_counter() - t1) * 1000)

        # Record active extraction model and provider
        ext_model = getattr(llm_client, "last_used_model", settings.groq_model) or settings.groq_model
        ext_prov = getattr(llm_client, "last_used_provider", "groq") or "groq" 

        # =========================================================================
        # Stage 2: Embeddings, Similarity, Gaps & Clustering (55% -> 75%)
        # =========================================================================
        t2_emb = time.perf_counter()
        job_record.publish_progress(
            stage=PipelineStage.EMBEDDING,
            status=JobStatus.RUNNING,
            progress_pct=58,
            message="Computing dense semantic embeddings for claims...",
        )

        claim_texts = [claim_to_embed_text(c) for c in all_claims]
        paper_id_to_int = {p.paper_id: i for i, p in enumerate(all_papers)}
        paper_idx = np.array([paper_id_to_int[c.paper_id] for c in all_claims], dtype=int)

        # Offload synchronous ONNX CPU embedding to a worker thread
        emb = await asyncio.to_thread(embedder.embed, claim_texts)
        embedding_ms = int((time.perf_counter() - t2_emb) * 1000)

        t2_clust = time.perf_counter()
        job_record.publish_progress(
            stage=PipelineStage.CLUSTERING,
            status=JobStatus.RUNNING,
            progress_pct=65,
            message="Building similarity matrix, detecting research gaps, and clustering...",
        )

        sim = cosine_matrix(emb, paper_idx)

        # Gaps evaluated BEFORE top-k and max-pair caps per contract §5
        gap_indices = find_gaps(sim, threshold=settings.similarity_threshold)
        gaps = build_research_gaps(gap_indices, all_claims, sim)

        # Candidate pairs pre-filtered with top_k per paper
        kept_pairs, total_candidates = candidate_pairs(
            sim=sim,
            paper_idx=paper_idx,
            threshold=settings.similarity_threshold,
            top_k=settings.top_k_per_paper,
            max_pairs=settings.max_referee_pairs,
        )

        # Topic clusters with contract discard rules
        clusters, _ = build_clusters(
            emb=emb,
            claims=all_claims,
            distance_threshold=settings.cluster_distance_threshold,
        )

        pair_stats = calculate_pair_stats(
            paper_idx=paper_idx,
            candidate_pairs_count=total_candidates,
            evaluated_pairs_count=len(kept_pairs),
        )

        if total_candidates > settings.max_referee_pairs:
            warnings.append(
                f"Candidate pairs truncated from {total_candidates} to {settings.max_referee_pairs} highest-similarity pairs."
            )

        job_record.publish_progress(
            stage=PipelineStage.CLUSTERING,
            status=JobStatus.RUNNING,
            progress_pct=75,
            message=f"Formed {len(clusters)} topic clusters and selected {len(kept_pairs)} candidate pairs.",
        )
        clustering_ms = int((time.perf_counter() - t2_clust) * 1000)

        # =========================================================================
        # Stage 3: Strict NLI Referee (75% -> 90%)
        # =========================================================================
        t3 = time.perf_counter()
        job_record.publish_progress(
            stage=PipelineStage.REFEREE,
            status=JobStatus.RUNNING,
            progress_pct=78,
            message=f"Evaluating {len(kept_pairs)} claim pairs with academic NLI referee...",
        )

        initial_calls = getattr(llm_client, "call_count", 0)

        edges = await evaluate_claim_pairs(
            candidate_indices=kept_pairs,
            claims=all_claims,
            papers=all_papers,
            sim=sim,
            llm_client=llm_client,
            batch_size=settings.referee_pairs_per_call,
            settings=settings,
        )

        referee_calls_made = max(0, getattr(llm_client, "call_count", 0) - initial_calls)

        job_record.publish_progress(
            stage=PipelineStage.REFEREE,
            status=JobStatus.RUNNING,
            progress_pct=90,
            message=f"Referee evaluated {len(edges)} verified claim relationships.",
        )
        referee_ms = int((time.perf_counter() - t3) * 1000)

        # Record active referee model and provider
        ref_model = getattr(llm_client, "last_used_model", settings.groq_model) or settings.groq_model
        ref_prov = getattr(llm_client, "last_used_provider", "groq") or "groq" 

        # =========================================================================
        # Stage 4: Consensus Writer & Graph Assembly (90% -> 100%)
        # =========================================================================
        t4 = time.perf_counter()
        job_record.publish_progress(
            stage=PipelineStage.CONSENSUS,
            status=JobStatus.RUNNING,
            progress_pct=92,
            message="Synthesizing literature consensus and executive summary...",
        )

        consensus_report, cons_prov, cons_model = await generate_consensus_report(
            papers=all_papers,
            edges=edges,
            gaps=gaps,
            llm_client=llm_client,
        )
        consensus_ms = int((time.perf_counter() - t4) * 1000)

        # Invariant: total_ms equals the exact sum of the 6 stage latencies per contract §3.5
        total_ms = (
            ingestion_ms
            + extraction_ms
            + embedding_ms
            + clustering_ms
            + referee_ms
            + consensus_ms
        )

        stage_latencies = StageLatency(
            ingestion_ms=ingestion_ms,
            extraction_ms=extraction_ms,
            embedding_ms=embedding_ms,
            clustering_ms=clustering_ms,
            referee_ms=referee_ms,
            consensus_ms=consensus_ms,
            total_ms=total_ms,
        )

        # Map embedding provider per contract §4 ("fastembed-local" or "hf-inference-api")
        emb_backend = settings.embedding_backend.lower()
        if "fastembed" in emb_backend:
            emb_prov = "fastembed-local"
        elif "hf" in emb_backend:
            emb_prov = "hf-inference-api"
        else:
            emb_prov = settings.embedding_backend

        models = build_model_disclosures(
            extraction_model=ext_model,
            extraction_provider=ext_prov,
            embedding_model=settings.embedding_model,
            embedding_provider=emb_prov,
            referee_model=ref_model,
            referee_provider=ref_prov,
            consensus_model=cons_model,
            consensus_provider=cons_prov,
        )

        # Assemble final result
        analysis_result = build_analysis_result(
            analysis_id=analysis_id,
            papers=all_papers,
            claims=all_claims,
            clusters=clusters,
            edges=edges,
            gaps=gaps,
            consensus=consensus_report,
            cross_paper_pairs_total=int(pair_stats["cross_paper_pairs_total"]),
            candidate_pairs_count=int(pair_stats["candidate_pairs"]),
            referee_pairs_evaluated=len(kept_pairs),
            referee_calls=referee_calls_made,
            pair_reduction_pct=float(pair_stats["pair_reduction_pct"]),
            stage_latencies=stage_latencies,
            models=models,
            warnings=warnings,
            mode=AnalysisMode.LIVE,
        )

        job_record.complete(analysis_result)
        return analysis_result

    try:
        return await asyncio.wait_for(_execute(), timeout=float(settings.job_timeout_seconds))
    except asyncio.TimeoutError:
        logger.error("Analysis %s exceeded timeout of %ds", analysis_id, settings.job_timeout_seconds)
        err = KairosError(
            ErrorCode.INTERNAL_ERROR,
            f"Analysis timed out after {settings.job_timeout_seconds} seconds.",
            status_code=504,
        )
        job_record.fail(err.to_body())
        raise err
    except KairosError as ke:
        logger.error("Analysis %s failed with KairosError: %s", analysis_id, ke)
        job_record.fail(ke.to_body())
        raise
    except Exception as exc:
        logger.exception("Unexpected pipeline failure on %s", analysis_id)
        err = KairosError(
            ErrorCode.INTERNAL_ERROR,
            f"An unexpected internal error occurred during synthesis: {exc}",
            status_code=500,
        )
        job_record.fail(err.to_body())
        raise err
    finally:
        if llm_client and hasattr(llm_client, "aclose"):
            close_coro = llm_client.aclose()
            if inspect.isawaitable(close_coro):
                await close_coro
