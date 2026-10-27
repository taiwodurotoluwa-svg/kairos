import re
from app.config import Settings
from app.schemas import SectionName, PaperSource
from app.services.ingestion.models import ParsedPdf, SectionedPaper

HEADING_RE = re.compile(
    r"^\s*(?:\d+(?:\.\d+)*\.?|[IVX]+\.)?\s*(abstract|introduction|related work|background|method(?:s|ology)?|approach|"
    r"materials and methods|experimental setup|experiments?|implementation details|results?|evaluation|discussion|"
    r"conclusions?|limitations?|future work|references|bibliography|acknowledg(?:e)?ments?)(?:\s*[:\.\-]?\s*$)",
    re.IGNORECASE | re.MULTILINE,
)

STOP_HEADINGS = {
    "references",
    "bibliography",
}

SECTION_MAP: dict[str, SectionName] = {
    "abstract": SectionName.ABSTRACT,
    "method": SectionName.METHODOLOGY,
    "methods": SectionName.METHODOLOGY,
    "methodology": SectionName.METHODOLOGY,
    "approach": SectionName.METHODOLOGY,
    "materials and methods": SectionName.METHODOLOGY,
    "experimental setup": SectionName.EXPERIMENTAL_SETUP,
    "experiments": SectionName.EXPERIMENTAL_SETUP,
    "implementation details": SectionName.EXPERIMENTAL_SETUP,
    "results": SectionName.RESULTS,
    "evaluation": SectionName.RESULTS,
    "discussion": SectionName.DISCUSSION,
    "conclusion": SectionName.CONCLUSION,
    "conclusions": SectionName.CONCLUSION,
    "limitation": SectionName.LIMITATIONS,
    "limitations": SectionName.LIMITATIONS,
    "introduction": SectionName.OTHER,
    "related work": SectionName.OTHER,
    "background": SectionName.OTHER,
    "future work": SectionName.OTHER,
    "acknowledgement": SectionName.OTHER,
    "acknowledgements": SectionName.OTHER,
    "acknowledgment": SectionName.OTHER,
    "acknowledgments": SectionName.OTHER,
}


def _classify_heading(raw_match: str) -> str | SectionName:
    norm = raw_match.strip().lower()
    if norm in STOP_HEADINGS:
        return "STOP"
    return SECTION_MAP.get(norm, SectionName.OTHER)


def section_paper(
    parsed: ParsedPdf,
    paper_id: str,
    title: str,
    source: PaperSource,
    arxiv_id: str | None = None,
    filename: str | None = None,
    settings: Settings | None = None,
) -> SectionedPaper:
    """
    Splits ParsedPdf page_texts into semantic sections with character budgeting and markers:
    [[SECTION: X]]
    [[PAGE n]]
    """
    max_chars = settings.max_paper_chars if settings else 24000

    # Stream of tuples: (page_num, section_name, text_segment)
    sections_found_set: set[SectionName] = set()
    raw_segments: list[tuple[int, SectionName, str]] = []

    current_section = SectionName.ABSTRACT
    stopped = False

    for page_num in sorted(parsed.page_texts.keys()):
        if stopped:
            break
        text = parsed.page_texts[page_num]
        if not text:
            continue

        # Find heading matches on this page
        matches = list(HEADING_RE.finditer(text))
        if not matches:
            # Entire page belongs to current section
            raw_segments.append((page_num, current_section, text))
            sections_found_set.add(current_section)
            continue

        last_pos = 0
        for m in matches:
            heading_word = m.group(1).lower().strip()
            heading_type = _classify_heading(heading_word)

            # Preceding text belongs to previous section
            pre_text = text[last_pos:m.start()].strip()
            if pre_text:
                raw_segments.append((page_num, current_section, pre_text))
                sections_found_set.add(current_section)

            if heading_type == "STOP":
                stopped = True
                break

            current_section = heading_type
            sections_found_set.add(current_section)
            last_pos = m.end()

        if not stopped and last_pos < len(text):
            trailing_text = text[last_pos:].strip()
            if trailing_text:
                raw_segments.append((page_num, current_section, trailing_text))
                sections_found_set.add(current_section)

    # 2. Check if meaningful headings were detected
    has_meaningful_headings = any(s != SectionName.ABSTRACT and s != SectionName.OTHER for s in sections_found_set)

    if not has_meaningful_headings:
        # Fallback to head/tail strategy: 6k head (ABSTRACT), up to 17k tail (OTHER) leaving 1k marker headroom
        total_avail = sum(len(t) for t in parsed.page_texts.values())
        if total_avail <= 6000:
            head_budget = max(200, total_avail // 2)
        else:
            head_budget = 6000

        tail_budget = max(0, max_chars - head_budget - 1000)

        head_segments: list[tuple[int, SectionName, str]] = []
        tail_candidates: list[tuple[int, str]] = []
        chars_left_head = head_budget

        for p in sorted(parsed.page_texts.keys()):
            t = parsed.page_texts[p]
            if not t:
                continue
            if chars_left_head > 0:
                if len(t) <= chars_left_head:
                    head_segments.append((p, SectionName.ABSTRACT, t))
                    chars_left_head -= len(t)
                else:
                    head_segments.append((p, SectionName.ABSTRACT, t[:chars_left_head]))
                    tail_candidates.append((p, t[chars_left_head:]))
                    chars_left_head = 0
            else:
                tail_candidates.append((p, t))

        # Build tail segments from remaining text
        total_tail_avail = sum(len(t) for _, t in tail_candidates)
        tail_segments: list[tuple[int, SectionName, str]] = []

        if total_tail_avail <= tail_budget:
            for p, t in tail_candidates:
                if t.strip():
                    tail_segments.append((p, SectionName.OTHER, t))
        else:
            # Take the final tail_budget characters from the end of the unsectioned paper
            chars_to_skip = total_tail_avail - tail_budget
            curr_skipped = 0
            for p, t in tail_candidates:
                if curr_skipped + len(t) <= chars_to_skip:
                    curr_skipped += len(t)
                    continue
                elif curr_skipped < chars_to_skip:
                    offset = chars_to_skip - curr_skipped
                    curr_skipped = chars_to_skip
                    tail_segments.append((p, SectionName.OTHER, t[offset:]))
                else:
                    tail_segments.append((p, SectionName.OTHER, t))

        output_parts: list[str] = ["[[SECTION: ABSTRACT]]"]
        for p, _, chunk in head_segments:
            if chunk.strip():
                output_parts.append(f"[[PAGE {p}]]\n{chunk}")

        if tail_segments:
            output_parts.append("[[SECTION: OTHER]]")
            for p, _, chunk in tail_segments:
                if chunk.strip():
                    output_parts.append(f"[[PAGE {p}]]\n{chunk}")

        text_for_llm = "\n\n".join(output_parts)
        if len(text_for_llm) > max_chars:
            text_for_llm = text_for_llm[:max_chars]

        sections_found = [SectionName.ABSTRACT]
        if tail_segments:
            sections_found.append(SectionName.OTHER)

        return SectionedPaper(
            paper_id=paper_id,
            title=title,
            text_for_llm=text_for_llm,
            sections_found=sections_found,
            page_texts=parsed.page_texts,
            page_count=parsed.page_count,
            source=source,
            arxiv_id=arxiv_id,
            filename=filename,
        )

    # 3. Apply Group Character Budgets:
    # 2500 + 6500 + 7500 + 5500 + 1000 = 23,000 chars total, leaving ~1,000 chars headroom for markers
    group_budgets = {
        "abstract": 2500,
        "methods": 6500,
        "results": 7500,
        "discussion": 5500,
    }

    group_mapping = {
        SectionName.ABSTRACT: "abstract",
        SectionName.METHODOLOGY: "methods",
        SectionName.EXPERIMENTAL_SETUP: "methods",
        SectionName.RESULTS: "results",
        SectionName.DISCUSSION: "discussion",
        SectionName.CONCLUSION: "discussion",
        SectionName.LIMITATIONS: "discussion",
        SectionName.OTHER: "other",
    }

    grouped_segments: dict[str, list[tuple[int, SectionName, str]]] = {
        "abstract": [],
        "methods": [],
        "results": [],
        "discussion": [],
        "other": [],
    }

    for p, sec, text in raw_segments:
        grp = group_mapping.get(sec, "other")
        grouped_segments[grp].append((p, sec, text))

    budgeted_output_by_group: dict[str, list[tuple[int, SectionName, str]]] = {}
    for grp, segs in grouped_segments.items():
        budget = group_budgets.get(grp, 1000)
        curr_chars = 0
        kept_segs = []
        for p, sec, t in segs:
            rem = budget - curr_chars
            if rem <= 0:
                break
            if len(t) <= rem:
                kept_segs.append((p, sec, t))
                curr_chars += len(t)
            else:
                kept_segs.append((p, sec, t[:rem]))
                curr_chars += rem
                break
        budgeted_output_by_group[grp] = kept_segs

    # 4. Construct model-ready text with markers
    ordered_groups = ["abstract", "methods", "results", "discussion", "other"]
    output_sections: list[str] = []
    final_sections_found: list[SectionName] = []

    for grp in ordered_groups:
        segs = budgeted_output_by_group.get(grp, [])
        if not segs:
            continue

        curr_sec = None
        for p, sec, chunk in segs:
            if not chunk.strip():
                continue
            if sec not in final_sections_found:
                final_sections_found.append(sec)

            if sec != curr_sec:
                output_sections.append(f"[[SECTION: {sec.value}]]")
                curr_sec = sec

            output_sections.append(f"[[PAGE {p}]]\n{chunk}")

    text_for_llm = "\n\n".join(output_sections)
    if len(text_for_llm) > max_chars:
        text_for_llm = text_for_llm[:max_chars]

    return SectionedPaper(
        paper_id=paper_id,
        title=title,
        text_for_llm=text_for_llm,
        sections_found=final_sections_found,
        page_texts=parsed.page_texts,
        page_count=parsed.page_count,
        source=source,
        arxiv_id=arxiv_id,
        filename=filename,
    )
