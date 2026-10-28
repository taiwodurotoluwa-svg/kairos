import asyncio
import time
import pytest
import pymupdf
import httpx
from app.config import Settings, get_settings
from app.errors import KairosError
from app.schemas import ErrorCode, SectionName
from app.services.ingestion.models import ParsedPdf
from app.services.ingestion.pdf_parser import parse_pdf
from app.services.ingestion.sectioner import section_paper
from app.services.ingestion.validators import validate_inputs
from app.services.ingestion.coordinator import ingest_all


def _create_test_pdf_bytes(sections: dict[str, str], title: str = "Test Study") -> bytes:
    """Helper creating an in-memory PDF document with custom text sections and metadata."""
    doc = pymupdf.open()
    doc.set_metadata({"title": title, "author": "Kairos Test Team"})

    # Page 1
    page1 = doc.new_page(width=595, height=842)
    y = 50
    page1.insert_text((50, y), f"Title: {title}", fontsize=16)
    y += 30

    for heading, text in sections.items():
        if y > 720:
            page = doc.new_page(width=595, height=842)
            y = 50
        else:
            page = doc[-1]

        page.insert_text((50, y), heading, fontsize=12)
        y += 20
        # Insert body text in lines
        lines = text.split("\n")
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if y > 760:
                page = doc.new_page(width=595, height=842)
                y = 50
            page.insert_text((50, y), line_str, fontsize=10)
            y += 15
        y += 10

    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_valid_pdf_parsing_and_page_indexing():
    """Verifies that PyMuPDF parses pages, extracts 1-indexed page_texts, and detects titles."""
    sections = {
        "1. Abstract": "This study analyzes clinical diagnostic metrics across diverse multi-site hospital datasets.\n" * 10,
        "2. Methods": "We trained deep neural networks using 5-fold cross validation on balanced cohorts.\n" * 15,
        "3. Results": "The model achieved 94.2% sensitivity and 89.1% specificity across all validation sets.\n" * 15,
        "4. Discussion": "Our findings demonstrate substantial gains in sensitivity while maintaining low false-positive rates.\n" * 10,
        "References": "1. Smith et al. Nature Medicine 2024.\n2. Doe et al. Lancet Digital Health 2023.\n",
    }
    data = _create_test_pdf_bytes(sections, title="Deep Diagnostic Evaluation")

    parsed = parse_pdf(data, "test_paper.pdf")
    assert parsed.page_count >= 2
    assert 1 in parsed.page_texts
    assert 2 in parsed.page_texts
    assert parsed.meta_title == "Deep Diagnostic Evaluation"
    assert parsed.char_count > 1000


def test_sectioning_and_stop_at_references():
    """Verifies section recognition, stop-at-references truncation, and model marker insertion."""
    sections = {
        "Abstract": "This paper presents a formal evaluation of medical imaging models under distribution shifts.\n" * 5,
        "Methodology": "High-resolution radiography scans were preprocessed using standard normalization pipelines.\n" * 8,
        "Results": "Across external validation cohorts, receiver operating characteristic curves demonstrated robust AUC.\n" * 8,
        "Conclusion": "In conclusion, distribution-robust architectures are critical for real-world clinical safety.\n" * 5,
        "References": "Discarded reference line 1.\nDiscarded bibliography item 2.\n",
    }
    data = _create_test_pdf_bytes(sections, title="Clinical Evaluation")
    parsed = parse_pdf(data, "clinical.pdf")

    sec_paper = section_paper(
        parsed=parsed,
        paper_id="p1",
        title=parsed.meta_title or "Clinical Evaluation",
        source="UPLOAD",
        filename="clinical.pdf",
    )

    # Check sections detected
    assert SectionName.ABSTRACT in sec_paper.sections_found
    assert SectionName.METHODOLOGY in sec_paper.sections_found
    assert SectionName.RESULTS in sec_paper.sections_found
    assert SectionName.CONCLUSION in sec_paper.sections_found

    # Check markers
    assert "[[SECTION: ABSTRACT]]" in sec_paper.text_for_llm
    assert "[[SECTION: RESULTS]]" in sec_paper.text_for_llm
    assert "[[PAGE 1]]" in sec_paper.text_for_llm

    # Check references are excluded
    assert "Discarded reference line 1" not in sec_paper.text_for_llm
    assert "Discarded bibliography item 2" not in sec_paper.text_for_llm


def test_character_budget_enforcement():
    """Verifies that large documents are budgeted to <= MAX_PAPER_CHARS (24,000 chars) with marker headroom."""
    settings = get_settings()
    huge_text = "Standard evaluation metric analysis for clinical safety and model interpretability. " * 500
    sections = {
        "Abstract": huge_text[:4000],
        "Methodology": huge_text[:9000],
        "Results": huge_text[:12000],
        "Discussion": huge_text[:8000],
        "References": "Ref 1. Ref 2.",
    }
    data = _create_test_pdf_bytes(sections, title="Huge Paper")
    parsed = parse_pdf(data, "huge.pdf")

    sec_paper = section_paper(
        parsed=parsed,
        paper_id="p1",
        title="Huge Paper",
        source="UPLOAD",
        settings=settings,
    )

    assert len(sec_paper.text_for_llm) <= settings.max_paper_chars
    # Asserts that markers are not cut off mid-marker
    assert not sec_paper.text_for_llm.endswith("[[PAGE")
    assert not sec_paper.text_for_llm.endswith("[[SECTION:")


def test_no_headings_fallback():
    """Verifies that unsectioned PDFs fall back to head (ABSTRACT) and tail (OTHER)."""
    text_blob = "Continuous unsectioned scientific narrative describing experimental protocols and results. " * 30
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    p.insert_textbox(pymupdf.Rect(50, 50, 500, 750), text_blob, fontsize=10)
    data = doc.tobytes()
    doc.close()

    parsed = parse_pdf(data, "unsectioned.pdf")
    sec_paper = section_paper(
        parsed=parsed,
        paper_id="p1",
        title="Unsectioned Paper",
        source="UPLOAD",
    )

    assert SectionName.ABSTRACT in sec_paper.sections_found
    assert SectionName.OTHER in sec_paper.sections_found
    assert len(sec_paper.text_for_llm) <= 24000


def test_unsectioned_head_tail_preservation():
    """Missing Test 3: Verifies that 15,000-char unsectioned paper across multiple pages preserves head and tail."""
    page_texts: dict[int, str] = {}
    for i in range(1, 6):
        page_texts[i] = f"Page {i} content describing distinct experimental observation phase {i}. " * 40

    parsed = ParsedPdf(
        page_texts=page_texts,
        page_count=5,
        meta_title="Multi-page Unsectioned Study",
        char_count=sum(len(t) for t in page_texts.values())
    )

    sec_paper = section_paper(
        parsed=parsed,
        paper_id="p1",
        title="Multi-page Unsectioned Study",
        source="UPLOAD",
    )

    assert SectionName.ABSTRACT in sec_paper.sections_found
    assert SectionName.OTHER in sec_paper.sections_found
    assert "[[SECTION: ABSTRACT]]" in sec_paper.text_for_llm
    assert "[[SECTION: OTHER]]" in sec_paper.text_for_llm
    # Verifies page 1 (head) and page 5 (tail) are both retained
    assert "[[PAGE 1]]" in sec_paper.text_for_llm
    assert "[[PAGE 5]]" in sec_paper.text_for_llm
    assert "observation phase 5" in sec_paper.text_for_llm
    assert len(sec_paper.text_for_llm) <= 24000


def test_invalid_file_type_magic_bytes():
    """Rejects non-PDF files missing %PDF- header."""
    settings = get_settings()
    files = [("doc.txt", b"Hello, this is just plain text, not a PDF!")]
    with pytest.raises(KairosError) as exc_info:
        validate_inputs(files, [], settings)
    assert exc_info.value.code == ErrorCode.INVALID_FILE_TYPE


def test_scanned_pdf_no_text_layer():
    """Rejects PDFs lacking extractable text layer (< 200 chars/page)."""
    doc = pymupdf.open()
    p = doc.new_page(width=595, height=842)
    # Insert fewer than 20 chars
    p.insert_text((50, 50), "Scanned image only", fontsize=10)
    data = doc.tobytes()
    doc.close()

    with pytest.raises(KairosError) as exc_info:
        parse_pdf(data, "scanned.pdf")
    assert exc_info.value.code == ErrorCode.NO_TEXT_LAYER


def test_corrupt_pdf_parse_failed():
    """Rejects corrupt PDF data with PDF_PARSE_FAILED."""
    corrupt_data = b"%PDF-1.4\nSome invalid garbage that cannot be parsed by pymupdf."
    with pytest.raises(KairosError) as exc_info:
        parse_pdf(corrupt_data, "corrupt.pdf")
    assert exc_info.value.code == ErrorCode.PDF_PARSE_FAILED


def test_paper_count_and_size_limits():
    """Missing Test 1: Enforces min_papers (2), max_papers (10), and size limits (FILE_TOO_LARGE)."""
    valid_pdf = _create_test_pdf_bytes({"Abstract": "A\n" * 300}, "Paper")

    # Custom settings with 1MB file cap and 2MB total cap
    tight_settings = Settings(max_file_mb=1, max_total_mb=2, min_papers=2, max_papers=10)

    # 1. Per-file limit: 2MB file exceeds 1MB limit -> FILE_TOO_LARGE
    oversized_file = [(
        "huge.pdf",
        b"%PDF-1.5\n" + b"x" * (2 * 1024 * 1024)
    )]
    with pytest.raises(KairosError) as exc_info:
        validate_inputs(oversized_file, [], tight_settings)
    assert exc_info.value.code == ErrorCode.FILE_TOO_LARGE
    assert exc_info.value.status_code == 413

    # 2. Total file limit: two 1.2MB files exceed 2MB total limit -> FILE_TOO_LARGE
    medium_file1 = ("m1.pdf", b"%PDF-1.5\n" + b"1" * int(1.2 * 1024 * 1024))
    medium_file2 = ("m2.pdf", b"%PDF-1.5\n" + b"2" * int(1.2 * 1024 * 1024))
    with pytest.raises(KairosError) as exc_info:
        validate_inputs([medium_file1, medium_file2], [], tight_settings)
    assert exc_info.value.code == ErrorCode.FILE_TOO_LARGE
    assert exc_info.value.status_code == 413

    # 3. Less than 2 papers
    default_settings = get_settings()
    with pytest.raises(KairosError) as exc_info:
        validate_inputs([("p1.pdf", valid_pdf)], [], default_settings)
    assert exc_info.value.code == ErrorCode.TOO_FEW_PAPERS

    # 4. More than 10 papers
    lots_of_files = [(f"p{i}.pdf", valid_pdf + bytes([i])) for i in range(11)]
    with pytest.raises(KairosError) as exc_info:
        validate_inputs(lots_of_files, [], default_settings)
    assert exc_info.value.code == ErrorCode.TOO_MANY_PAPERS


def test_duplicate_file_deduplication():
    """De-duplicates identical uploaded files by SHA-256 hash."""
    settings = get_settings()
    pdf_bytes = _create_test_pdf_bytes({"Abstract": "Content line for duplicate test.\n" * 20}, "Paper")

    # Upload identical bytes with different names
    files = [("copy1.pdf", pdf_bytes), ("copy2.pdf", pdf_bytes), ("p3.pdf", pdf_bytes + b"\n%extra")]
    deduped_files, _ = validate_inputs(files, [], settings)
    assert len(deduped_files) == 2


def test_cross_format_and_cross_source_deduplication():
    """Missing Test 2: Verifies cross-format arXiv deduplication in validators and cross-source SHA-256 deduplication in coordinator."""
    settings = get_settings()
    valid_pdf = _create_test_pdf_bytes({"Abstract": "Paper content line describing experimental methods.\n" * 20}, "Paper")
    p2_pdf = _create_test_pdf_bytes({"Abstract": "Different paper content line describing validation methods.\n" * 20}, "Distinct Paper")

    # 1. Cross-format arXiv deduplication inside validate_inputs
    arxiv_variations = [
        "2309.12345",
        "arxiv:2309.12345v2",
        "https://arxiv.org/abs/2309.12345v1",
        "https://arxiv.org/pdf/2309.12345.pdf",
    ]
    # Provide 1 valid upload + 4 arXiv variations of the SAME paper
    deduped_files, deduped_arxiv = validate_inputs([("p1.pdf", valid_pdf)], arxiv_variations, settings)
    assert len(deduped_arxiv) == 1
    assert deduped_arxiv[0] == "2309.12345"

    # 2. Cross-source SHA-256 deduplication inside coordinator.ingest_all
    async def _run_coordinator_dedup():
        files = [("upload1.pdf", valid_pdf), ("upload2.pdf", p2_pdf)]
        arxiv_ids = ["2309.12345"]  # returns valid_pdf (duplicate of upload1.pdf)

        import app.services.ingestion.coordinator as coord_mod
        orig_fetch = coord_mod.fetch_all_arxiv

        async def mock_fetch(a_ids, s):
            return [("2309.12345", "arxiv_2309.12345.pdf", valid_pdf)], []

        coord_mod.fetch_all_arxiv = mock_fetch
        try:
            batch = await ingest_all(files, arxiv_ids, settings)
            # upload1 and upload2 survive, arXiv duplicate is skipped
            assert len(batch.papers) == 2
            assert any("duplicate" in w.lower() for w in batch.warnings)
        finally:
            coord_mod.fetch_all_arxiv = orig_fetch

    asyncio.run(_run_coordinator_dedup())


def test_8_pdfs_concurrent_parsing_benchmark():
    """Acceptance criterion: 8 PDFs parsed concurrently in < 2 seconds."""
    async def _run():
        settings = get_settings()
        files = []
        for i in range(1, 9):
            sections = {
                "Abstract": f"Abstract for simulated benchmark paper {i}.\n" * 10,
                "Methodology": f"Methods section discussing architecture {i}.\n" * 15,
                "Results": f"Experimental results demonstrating performance {i}.\n" * 15,
                "References": "Reference 1.\n",
            }
            data = _create_test_pdf_bytes(sections, title=f"Benchmark Paper {i}")
            files.append((f"paper_{i}.pdf", data))

        start = time.perf_counter()
        batch = await ingest_all(files, [], settings)
        duration = time.perf_counter() - start

        assert len(batch.papers) == 8
        assert duration < 2.0, f"Concurrent parsing took {duration:.2f}s, expected < 2.0s"
        assert [p.paper_id for p in batch.papers] == [f"p{i}" for i in range(1, 9)]

    asyncio.run(_run())
