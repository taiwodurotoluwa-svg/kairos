import re
from typing import Any
from pydantic import BaseModel, Field, field_validator
from app.config import Settings
from app.schemas import (
    ClaimType,
    ExtractedClaim,
    PaperMetadata,
    PaperSource,
    Provenance,
    SectionName,
)
from app.services.ingestion.models import SectionedPaper
from app.services.llm.client import LLMClient
from app.services.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT_TEMPLATE,
)
from app.services.quote_verifier import verify_quote


class RawClaim(BaseModel):
    """Raw extracted claim from LLM response before quote verification."""
    claim_type: ClaimType
    topic_hint: str
    statement: str
    metric_value: str | None = None
    section: SectionName
    page_number: int
    verbatim_quote: str

    @field_validator("statement")
    @classmethod
    def clamp_statement(cls, v: str) -> str:
        return v.strip()[:280]

    @field_validator("page_number")
    @classmethod
    def check_page_number(cls, v: int) -> int:
        return max(1, v)


class RawExtraction(BaseModel):
    """Raw structured extraction response matching 03-open-weight-models.md SCHEMA."""
    title: str = "Untitled Paper"
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    dataset: str = "Not reported"
    sample_size: str | None = None
    methodology: str = "Not reported"
    primary_metric: str = "Not reported"
    limitations: str = "Not reported"
    core_conclusion: str = "Not reported"
    claims: list[RawClaim] = Field(default_factory=list)


def _generate_citation_label(authors: list[str], year: int | None, title: str) -> str:
    """Generates an academic citation label like 'Vaswani et al. (2017)' or 'Attention Is All... (2017)'."""
    year_str = str(year) if year else "n.d."

    if authors:
        first = authors[0].strip()
        last_name = first.split()[-1] if first else "Anonymous"
        if len(authors) == 1:
            return f"{last_name} ({year_str})"
        elif len(authors) == 2:
            second_last = authors[1].split()[-1] if authors[1].strip() else "Co-author"
            return f"{last_name} & {second_last} ({year_str})"
        else:
            return f"{last_name} et al. ({year_str})"

    clean_title = re.sub(r"[^\w\s]", "", title).strip()
    words = clean_title.split()[:3]
    prefix = " ".join(words) if words else "Study"
    return f"{prefix} ({year_str})"


async def extract_claims_from_paper(
    sec_paper: SectionedPaper,
    llm_client: LLMClient,
    settings: Settings | None = None,
) -> tuple[PaperMetadata, list[ExtractedClaim], list[str]]:
    """
    Runs Stage 1 extraction on a sectioned paper:
    1. Submits sectioned text with [[SECTION: X]] and [[PAGE n]] markers to open-weight LLM.
    2. Validates output with RawExtraction schema and executes corrective retry if needed.
    3. Verifies every claim's quote against raw page text (anti-hallucination filter).
    4. Drops unverified/hallucinated quotes and corrects page numbers if displaced.
    5. Assembles PaperMetadata and ExtractedClaim list with exact Provenance.
    Returns:
        (PaperMetadata, list[ExtractedClaim], list[warning_strings])
    """
    user_prompt = EXTRACTION_USER_PROMPT_TEMPLATE.format(
        filename=sec_paper.filename or f"{sec_paper.paper_id}.pdf",
        sectioned_text=sec_paper.text_for_llm,
    )

    raw_data, provider_name, model_id = await llm_client.complete_json(
        system=EXTRACTION_SYSTEM_PROMPT,
        user=user_prompt,
        max_tokens=1800,
        temperature=0.1,
        validate=RawExtraction.model_validate,
    )

    # Resolve title
    final_title = sec_paper.title
    if raw_data.title and len(raw_data.title.strip()) > 5 and not raw_data.title.lower().startswith("untitled"):
        final_title = raw_data.title.strip()

    citation_label = _generate_citation_label(raw_data.authors, raw_data.year, final_title)

    num_match = re.search(r"\d+", sec_paper.paper_id)
    paper_num = int(num_match.group(0)) if num_match else 1
    short_label = f"P{paper_num}"
    palette_index = (paper_num - 1) % 8

    paper_meta = PaperMetadata(
        paper_id=sec_paper.paper_id,
        short_label=short_label,
        citation_label=citation_label,
        palette_index=palette_index,
        source=sec_paper.source,
        arxiv_id=sec_paper.arxiv_id,
        filename=sec_paper.filename,
        title=final_title,
        authors=raw_data.authors,
        year=raw_data.year,
        page_count=sec_paper.page_count,
        sections_found=sec_paper.sections_found,
        dataset=raw_data.dataset or "Not reported",
        sample_size=raw_data.sample_size,
        methodology=raw_data.methodology or "Not reported",
        primary_metric=raw_data.primary_metric or "Not reported",
        limitations=raw_data.limitations or "Not reported",
        core_conclusion=raw_data.core_conclusion or "Not reported",
        extraction_model=model_id,
    )

    warnings: list[str] = []
    kept_claims: list[ExtractedClaim] = []
    dropped_count = 0

    claim_counter = 1
    for raw_claim in raw_data.claims:
        # Verify quote against raw page texts
        verified = verify_quote(
            quote=raw_claim.verbatim_quote,
            pages=sec_paper.page_texts,
            claimed_page=raw_claim.page_number,
        )

        if verified is None:
            dropped_count += 1
            continue

        true_quote, verified_page = verified

        prov = Provenance(
            paper_id=sec_paper.paper_id,
            paper_title=final_title,
            section=raw_claim.section,
            page_number=verified_page,
            verbatim_quote=true_quote,
        )

        claim_id = f"{sec_paper.paper_id}c{claim_counter}"
        claim_counter += 1

        extracted_claim = ExtractedClaim(
            claim_id=claim_id,
            paper_id=sec_paper.paper_id,
            claim_type=raw_claim.claim_type,
            topic_hint=raw_claim.topic_hint.strip(),
            statement=raw_claim.statement.strip(),
            metric_value=raw_claim.metric_value,
            provenance=prov,
        )
        kept_claims.append(extracted_claim)

    if dropped_count > 0:
        warnings.append(
            f"Paper '{final_title}' ({sec_paper.paper_id}): dropped {dropped_count} unverified or hallucinated claim quote(s)."
        )

    if len(kept_claims) < 2:
        warnings.append(
            f"Paper '{final_title}' ({sec_paper.paper_id}) yielded only {len(kept_claims)} verified claim(s)."
        )

    return paper_meta, kept_claims, warnings
