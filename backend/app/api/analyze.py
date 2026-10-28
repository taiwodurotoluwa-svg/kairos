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
    ErrorBody,
    ErrorCode,
    ErrorResponse,
    JobCreated,
    JobStatus,
)
from app.services.ingestion.validators import validate_inputs
from app.services.jobs import get_job_store
from app.services.pipeline import run_pipeline
from app.services.rate_limit import get_rate_limiter

logger = logging.getLogger("kairos.api.analyze")
router = APIRouter(tags=["analyze"])

_BACKGROUND_TASKS: set[asyncio.Task] = set()


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

    # Per-IP rate limiting (contract §3.7) with reverse-proxy X-Forwarded-For support
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        client_ip = forwarded.split(",")[0].strip()
    elif request.client:
        client_ip = request.client.host
    else:
        client_ip = "unknown"
    get_rate_limiter().check_rate_limit(client_ip)

    # Read uploaded file contents with early size bound check (Opt 3)
    raw_files: list[tuple[str, bytes]] = []
    max_bytes = settings.max_file_mb * 1024 * 1024
    for f in files:
        if f.filename:
            content = await f.read(max_bytes + 1)
            if len(content) > max_bytes:
                raise KairosError(
                    ErrorCode.FILE_TOO_LARGE,
                    f"File '{f.filename}' exceeds maximum allowed size ({settings.max_file_mb}MB).",
                    status_code=413,
                )
            raw_files.append((f.filename, content))

    # Parse arXiv IDs: support JSON array string per §3.4 and comma/whitespace separated strings (F-01)
    parsed_arxiv_ids: list[str] = []
    if arxiv_ids and arxiv_ids.strip():
        raw_str = arxiv_ids.strip()
        if raw_str.startswith("["):
            import json
            try:
                items = json.loads(raw_str)
            except Exception:
                items = re.split(r"[,\s\n]+", raw_str.strip("[]"))
        else:
            items = re.split(r"[,\s\n]+", raw_str)
        parsed_arxiv_ids = [str(x).strip().strip("'\"") for x in items if str(x).strip().strip("'\"")]

    # Validate paper limits, file sizes, and PDF magic bytes before starting job
    validate_inputs(files=raw_files, arxiv_ids=parsed_arxiv_ids, settings=settings)

    # Bounded memory: cleanup expired jobs before allocating a new one
    job_store = get_job_store()
    job_store.cleanup_expired(settings.job_ttl_minutes)

    analysis_id = job_store.generate_analysis_id()
    job_store.create_job(analysis_id)

    # Launch pipeline asynchronously with strong reference and unhandled exception guard
    async def _run_pipeline_background() -> None:
        try:
            await run_pipeline(
                analysis_id=analysis_id,
                raw_files=raw_files,
                arxiv_ids=parsed_arxiv_ids,
                job_store=job_store,
                settings=settings,
            )
        except Exception as exc:
            logger.info("Background analysis %s finished with exception: %s", analysis_id, exc)

    task = asyncio.create_task(_run_pipeline_background())
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)

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
                    payload = event.model_dump_json()
                elif event.status == JobStatus.FAILED:
                    event_name = "failed"
                    # §3.5 specifies ErrorResponse payload for failed SSE events
                    job = job_store.get_job(analysis_id)
                    error_body = (
                        job.state.error
                        if (job and job.state.error)
                        else ErrorBody(
                            code=ErrorCode.INTERNAL_ERROR,
                            message=event.message,
                        )
                    )
                    payload = ErrorResponse(error=error_body).model_dump_json()
                else:
                    event_name = "progress"
                    payload = event.model_dump_json()

                yield {
                    "event": event_name,
                    "data": payload,
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
async def get_analysis_result(analysis_id: str, raw: bool = False) -> Response:
    """
    Retrieve the current JobState per 02-api-contracts.md §3.6 (200 -> JobState).
    When status == 'COMPLETED', job.state.result contains the full AnalysisResult.
    When status == 'FAILED', job.state.error contains the ErrorBody (never HTTP 500).
    Optionally, pass ?raw=true to retrieve raw AnalysisResult when completed.
    """
    job_store = get_job_store()
    job = job_store.get_job(analysis_id)
    if job is None:
        raise KairosError(
            ErrorCode.ANALYSIS_NOT_FOUND,
            f"Analysis job {analysis_id} not found or expired.",
            status_code=404,
        )

    if raw and job.state.status == JobStatus.COMPLETED and job.state.result is not None:
        return Response(
            content=job.state.result.model_dump_json(),
            media_type="application/json",
            status_code=200,
        )

    # Return JobState on 200 across all statuses (QUEUED, RUNNING, COMPLETED, FAILED)
    return Response(
        content=job.state.model_dump_json(),
        media_type="application/json",
        status_code=200,
    )
