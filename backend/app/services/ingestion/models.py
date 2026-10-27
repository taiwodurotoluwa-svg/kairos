from dataclasses import dataclass, field
from typing import Optional
from app.schemas import SectionName, PaperSource


@dataclass
class ParsedPdf:
    page_texts: dict[int, str]  # 1-indexed: 1 -> text
    page_count: int
    meta_title: Optional[str] = None
    char_count: int = 0


@dataclass
class SectionedPaper:
    paper_id: str  # e.g. "p1", "p2", ...
    title: str
    text_for_llm: str
    sections_found: list[SectionName]
    page_texts: dict[int, str]
    page_count: int
    source: PaperSource
    arxiv_id: Optional[str] = None
    filename: Optional[str] = None


@dataclass
class IngestedBatch:
    papers: list[SectionedPaper]
    warnings: list[str] = field(default_factory=list)
