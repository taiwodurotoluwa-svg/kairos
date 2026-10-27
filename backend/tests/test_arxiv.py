import asyncio
import pytest
import httpx
import pymupdf
from app.config import get_settings
from app.errors import KairosError
from app.schemas import ErrorCode
from app.services.ingestion.arxiv_fetcher import normalize_arxiv_id, fetch_arxiv_pdf, fetch_all_arxiv


def _create_mock_pdf_bytes() -> bytes:
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)
    page.insert_text((50, 50), "arXiv Mock Paper Content\n" * 20, fontsize=11)
    content = doc.tobytes()
    doc.close()
    return content


def test_normalize_arxiv_id_all_formats():
    """Verifies that all 5 arXiv URL and string formats normalize to canonical IDs."""
    assert normalize_arxiv_id("2309.12345") == "2309.12345"
    assert normalize_arxiv_id("2309.12345v3") == "2309.12345"
    assert normalize_arxiv_id("arxiv:2309.12345") == "2309.12345"
    assert normalize_arxiv_id("ARXIV: 2309.12345v1") == "2309.12345"
    assert normalize_arxiv_id("https://arxiv.org/abs/2309.12345") == "2309.12345"
    assert normalize_arxiv_id("https://arxiv.org/abs/2309.12345v2") == "2309.12345"
    assert normalize_arxiv_id("https://arxiv.org/pdf/2309.12345.pdf") == "2309.12345"
    assert normalize_arxiv_id("http://arxiv.org/pdf/2309.12345") == "2309.12345"
    assert normalize_arxiv_id("hep-th/9901001") == "hep-th/9901001"
    assert normalize_arxiv_id("hep-th/9901001v2") == "hep-th/9901001"


def test_normalize_arxiv_id_invalid_formats():
    """Missing Test 1: Rejects malformed arXiv identifiers with INVALID_ARXIV_ID."""
    invalid_ids = ["not_an_id", "2309", "abc.123", "http://otherdomain.com/paper.pdf", ""]
    for bad in invalid_ids:
        with pytest.raises(KairosError) as exc_info:
            normalize_arxiv_id(bad)
        assert exc_info.value.code == ErrorCode.INVALID_ARXIV_ID


def test_fetch_arxiv_pdf_success():
    """Verifies successful arXiv fetch and %PDF- validation using mock transport."""
    async def _run():
        pdf_bytes = _create_mock_pdf_bytes()

        def handler(request: httpx.Request) -> httpx.Response:
            assert "2309.12345.pdf" in str(request.url)
            return httpx.Response(200, content=pdf_bytes)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            sem = asyncio.Semaphore(2)
            fn, content = await fetch_arxiv_pdf("2309.12345", client, sem)
            assert fn == "arxiv_2309.12345.pdf"
            assert content.startswith(b"%PDF-")

    asyncio.run(_run())


def test_fetch_arxiv_pdf_file_too_large():
    """Verifies that an arXiv download exceeding max_file_mb raises FILE_TOO_LARGE."""
    async def _run():
        huge_content = b"%PDF-1.4\n" + b"0" * (2 * 1024 * 1024)  # 2MB

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, content=huge_content)

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            sem = asyncio.Semaphore(2)
            with pytest.raises(KairosError) as exc_info:
                # Limit to 1MB
                await fetch_arxiv_pdf("2309.12345", client, sem, max_file_mb=1)
            assert exc_info.value.code == ErrorCode.FILE_TOO_LARGE

    asyncio.run(_run())


def test_fetch_arxiv_pdf_http_error():
    """Verifies that HTTP 404 from arXiv raises KairosError(ARXIV_FETCH_FAILED)."""
    async def _run():
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(404, content=b"Not found on arXiv")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            sem = asyncio.Semaphore(2)
            with pytest.raises(KairosError) as exc_info:
                await fetch_arxiv_pdf("2309.99999", client, sem)
            assert exc_info.value.code == ErrorCode.ARXIV_FETCH_FAILED

    asyncio.run(_run())


def test_fetch_all_arxiv_partial_failure_isolation():
    """Verifies that an individual failure is isolated to warnings while valid papers succeed."""
    async def _run():
        pdf_bytes = _create_mock_pdf_bytes()
        settings = get_settings()

        def handler(request: httpx.Request) -> httpx.Response:
            if "2309.11111" in str(request.url):
                return httpx.Response(200, content=pdf_bytes)
            return httpx.Response(404, content=b"Not found")

        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as client:
            papers, warnings = await fetch_all_arxiv(["2309.11111", "2309.99999"], settings, client=client)
            assert len(papers) == 1
            assert papers[0][0] == "2309.11111"
            assert len(warnings) == 1
            assert "2309.99999" in warnings[0]

    asyncio.run(_run())
