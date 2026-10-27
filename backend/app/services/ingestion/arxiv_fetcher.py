import asyncio
import re
import httpx
from app.config import Settings
from app.errors import KairosError
from app.schemas import ErrorCode

ARXIV_NEW_RE = re.compile(r"^(\d{4}\.\d{4,5})(?:v\d+)?$")
ARXIV_OLD_RE = re.compile(r"^([a-z\-]+/\d{7})(?:v\d+)?$", re.IGNORECASE)


def normalize_arxiv_id(raw: str) -> str:
    """
    Normalises all standard arXiv input formats to canonical identifier:
    - 2309.12345
    - 2309.12345v2 -> 2309.12345
    - arxiv:2309.12345 -> 2309.12345
    - https://arxiv.org/abs/2309.12345 -> 2309.12345
    - https://arxiv.org/pdf/2309.12345.pdf -> 2309.12345
    - hep-th/9901001 -> hep-th/9901001
    """
    text = raw.strip()

    # Strip URLs
    text = re.sub(r"^https?://arxiv\.org/(?:abs|pdf)/", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\.pdf$", "", text, flags=re.IGNORECASE)

    # Strip arxiv: prefix
    text = re.sub(r"^arxiv:\s*", "", text, flags=re.IGNORECASE).strip()

    # Check new format
    m_new = ARXIV_NEW_RE.match(text)
    if m_new:
        return m_new.group(1)

    # Check old format
    m_old = ARXIV_OLD_RE.match(text)
    if m_old:
        return m_old.group(1).lower()

    raise KairosError(
        ErrorCode.ARXIV_FETCH_FAILED,
        f"Invalid arXiv identifier format: '{raw}'. Supported forms include '2309.12345', 'arxiv:2309.12345', or 'https://arxiv.org/abs/2309.12345'.",
        400
    )


async def fetch_arxiv_pdf(
    arxiv_id: str,
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
) -> tuple[str, bytes]:
    """
    Fetches a single paper PDF from arXiv with timeout and validation.
    """
    clean_id = normalize_arxiv_id(arxiv_id)
    url = f"https://arxiv.org/pdf/{clean_id}.pdf"
    headers = {"User-Agent": "Kairos-Paper-Synthesizer/1.0 (Research Assistant; mailto:team@kairos.dev)"}

    async with semaphore:
        try:
            res = await client.get(url, headers=headers, follow_redirects=True, timeout=30.0)
        except Exception as exc:
            raise KairosError(
                ErrorCode.ARXIV_FETCH_FAILED,
                f"Network error downloading arXiv paper '{clean_id}': {exc}",
                400
            ) from exc

    if res.status_code != 200:
        raise KairosError(
            ErrorCode.ARXIV_FETCH_FAILED,
            f"arXiv returned HTTP {res.status_code} for paper '{clean_id}'.",
            400
        )

    content = res.content
    if b"%PDF-" not in content[:1024]:
        raise KairosError(
            ErrorCode.ARXIV_FETCH_FAILED,
            f"arXiv response for paper '{clean_id}' did not contain valid PDF data.",
            400
        )

    filename = f"arxiv_{clean_id.replace('/', '_')}.pdf"
    return filename, content


async def fetch_all_arxiv(
    arxiv_ids: list[str],
    settings: Settings,
    client: httpx.AsyncClient | None = None
) -> tuple[list[tuple[str, str, bytes]], list[str]]:
    """
    Concurrently fetches multiple arXiv papers.
    Returns:
    - successful_papers: list of (canonical_arxiv_id, filename, pdf_bytes)
    - warnings: list of error warning strings for failed downloads
    """
    if not arxiv_ids:
        return [], []

    sem = asyncio.Semaphore(settings.arxiv_concurrency)
    close_client = False
    if client is None:
        client = httpx.AsyncClient()
        close_client = True

    try:
        results: list[tuple[str, str, bytes]] = []
        warnings: list[str] = []

        async def _fetch_one(aid: str):
            try:
                clean_id = normalize_arxiv_id(aid)
                filename, data = await fetch_arxiv_pdf(clean_id, client, sem)
                return ("OK", clean_id, filename, data)
            except Exception as exc:
                return ("ERR", aid, str(exc), b"")

        tasks = [_fetch_one(aid) for aid in arxiv_ids]
        raw_responses = await asyncio.gather(*tasks)

        for status, ident, fn_or_err, data in raw_responses:
            if status == "OK":
                results.append((ident, fn_or_err, data))
            else:
                warnings.append(f"Failed to fetch arXiv paper '{ident}': {fn_or_err}")

        return results, warnings
    finally:
        if close_client:
            await client.aclose()
