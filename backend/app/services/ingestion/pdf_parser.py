import re
import threading
import pymupdf
from app.errors import KairosError
from app.schemas import ErrorCode
from app.services.ingestion.models import ParsedPdf

_MUPDF_LOCK = threading.Lock()


def _dehyphenate(text: str) -> str:
    """Rejoins soft-hyphenated words split across line breaks while preserving compound hyphens (Opt 4)."""
    def _repl(m: re.Match) -> str:
        prefix, suffix = m.group(1), m.group(2)
        if prefix.lower() in {"self", "multi", "cross", "non", "pre", "post", "co", "low", "high", "out", "inter", "intra"} or prefix.isdigit():
            return f"{prefix}-{suffix}"
        return f"{prefix}{suffix}"
    return re.sub(r"(\w+)-\n([a-z]\w*)", _repl, text)


def _clean_text(text: str) -> str:
    """Normalises paragraph breaks and removes non-printable control characters."""
    text = _dehyphenate(text)
    # Remove control characters except standard whitespace
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    # Normalise 3+ newlines to double newline
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_pdf(data: bytes, filename: str = "paper.pdf") -> ParsedPdf:
    """
    Parses a PDF from bytes using PyMuPDF.
    - Protected by module-level lock (_MUPDF_LOCK) for C-library thread safety.
    - Extracts text per page (1-indexed) in document stream order (sort=False) to preserve two-column layouts.
    - Checks for sufficient text density (>= 200 mean chars/page).
    - Extracts metadata title if available.
    - Raises KairosError(NO_TEXT_LAYER) or KairosError(PDF_PARSE_FAILED).
    """
    with _MUPDF_LOCK:
        try:
            doc = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise KairosError(
                ErrorCode.PDF_PARSE_FAILED,
                f"Failed to open or parse PDF '{filename}': {exc}",
                400
            ) from exc

        try:
            page_count = len(doc)
            if page_count == 0:
                raise KairosError(
                    ErrorCode.PDF_PARSE_FAILED,
                    f"PDF '{filename}' contains 0 pages.",
                    400
                )

            page_texts: dict[int, str] = {}
            total_chars = 0

            for page_idx, page in enumerate(doc, start=1):
                # Use sort=False (stream/reading order) to prevent column interleaving in multi-column layouts
                raw_text = page.get_text("text", sort=False)
                cleaned = _clean_text(raw_text)
                page_texts[page_idx] = cleaned
                total_chars += len(cleaned)

            # Scanned PDF check: mean chars per page must be >= 200
            mean_chars = total_chars / page_count
            if mean_chars < 200:
                raise KairosError(
                    ErrorCode.NO_TEXT_LAYER,
                    f"PDF '{filename}' appears to be scanned or lacks an extractable text layer "
                    f"(mean {mean_chars:.0f} chars/page < 200).",
                    400
                )

            # Meta title extraction
            meta_title = None
            if doc.metadata:
                raw_title = doc.metadata.get("title", "")
                if raw_title and len(raw_title.strip()) > 4 and not raw_title.lower().startswith("untitled"):
                    meta_title = raw_title.strip()

            return ParsedPdf(
                page_texts=page_texts,
                page_count=page_count,
                meta_title=meta_title,
                char_count=total_chars
            )
        finally:
            doc.close()
