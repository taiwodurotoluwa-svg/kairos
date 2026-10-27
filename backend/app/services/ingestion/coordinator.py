import asyncio
import hashlib
from pathlib import Path
from app.config import Settings
from app.errors import KairosError
from app.schemas import ErrorCode, PaperSource
from app.services.ingestion.models import IngestedBatch, SectionedPaper, ParsedPdf
from app.services.ingestion.validators import validate_inputs
from app.services.ingestion.pdf_parser import parse_pdf
from app.services.ingestion.sectioner import section_paper
from app.services.ingestion.arxiv_fetcher import fetch_all_arxiv


async def ingest_all(
    files: list[tuple[str, bytes]],
    arxiv_ids: list[str],
    settings: Settings,
) -> IngestedBatch:
    """
    Unified end-to-end multi-paper ingestion pipeline:
    1. Validates file counts, sizes, magic bytes, and deduplicates inputs.
    2. Concurrently fetches arXiv papers (with graceful failure isolation).
    3. Cross-deduplicates arXiv downloaded papers against uploaded PDFs by SHA-256.
    4. Concurrently parses PDFs in thread pools using PyMuPDF.
    5. Handles scanned / broken PDFs with warnings.
    6. Sections text, budgets characters, and assigns stable paper IDs (p1..p10).
    """
    # 1. Input validation & deduplication
    valid_files, valid_arxiv = validate_inputs(files, arxiv_ids, settings)

    all_warnings: list[str] = []

    # 2. Fetch arXiv papers
    arxiv_papers, arxiv_warnings = await fetch_all_arxiv(valid_arxiv, settings)
    all_warnings.extend(arxiv_warnings)

    # 3. Assemble full raw paper list: (filename, data, source, arxiv_id)
    # Cross-deduplicate fetched arXiv PDFs against uploaded PDFs by SHA-256
    seen_hashes: set[str] = set()
    raw_papers: list[tuple[str, bytes, PaperSource, str | None]] = []

    for fn, data in valid_files:
        h = hashlib.sha256(data).hexdigest()
        seen_hashes.add(h)
        raw_papers.append((fn, data, PaperSource.UPLOAD, None))

    for aid, fn, data in arxiv_papers:
        h = hashlib.sha256(data).hexdigest()
        if h in seen_hashes:
            all_warnings.append(f"arXiv paper '{aid}' is identical to an uploaded PDF (SHA-256 duplicate); skipped.")
            continue
        seen_hashes.add(h)
        raw_papers.append((fn, data, PaperSource.ARXIV, aid))

    if not raw_papers:
        raise KairosError(
            ErrorCode.TOO_FEW_PAPERS,
            "No valid PDF papers were provided or could be retrieved.",
            400,
            details={"warnings": all_warnings}
        )

    # 4. Concurrently parse PDFs in thread pool
    async def _parse_single(item):
        fn, data, src, aid = item
        try:
            parsed = await asyncio.to_thread(parse_pdf, data, fn)
            return ("OK", fn, parsed, src, aid, "")
        except Exception as exc:
            return ("ERR", fn, None, src, aid, str(exc))

    parse_tasks = [_parse_single(item) for item in raw_papers]
    parse_results = await asyncio.gather(*parse_tasks)

    surviving: list[tuple[str, ParsedPdf, PaperSource, str | None]] = []
    for status, fn, parsed, src, aid, err_msg in parse_results:
        if status == "OK" and parsed is not None:
            surviving.append((fn, parsed, src, aid))
        else:
            all_warnings.append(f"Excluded '{fn}': {err_msg}")

    # Check minimum surviving threshold
    if len(surviving) < settings.min_papers:
        raise KairosError(
            ErrorCode.TOO_FEW_PAPERS,
            f"Only {len(surviving)} paper(s) could be successfully parsed. At least {settings.min_papers} are required.",
            400,
            details={"warnings": all_warnings}
        )

    # 5. Section and budget each surviving paper
    sectioned_papers: list[SectionedPaper] = []
    for idx, (fn, parsed, src, aid) in enumerate(surviving, start=1):
        paper_id = f"p{idx}"

        # Clean title
        if parsed.meta_title and len(parsed.meta_title.strip()) > 5:
            title = parsed.meta_title.strip()
        else:
            base_name = Path(fn).stem.replace("_", " ").replace("-", " ")
            title = base_name.strip().title()

        sec_paper = section_paper(
            parsed=parsed,
            paper_id=paper_id,
            title=title,
            source=src,
            arxiv_id=aid,
            filename=fn,
            settings=settings,
        )
        sectioned_papers.append(sec_paper)

    return IngestedBatch(papers=sectioned_papers, warnings=all_warnings)
