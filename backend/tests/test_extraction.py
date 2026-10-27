import asyncio
from unittest.mock import AsyncMock
import pytest
from app.schemas import ClaimType, PaperSource, SectionName
from app.services.extraction import extract_claims_from_paper, RawExtraction, RawClaim
from app.services.ingestion.models import SectionedPaper
from app.services.llm.client import LLMClient
from app.services.prompts.extraction import (
    EXTRACTION_SYSTEM_PROMPT,
    EXTRACTION_USER_PROMPT_TEMPLATE,
    CORRECTIVE_RETRY_TEMPLATE,
)


def test_extraction_system_prompt_matches_contract_rules():
    """Acceptance criterion: Asserts the extraction system prompt contains all 10 numbered hard rules."""
    assert "HARD RULES" in EXTRACTION_SYSTEM_PROMPT
    assert "1. Output ONLY one JSON object that matches the SCHEMA below." in EXTRACTION_SYSTEM_PROMPT
    assert "2. Use ONLY information present in the PAPER TEXT." in EXTRACTION_SYSTEM_PROMPT
    assert "3. Every claim MUST include \"verbatim_quote\":" in EXTRACTION_SYSTEM_PROMPT
    assert "4. \"page_number\" is the integer n of the nearest preceding [[PAGE n]] marker before the quote." in EXTRACTION_SYSTEM_PROMPT
    assert "5. \"section\" is the name in the nearest preceding [[SECTION: NAME]] marker" in EXTRACTION_SYSTEM_PROMPT
    assert "6. Extract between 4 and 6 atomic claims." in EXTRACTION_SYSTEM_PROMPT
    assert "7. Include at least one claim of type CONCLUSION." in EXTRACTION_SYSTEM_PROMPT
    assert "8. \"claim_type\" is one of: EMPIRICAL_RESULT, METHOD, LIMITATION, CONCLUSION." in EXTRACTION_SYSTEM_PROMPT
    assert "9. \"topic_hint\" is a 2-6 word noun phrase" in EXTRACTION_SYSTEM_PROMPT
    assert "10. \"year\" is the 4-digit publication year if printed in the text, otherwise null." in EXTRACTION_SYSTEM_PROMPT


def test_extract_claims_from_paper_success_and_provenance():
    """Verifies end-to-end claim extraction, citation label generation, and verbatim quote verification."""
    async def _run():
        page_texts = {
            1: "Title: Deep Learning in Chest Radiography\nAbstract: We evaluate chest radiography models.",
            2: "Methods: Balanced datasets were gathered across 3 hospital networks.",
            3: "Results: The proposed architecture demonstrated 94.2% diagnostic sensitivity in external validation cohorts.",
            4: "Conclusion: Model calibration under distribution shift remains essential for patient safety.",
        }

        sec_paper = SectionedPaper(
            paper_id="p1",
            title="Deep Learning in Chest Radiography",
            text_for_llm="[[SECTION: ABSTRACT]]\n[[PAGE 1]]\nAbstract text...\n[[SECTION: RESULTS]]\n[[PAGE 3]]\nThe proposed architecture demonstrated 94.2% diagnostic sensitivity in external validation cohorts.",
            sections_found=[SectionName.ABSTRACT, SectionName.RESULTS, SectionName.CONCLUSION],
            page_texts=page_texts,
            page_count=4,
            source=PaperSource.UPLOAD,
            filename="chest_rad.pdf",
        )

        mock_raw = RawExtraction(
            title="Deep Learning in Chest Radiography",
            authors=["Jane Doe", "Alex Smith"],
            year=2024,
            dataset="MIMIC-CXR and CheXpert",
            sample_size="10,000 scans",
            methodology="Deep convolutional neural network with temperature scaling",
            primary_metric="Sensitivity and specificity",
            limitations="External multi-center validation limited to 3 hospital sites",
            core_conclusion="Distribution shift calibration is critical for real-world clinical deployment",
            claims=[
                RawClaim(
                    claim_type=ClaimType.EMPIRICAL_RESULT,
                    topic_hint="diagnostic sensitivity",
                    statement="The proposed architecture achieved 94.2% sensitivity in external validation.",
                    metric_value="94.2%",
                    section=SectionName.RESULTS,
                    page_number=3,
                    verbatim_quote="The proposed architecture demonstrated 94.2% diagnostic sensitivity in external validation cohorts.",
                ),
                RawClaim(
                    claim_type=ClaimType.CONCLUSION,
                    topic_hint="clinical safety",
                    statement="Model calibration under distribution shift is essential for patient safety.",
                    section=SectionName.CONCLUSION,
                    page_number=4,
                    verbatim_quote="Model calibration under distribution shift remains essential for patient safety.",
                ),
            ],
        )

        mock_llm_client = AsyncMock(spec=LLMClient)
        mock_llm_client.complete_json.return_value = (mock_raw, "groq", "llama-3.1-8b-instant")

        meta, claims, warnings = await extract_claims_from_paper(sec_paper, mock_llm_client)

        # 1. Paper metadata checks
        assert meta.paper_id == "p1"
        assert meta.title == "Deep Learning in Chest Radiography"
        assert meta.citation_label == "Doe & Smith (2024)"
        assert meta.dataset == "MIMIC-CXR and CheXpert"

        # 2. Claim checks
        assert len(claims) == 2
        assert claims[0].claim_id == "p1c1"
        assert claims[0].claim_type == ClaimType.EMPIRICAL_RESULT
        assert claims[0].provenance.page_number == 3
        assert claims[0].provenance.verbatim_quote == "The proposed architecture demonstrated 94.2% diagnostic sensitivity in external validation cohorts."

        assert claims[1].claim_id == "p1c2"
        assert claims[1].claim_type == ClaimType.CONCLUSION
        assert claims[1].provenance.page_number == 4

        # 3. Warnings check
        assert len(warnings) == 0

    asyncio.run(_run())


def test_extract_claims_drops_hallucinated_quotes_and_warns():
    """Verifies that unverified/hallucinated quotes are dropped and warnings are recorded."""
    async def _run():
        page_texts = {
            1: "Solar microgrid control algorithms under intermittent cloud cover.",
            2: "Evaluation of battery state-of-charge degradation over 5-year cycles.",
        }

        sec_paper = SectionedPaper(
            paper_id="p2",
            title="Solar Microgrid Reliability",
            text_for_llm="[[SECTION: ABSTRACT]]\n[[PAGE 1]]\nSolar microgrid text.",
            sections_found=[SectionName.ABSTRACT],
            page_texts=page_texts,
            page_count=2,
            source=PaperSource.UPLOAD,
        )

        mock_raw = RawExtraction(
            title="Solar Microgrid Reliability",
            authors=["Alice Wonder"],
            year=2023,
            claims=[
                # Valid quote
                RawClaim(
                    claim_type=ClaimType.METHOD,
                    topic_hint="battery life",
                    statement="Battery state-of-charge was evaluated over 5-year operational cycles.",
                    section=SectionName.METHODOLOGY,
                    page_number=2,
                    verbatim_quote="battery state-of-charge degradation over 5-year cycles.",
                ),
                # Fabricated quote not in page_texts
                RawClaim(
                    claim_type=ClaimType.EMPIRICAL_RESULT,
                    topic_hint="efficiency gain",
                    statement="Solar panels achieved 99.9% energy conversion efficiency.",
                    section=SectionName.RESULTS,
                    page_number=1,
                    verbatim_quote="Solar panels achieved 99.9% energy conversion efficiency without degradation.",
                ),
            ],
        )

        mock_llm_client = AsyncMock(spec=LLMClient)
        mock_llm_client.complete_json.return_value = (mock_raw, "groq", "llama-3.1-8b-instant")

        meta, claims, warnings = await extract_claims_from_paper(sec_paper, mock_llm_client)

        # 1 valid claim kept, 1 hallucinated dropped
        assert len(claims) == 1
        assert claims[0].claim_id == "p2c1"
        assert any("dropped 1 unverified" in w for w in warnings)
        assert any("yielded only 1 verified claim" in w for w in warnings)

    asyncio.run(_run())
