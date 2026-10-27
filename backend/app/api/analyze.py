from __future__ import annotations

import asyncio
import logging
import re
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, File, Form, Request, Response, UploadFile, status
from sse_starlette.sse import EventSourceResponse

from app.config import get_settings
from app.errors import KairosError
from app.schemas import (
    ErrorCode,
    JobCreated,
    JobStatus,
)
from app.services.ingestion.validators import validate_inputs
from app.services.jobs import get_job_store
from app.services.pipeline import run_pipeline
from app.services.rate_limit import get_rate_limiter

logger = logging.getLogger("kairos.api.analyze")
router = APIRouter(tags=["analyze"])


@router.post(
    "/analyze",
    response_model=JobCreated,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit PDFs and arXiv IDs for multi-paper synthesis",
)
async def submit_analysis(
    request: Request,
    files: list[UploadFile] = File(default=[]),
    arxiv_ids: Optional[str] = Form(default=None),
) -> JobCreated:
    """Submit 2 to 10 research papers via direct PDF uploads or arXiv IDs.

    Returns 202 Accepted with analysis_id and polling / SSE event stream URLs.
    """
    settings = get_settings()

    # Per-IP rate limiting (contract §3.7)
    client_ip = request.client.host if request.client else "unknown"
    get_rate_limiter().check_rate_limit(client_ip)

    # Read uploaded file contents
    raw_files: list[tuple[str, bytes]] = []
    for f in files:
        if f.filename:
            content = await f.read()
            raw_files.append((f.filename, content))

    # Parse arXiv IDs (comma, space, or newline separated)
    parsed_arxiv_ids: list[str] = []
    if arxiv_ids:
        for item in re.split(r"[,\s\n]+", arxiv_ids.strip()):
            clean = item.strip()
            if clean:
                parsed_arxiv_ids.append(clean)

    # Validate paper limits, file sizes, and PDF magic bytes before starting job
    validate_inputs(files=raw_files, arxiv_ids=parsed_arxiv_ids, settings=settings)

    # Create job in JobStore
    job_store = get_job_store()
    analysis_id = job_store.generate_analysis_id()
    job_store.create_job(analysis_id)

    # Launch pipeline asynchronously in the background
    asyncio.create_task(
        run_pipeline(
            analysis_id=analysis_id,
            raw_files=raw_files,
            arxiv_ids=parsed_arxiv_ids,
            job_store=job_store,
            settings=settings,
        )
    )

    return JobCreated(
        analysis_id=analysis_id,
        status=JobStatus.QUEUED,
        events_url=f"/api/v1/analyze/{analysis_id}/events",
        result_url=f"/api/v1/analyze/{analysis_id}",
    )


@router.get(
    "/analyze/{analysis_id}/events",
    summary="Server-Sent Events progress stream for an active synthesis job",
)
async def stream_analysis_events(
    analysis_id: str,
    request: Request,
) -> EventSourceResponse:
    """Stream live Server-Sent Events (progress, complete, failed) with 15s keep-alive pings."""
    job_store = get_job_store()
    queue = job_store.subscribe(analysis_id)
    if queue is None:
        raise KairosError(
            ErrorCode.ANALYSIS_NOT_FOUND,
            f"Analysis job {analysis_id} not found or expired.",
            status_code=404,
        )

    async def event_generator() -> AsyncGenerator[dict[str, str], None]:
        try:
            while True:
                # Check for client disconnect
                if await request.is_disconnected():
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=15.0)
                except asyncio.TimeoutError:
                    # Keep-alive ping comment
                    yield {"comment": "keep-alive"}
                    continue

                if event is None:
                    # Stream finished (complete or failed)
                    break

                # Determine SSE event type
                if event.status == JobStatus.COMPLETED:
                    event_name = "complete"
                elif event.status == JobStatus.FAILED:
                    event_name = "failed"
                else:
                    event_name = "progress"

                yield {
                    "event": event_name,
                    "data": event.model_dump_json(),
                }

                if event.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                    break

        finally:
            job_store.unsubscribe(analysis_id, queue)

    return EventSourceResponse(event_generator(), ping=15)


@router.get(
    "/analyze/{analysis_id}",
    summary="Retrieve final synthesis result or current job status",
)
async def get_analysis_result(analysis_id: str) -> Response:
    """Retrieve the completed AnalysisResult or the active JobState."""
    job_store = get_job_store()
    job = job_store.get_job(analysis_id)
    if job is None:
        raise KairosError(
            ErrorCode.ANALYSIS_NOT_FOUND,
            f"Analysis job {analysis_id} not found or expired.",
            status_code=404,
        )

    if job.state.status == JobStatus.COMPLETED and job.state.result is not None:
        # Return full AnalysisResult
        return Response(
            content=job.state.result.model_dump_json(),
            media_type="application/json",
            status_code=200,
        )

    if job.state.status == JobStatus.FAILED:
        err = job.state.error
        raise KairosError(
            code=err.code if err else ErrorCode.INTERNAL_ERROR,
            message=err.message if err else "Analysis job failed.",
            status_code=500,
        )

    # Return intermediate JobState while queued or running
    return Response(
        content=job.state.model_dump_json(),
        media_type="application/json",
        status_code=200,
    )
