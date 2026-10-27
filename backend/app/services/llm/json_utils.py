import json
import re
from typing import Any


class InvalidJSON(ValueError):
    """Raised when an LLM response cannot be parsed into a valid JSON object."""
    pass


def parse_json_object(text: str) -> dict[str, Any]:
    """
    Parses a JSON object from raw LLM output:
    1. Strips markdown code fences (```json ... ``` or ``` ... ```).
    2. Locates the outermost JSON object bounds ({ ... }).
    3. Decodes JSON using raw_decode to gracefully ignore trailing commentary or extra notes.
    4. Ensures the decoded result is a dictionary.
    5. Raises InvalidJSON with diagnostic context if invalid.
    """
    if not text or not isinstance(text, str):
        raise InvalidJSON("Response is empty or not a string.")

    cleaned = text.strip()

    # Strip markdown code fences if present at start/end
    cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\n?\s*```\s*$", "", cleaned)
    cleaned = cleaned.strip()

    # Locate outermost starting {
    start = cleaned.find("{")
    if start == -1:
        preview = cleaned[:80].replace("\n", " ")
        raise InvalidJSON(f"No JSON object delimiter found in response: '{preview}'")

    try:
        data, _ = json.JSONDecoder().raw_decode(cleaned[start:])
    except json.JSONDecodeError as exc:
        raise InvalidJSON(f"JSON decode syntax error: {exc}") from exc

    if not isinstance(data, dict):
        raise InvalidJSON(f"Expected JSON object (dict), but got {type(data).__name__}.")

    return data
