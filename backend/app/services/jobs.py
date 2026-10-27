from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import logging
from typing import Optional
import uuid

from app.schemas import (
    AnalysisResult,
    ErrorBody,
    JobState,
    JobStatus,
    PipelineStage,
    ProgressEvent,
)

logger = logging.getLogger("kairos.jobs")


class JobRecord:
    def __init__(self, analysis_id: str) -> None:
        self.analysis_id = analysis_id
        self.state = JobState(
            analysis_id=analysis_id,
            status=JobStatus.QUEUED,
            stage=PipelineStage.INGESTION,
            progress_pct=0,
            error=None,
            result=None,
        )
        self.created_at = datetime.now(timezone.utc)
        self.last_event: Optional[ProgressEvent] = None
        self.subscribers: set[asyncio.Queue[ProgressEvent | None]] = set()

    def publish_progress(
        self,
        stage: PipelineStage,
        status: JobStatus,
        progress_pct: int,
        message: str,
    ) -> ProgressEvent:
        """Update job state and broadcast progress event to all subscribers."""
        self.state.stage = stage
        self.state.status = status
        self.state.progress_pct = max(0, min(100, progress_pct))

        event = ProgressEvent(
            analysis_id=self.analysis_id,
            stage=stage,
            status=status,
            progress_pct=self.state.progress_pct,
            message=message,
            timestamp=datetime.now(timezone.utc),
        )
        self.last_event = event

        for q in list(self.subscribers):
            try:
                q.put_nowait(event)
            except Exception:
                self.subscribers.discard(q)

        return event

    def complete(self, result: AnalysisResult) -> ProgressEvent:
        """Mark job as completed and broadcast final event."""
        self.state.result = result
        event = self.publish_progress(
            stage=PipelineStage.DONE,
            status=JobStatus.COMPLETED,
            progress_pct=100,
            message="Analysis complete.",
        )
        # Notify subscribers that stream has ended
        for q in list(self.subscribers):
            try:
                q.put_nowait(None)
            except Exception:
                pass
        return event

    def fail(self, error: ErrorBody) -> ProgressEvent:
        """Mark job as failed and broadcast error event."""
        self.state.error = error
        event = self.publish_progress(
            stage=self.state.stage,
            status=JobStatus.FAILED,
            progress_pct=self.state.progress_pct,
            message=error.message,
        )
        for q in list(self.subscribers):
            try:
                q.put_nowait(None)
            except Exception:
                pass
        return event


class JobStore:
    """Thread-safe and async in-memory job store with SSE fanout and TTL cleanup."""

    def __init__(self) -> None:
        self._jobs: dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    def generate_analysis_id(self) -> str:
        return f"ana-{uuid.uuid4().hex[:12]}"

    def create_job(self, analysis_id: str | None = None) -> JobRecord:
        if analysis_id is None:
            analysis_id = self.generate_analysis_id()

        record = JobRecord(analysis_id)
        self._jobs[analysis_id] = record
        # Initial event
        record.publish_progress(
            stage=PipelineStage.INGESTION,
            status=JobStatus.QUEUED,
            progress_pct=0,
            message="Job queued for processing.",
        )
        return record

    def get_job(self, analysis_id: str) -> JobRecord | None:
        return self._jobs.get(analysis_id)

    def subscribe(self, analysis_id: str) -> asyncio.Queue[ProgressEvent | None] | None:
        """Subscribe to job progress events. Replays the latest event if available."""
        record = self._jobs.get(analysis_id)
        if record is None:
            return None

        q: asyncio.Queue[ProgressEvent | None] = asyncio.Queue()
        record.subscribers.add(q)

        # Replay last event if available
        if record.last_event is not None:
            q.put_nowait(record.last_event)

        # If job is already complete or failed, signal stream completion
        if record.state.status in (JobStatus.COMPLETED, JobStatus.FAILED):
            q.put_nowait(None)

        return q

    def unsubscribe(self, analysis_id: str, q: asyncio.Queue[ProgressEvent | None]) -> None:
        record = self._jobs.get(analysis_id)
        if record is not None:
            record.subscribers.discard(q)

    def cleanup_expired(self, ttl_minutes: int = 60) -> int:
        now = datetime.now(timezone.utc)
        to_delete = []
        for aid, rec in self._jobs.items():
            age_minutes = (now - rec.created_at).total_seconds() / 60.0
            if age_minutes > ttl_minutes:
                to_delete.append(aid)

        for aid in to_delete:
            del self._jobs[aid]

        return len(to_delete)


# Global singleton instance
_JOB_STORE_INSTANCE: JobStore = JobStore()


def get_job_store() -> JobStore:
    return _JOB_STORE_INSTANCE
