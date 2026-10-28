"""
Verify that every quote in the baked REAL_PIPELINE_OUTPUT presets is a real substring of the source arXiv PDF.
Usage:
    python -m scripts.verify_fixture_quotes
"""

import asyncio
import json
import sys
from pathlib import Path

import httpx
from app.schemas import AnalysisResult, FixtureProvenance
from app.services.ingestion.arxiv_fetcher import fetch_arxiv_pdf
from app.services.ingestion.pdf_parser import parse_pdf
from app.services.quote_verifier import verify_quote

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"

PRESET_FILES = [
    "demo_radiology_8papers.json",
    "demo_llm_quantization_6papers.json",
    "demo_microgrids_6papers.json",
]


async def verify_all() -> None:
    sem = asyncio.Semaphore(3)
    headers = {"User-Agent": "Kairos/1.0 (Academic Literature Synthesis; mailto:kairos@openbuild.ai)"}
    pdf_cache: dict[str, dict[int, str]] = {}

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        for fname in PRESET_FILES:
            fpath = FIXTURES_DIR / fname
            res = AnalysisResult.model_validate_json(fpath.read_bytes())
            assert res.fixture_provenance == FixtureProvenance.REAL_PIPELINE_OUTPUT, (
                f"{fname} is not REAL_PIPELINE_OUTPUT"
            )
            paper_map = {p.paper_id: p for p in res.papers}
            verified_count = 0
            for claim in res.claims:
                pmeta = paper_map[claim.paper_id]
                aid = pmeta.arxiv_id
                assert aid, f"Missing arxiv_id on {pmeta.paper_id} in {fname}"
                if aid not in pdf_cache:
                    _, pdf_bytes = await fetch_arxiv_pdf(aid, client, sem, max_file_mb=20)
                    parsed = parse_pdf(pdf_bytes, f"{aid}.pdf")
                    pdf_cache[aid] = parsed.page_texts
                pages = pdf_cache[aid]
                v = verify_quote(claim.provenance.verbatim_quote, pages, claim.provenance.page_number)
                assert v is not None, (
                    f"Quote verification failed for {claim.claim_id} in {fname}: {claim.provenance.verbatim_quote}"
                )
                verified_count += 1
            print(f"[VERIFY] {fname}: {verified_count}/{len(res.claims)} claims verified against source arXiv PDFs!", flush=True)


if __name__ == "__main__":
    asyncio.run(verify_all())
