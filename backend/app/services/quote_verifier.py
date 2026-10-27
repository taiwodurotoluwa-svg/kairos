import unicodedata
from rapidfuzz import fuzz

_MAP = {ord(c): "-" for c in "\u2010\u2011\u2012\u2013\u2014\u2212"} | {
    0x2018: "'",
    0x2019: "'",
    0x201C: '"',
    0x201D: '"',
}


def normalize_with_map(text: str) -> tuple[str, list[int]]:
    """
    Normalises string into standard matching form while maintaining character index mapping:
    - NFKC normalisation.
    - Curly quotes mapped to ASCII single/double quotes.
    - Unicode dashes mapped to ASCII hyphen.
    - Collapses consecutive whitespace to a single space.
    - casefold() for case-insensitive matching.
    Returns:
        (normalised_string, list_of_original_indices)
    """
    out: list[str] = []
    idx: list[int] = []
    prev_space = True

    for i, ch in enumerate(text):
        for c in unicodedata.normalize("NFKC", ch).translate(_MAP):
            if c.isspace():
                if prev_space:
                    continue
                c, prev_space = " ", True
            else:
                prev_space = False

            for cc in c.casefold():
                out.append(cc)
                idx.append(i)

    return "".join(out), idx


def _slice(original: str, idx: list[int], start: int, end: int) -> str | None:
    """Extracts the true verbatim substring from the original text and validates length (10-600 chars)."""
    if not idx or start >= len(idx) or end <= 0 or start >= end:
        return None

    orig_start = idx[start]
    orig_end = idx[min(end - 1, len(idx) - 1)] + 1
    text = original[orig_start:orig_end].strip()

    if 10 <= len(text) <= 600:
        return text
    return None


def verify_quote(
    quote: str,
    pages: dict[int, str],
    claimed_page: int,
    fuzzy_min: int = 92
) -> tuple[str, int] | None:
    """
    Verifies that a quote is an authentic substring of the paper text.
    - Rejects quotes shorter than 10 or longer than 600 chars.
    - Rejects quotes containing model prompt markers [[PAGE or [[SECTION.
    - First attempts exact normalized match on claimed page and adjacent pages.
    - Falls back to fuzzy partial ratio alignment (rapidfuzz >= fuzzy_min, default: 92).
    - If verified, returns (verbatim_true_substring, verified_page_number).
    - If unverified (hallucination or low confidence), returns None.
    """
    if not quote or not isinstance(quote, str):
        return None

    # Anti-hallucination marker guard
    lower_q = quote.lower()
    if "[[page" in lower_q or "[[section" in lower_q:
        return None

    nq, _ = normalize_with_map(quote)
    nq = nq.strip()
    if len(nq) < 10 or len(nq) > 600:
        return None

    if not pages:
        return None

    # Search claimed page first, then adjacent pages, then outward
    order = sorted(pages.keys(), key=lambda p: (abs(p - claimed_page), p))
    cache = {p: normalize_with_map(pages[p]) for p in order}

    # 1. Exact pass
    for p in order:
        nt, im = cache[p]
        pos = nt.find(nq)
        if pos >= 0:
            sl = _slice(pages[p], im, pos, pos + len(nq))
            if sl is not None:
                return sl, p

    # 2. Fuzzy pass (aligning minor OCR typos, line break wraps, or omitted punctuation)
    best = None
    for p in order:
        nt, im = cache[p]
        if not nt:
            continue
        al = fuzz.partial_ratio_alignment(nq, nt)
        if al and al.score >= fuzzy_min and (best is None or al.score > best[0]):
            best = (al.score, p, im, al.dest_start, al.dest_end)

    if best is not None:
        sl = _slice(pages[best[1]], best[2], best[3], best[4])
        if sl is not None:
            return sl, best[1]

    return None
