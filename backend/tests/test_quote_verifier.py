import pytest
from app.services.quote_verifier import normalize_with_map, verify_quote


def test_quote_verifier_exact_match():
    """Verifies that an exact substring on the claimed page matches and returns verbatim text."""
    pages = {
        1: "Title: Deep Learning in Chest Radiography\nAbstract: This paper presents high diagnostic sensitivity.",
        2: "Methods: We collected 10,000 radiography images. Balanced validation cohorts were used.",
        3: "Results: The model achieved 94.2% sensitivity across external test cohorts.",
    }
    quote = "The model achieved 94.2% sensitivity across external test cohorts."
    res = verify_quote(quote, pages, claimed_page=3)

    assert res is not None
    verbatim_text, page_num = res
    assert page_num == 3
    assert verbatim_text == "The model achieved 94.2% sensitivity across external test cohorts."


def test_quote_verifier_whitespace_and_hyphenation():
    """Verifies that whitespace irregularities and line-break hyphens match verbatim text."""
    pages = {
        1: "Methods: High-resolution multi-\nsite radiography images were preprocessed with standard pipelines.",
    }
    # LLM quote has single space and no hyphen break
    quote = "High-resolution multi-site radiography images were preprocessed"
    res = verify_quote(quote, pages, claimed_page=1)

    assert res is not None
    verbatim_text, page_num = res
    assert page_num == 1
    assert "radiography images" in verbatim_text


def test_quote_verifier_curly_quotes_and_dashes():
    """Verifies that curly quotes and unicode dashes are mapped and matched."""
    pages = {
        1: 'Discussion: The “breakthrough” model—operating under low-dose conditions—showed robust metrics.',
    }
    # LLM quote uses ASCII quotes and hyphens
    quote = 'The "breakthrough" model-operating under low-dose conditions-showed robust metrics.'
    res = verify_quote(quote, pages, claimed_page=1)

    assert res is not None
    verbatim_text, page_num = res
    assert page_num == 1
    # Returns true original text with curly quotes and em-dashes
    assert "“breakthrough”" in verbatim_text


def test_quote_verifier_page_correction():
    """Verifies that when LLM claims page 1 but quote is actually on page 3, page number is corrected."""
    pages = {
        1: "Abstract: Overview of deep learning architectures.",
        2: "Methods: Hardware acceleration setup with GPU clusters.",
        3: "Results: Evaluation demonstrated a 4.8x throughput speedup without accuracy loss.",
    }
    quote = "Evaluation demonstrated a 4.8x throughput speedup without accuracy loss."
    # Claimed page 1, but actually on page 3
    res = verify_quote(quote, pages, claimed_page=1)

    assert res is not None
    verbatim_text, page_num = res
    assert page_num == 3
    assert verbatim_text == quote


def test_quote_verifier_fuzzy_repair_real_substring():
    """Verifies that slight OCR typo or missing word triggers rapidfuzz repair returning true substring."""
    pages = {
        2: "Clinical validation demonstrated receiver operating characteristic AUC of 0.941 across hospital sites.",
    }
    # LLM hallucinated 'hospitals' instead of 'hospital sites' or had minor difference
    quote = "Clinical validation demonstrated receiver operating characteristic AUC of 0.941 across hospitals."
    res = verify_quote(quote, pages, claimed_page=2, fuzzy_min=90)

    assert res is not None
    verbatim_text, page_num = res
    assert page_num == 2
    # Must be a true substring of the original page text!
    assert verbatim_text in pages[2]


def test_quote_verifier_hallucinated_quote_dropped():
    """Verifies that completely fabricated claims with no matching text return None."""
    pages = {
        1: "Introduction to renewable microgrids and battery energy storage systems.",
        2: "Methodology regarding inverter efficiency and voltage sag calculations.",
    }
    hallucinated_quote = "Quantum computers will completely replace all silicon microprocessors by 2030."
    res = verify_quote(hallucinated_quote, pages, claimed_page=1)

    assert res is None


def test_quote_verifier_disallowed_markers_rejected():
    """Verifies quotes containing internal prompt markers are immediately rejected."""
    pages = {
        1: "Title: Test Study\n[[SECTION: RESULTS]]\nResults: The accuracy was 98%.",
    }
    quote_with_marker = "[[SECTION: RESULTS]]\nResults: The accuracy was 98%."
    assert verify_quote(quote_with_marker, pages, claimed_page=1) is None

    quote_with_page_marker = "[[PAGE 1]] Results: The accuracy was 98%."
    assert verify_quote(quote_with_page_marker, pages, claimed_page=1) is None


def test_quote_verifier_length_bounds():
    """Verifies that quotes shorter than 10 chars or longer than 600 chars are rejected."""
    pages = {
        1: "Short quote. " + ("Long text describing detailed experimental setups in immense length. " * 30),
    }
    # Too short (< 10 chars)
    assert verify_quote("Short", pages, claimed_page=1) is None

    # Too long (> 600 chars)
    too_long_quote = ("Long text describing detailed experimental setups in immense length. " * 15)
    assert len(too_long_quote) > 600
    assert verify_quote(too_long_quote, pages, claimed_page=1) is None
