import hashlib
from app.config import Settings
from app.errors import KairosError
from app.schemas import ErrorCode
from app.services.ingestion.arxiv_fetcher import normalize_arxiv_id


def validate_inputs(
    files: list[tuple[str, bytes]],
    arxiv_ids: list[str],
    settings: Settings
) -> tuple[list[tuple[str, bytes]], list[str]]:
    """
    Validates uploaded PDF files and arXiv ID list:
    1. Magic bytes check: every file must contain b"%PDF-" in first 1024 bytes.
    2. File size bounds: per-file <= max_file_mb, total <= max_total_mb.
    3. De-duplication: files by SHA-256 hash, arXiv IDs by canonical normalized ID.
    4. Paper count bounds: min_papers <= total <= max_papers.
    """
    max_file_bytes = settings.max_file_mb * 1024 * 1024
    max_total_bytes = settings.max_total_mb * 1024 * 1024

    total_bytes = 0
    seen_hashes: set[str] = set()
    deduped_files: list[tuple[str, bytes]] = []

    for filename, data in files:
        # Check individual file size
        file_len = len(data)
        if file_len > max_file_bytes:
            raise KairosError(
                ErrorCode.FILE_TOO_LARGE,
                f"File '{filename}' exceeds {settings.max_file_mb}MB limit ({file_len / (1024 * 1024):.1f}MB).",
                413
            )

        total_bytes += file_len
        if total_bytes > max_total_bytes:
            raise KairosError(
                ErrorCode.FILE_TOO_LARGE,
                f"Total file size exceeds {settings.max_total_mb}MB limit ({total_bytes / (1024 * 1024):.1f}MB).",
                413
            )

        # Check magic bytes (%PDF-)
        header = data[:1024]
        if b"%PDF-" not in header:
            raise KairosError(
                ErrorCode.INVALID_FILE_TYPE,
                f"File '{filename}' is not a valid PDF document (missing %PDF- header).",
                400
            )

        # SHA-256 de-duplication
        h = hashlib.sha256(data).hexdigest()
        if h in seen_hashes:
            continue
        seen_hashes.add(h)
        deduped_files.append((filename, data))

    # De-duplicate arXiv IDs using canonical normalization
    seen_arxiv: set[str] = set()
    deduped_arxiv: list[str] = []
    for aid in arxiv_ids:
        raw_aid = aid.strip()
        if not raw_aid:
            continue
        # Canonicalize format (e.g. 'https://arxiv.org/abs/2309.12345v1' -> '2309.12345')
        canonical_id = normalize_arxiv_id(raw_aid)
        if canonical_id in seen_arxiv:
            continue
        seen_arxiv.add(canonical_id)
        deduped_arxiv.append(canonical_id)

    total_count = len(deduped_files) + len(deduped_arxiv)

    if total_count < settings.min_papers:
        raise KairosError(
            ErrorCode.TOO_FEW_PAPERS,
            f"At least {settings.min_papers} unique papers are required for synthesis (received {total_count}).",
            400
        )

    if total_count > settings.max_papers:
        raise KairosError(
            ErrorCode.TOO_MANY_PAPERS,
            f"At most {settings.max_papers} papers are allowed per analysis (received {total_count}).",
            400
        )

    return deduped_files, deduped_arxiv
