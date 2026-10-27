"""
Smoke extraction script: extracts and verifies scientific claims from a real PDF.
Usage:
    python -m scripts.smoke_extract <path_to_pdf>
"""

import asyncio
import sys
from pathlib import Path
from app.config import get_settings
from app.services.extraction import extract_claims_from_paper
from app.services.ingestion.pdf_parser import parse_pdf
from app.services.ingestion.sectioner import section_paper
from app.services.llm.client import LLMClient
from app.schemas import PaperSource


async def main():
    if len(sys.argv) < 2:
        print("Usage: python -m scripts.smoke_extract <path_to_pdf>")
        sys.exit(1)

    pdf_path = Path(sys.argv[1])
    if not pdf_path.exists():
        print(f"Error: File '{pdf_path}' does not exist.")
        sys.exit(1)

    data = pdf_path.read_bytes()
    settings = get_settings()

    print(f"1. Parsing PDF '{pdf_path.name}' ({len(data)} bytes)...")
    parsed = parse_pdf(data, pdf_path.name)
    print(f"   Pages: {parsed.page_count}, Characters: {parsed.char_count}")

    print("2. Sectioning and budgeting paper...")
    sec_paper = section_paper(
        parsed=parsed,
        paper_id="p1",
        title=parsed.meta_title or pdf_path.stem.replace("_", " ").title(),
        source=PaperSource.UPLOAD,
        filename=pdf_path.name,
        settings=settings,
    )
    print(f"   Sections found: {[s.value for s in sec_paper.sections_found]}")
    print(f"   Characters budgeted: {len(sec_paper.text_for_llm)} (max {settings.max_paper_chars})")

    print("3. Executing Stage 1 extraction with open-weight LLM chain...")
    client = LLMClient(settings)
    meta, claims, warnings = await extract_claims_from_paper(sec_paper, client, settings)

    print("\n=== EXTRACTED PAPER METADATA ===")
    print(f"Title: {meta.title}")
    print(f"Citation label: {meta.citation_label}")
    print(f"Authors: {', '.join(meta.authors) if meta.authors else 'None'}")
    print(f"Year: {meta.year}")
    print(f"Dataset: {meta.dataset}")
    print(f"Methodology: {meta.methodology}")
    print(f"Primary Metric: {meta.primary_metric}")
    print(f"Core Conclusion: {meta.core_conclusion}")

    print(f"\n=== VERIFIED CLAIMS ({len(claims)}) ===")
    for idx, c in enumerate(claims, start=1):
        print(f"\n[{idx}] Claim ID: {c.claim_id} | Type: {c.claim_type.value} | Topic: {c.topic_hint}")
        print(f"    Statement: {c.statement}")
        print(f"    Provenance: Page {c.provenance.page_number} ({c.provenance.section.value})")
        print(f"    Verbatim Quote: \"{c.provenance.verbatim_quote}\"")

    if warnings:
        print(f"\n=== WARNINGS ({len(warnings)}) ===")
        for w in warnings:
            print(f"  - {w}")


if __name__ == "__main__":
    asyncio.run(main())
