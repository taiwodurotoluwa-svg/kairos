import asyncio
import time
import pytest
import pymupdf
from app.config import get_settings
from app.errors import KairosError
from app.schemas import ErrorCode, SectionName
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
    """Verifies that large documents are budgeted to <= MAX_PAPER_CHARS (24,000 chars)."""
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


def test_no_headings_fallback():
    """Verifies that unsectioned PDFs fall back to 6k head (ABSTRACT) and 18k tail (OTHER)."""
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
    """Enforces min_papers (2), max_papers (10), and size limits."""
    settings = get_settings()
    valid_pdf = _create_test_pdf_bytes({"Abstract": "A" * 300}, "Paper")

    # Less than 2 papers
    with pytest.raises(KairosError) as exc_info:
        validate_inputs([("p1.pdf", valid_pdf)], [], settings)
    assert exc_info.value.code == ErrorCode.TOO_FEW_PAPERS

    # More than 10 papers
    lots_of_files = [(f"p{i}.pdf", valid_pdf + bytes([i])) for i in range(11)]
    with pytest.raises(KairosError) as exc_info:
        validate_inputs(lots_of_files, [], settings)
    assert exc_info.value.code == ErrorCode.TOO_MANY_PAPERS


def test_duplicate_file_deduplication():
    """De-duplicates identical uploaded files by SHA-256 hash."""
    settings = get_settings()
    pdf_bytes = _create_test_pdf_bytes({"Abstract": "Content " * 50}, "Paper")

    # Upload identical bytes with different names
    files = [("copy1.pdf", pdf_bytes), ("copy2.pdf", pdf_bytes), ("p3.pdf", pdf_bytes + b"\n%extra")]
    deduped_files, _ = validate_inputs(files, [], settings)
    assert len(deduped_files) == 2


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
