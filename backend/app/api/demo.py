from functools import lru_cache
from pathlib import Path
from fastapi import APIRouter
from app.config import get_settings
from app.errors import KairosError
from app.schemas import AnalysisResult, DemoPresetSummary, ErrorCode

router = APIRouter(tags=["demo"])

# preset_id -> (file name, title, description, domain)
PRESETS: dict[str, tuple[str, str, str, str]] = {
    "radiology": ("demo_radiology_8papers.json", "Deep learning in chest radiography", "8 papers on lab vs real-world performance", "Medical imaging"),
    "llm_quantization": ("demo_llm_quantization_6papers.json", "LLM quantization trade-offs", "6 papers on accuracy vs efficiency", "Machine learning"),
    "microgrids": ("demo_microgrids_6papers.json", "Solar micro-grid reliability", "6 papers on storage and stability", "Energy systems"),
    "contract_sample": ("contract_sample.json", "Contract sample (3 papers)", "Synthetic payload that illustrates the API contract", "Contract"),
}


def _resolve_fixture_path(filename: str) -> Path:
    settings = get_settings()
    candidate1 = Path(settings.fixtures_dir) / filename
    if candidate1.exists():
        return candidate1
    candidate2 = Path(__file__).resolve().parent.parent.parent.parent / "fixtures" / filename
    if candidate2.exists():
        return candidate2
    return candidate1


PRESET_ALIASES: dict[str, str] = {
    "demo_radiology_8papers": "radiology",
    "demo_llm_quantization_6papers": "llm_quantization",
    "demo_microgrids_6papers": "microgrids",
}


@lru_cache(maxsize=16)
def _load(preset_id: str) -> AnalysisResult:
    preset_id = PRESET_ALIASES.get(preset_id, preset_id)
    if preset_id not in PRESETS:
        raise KairosError(ErrorCode.PRESET_NOT_FOUND, f"Unknown preset '{preset_id}'.", 404)
    path = _resolve_fixture_path(PRESETS[preset_id][0])
    if not path.exists():
        raise KairosError(ErrorCode.PRESET_NOT_FOUND, f"Preset file for '{preset_id}' is missing.", 404)
    try:
        return AnalysisResult.model_validate_json(path.read_bytes())
    except KairosError:
        raise
    except Exception as exc:
        raise KairosError(ErrorCode.INTERNAL_ERROR, f"Invalid fixture '{preset_id}': {exc}", 500) from exc


def warm_demo_cache() -> None:
    """Pre-warm cached demo presets so Demo Day playback has sub-millisecond response."""
    for pid in PRESETS:
        try:
            _load(pid)
        except Exception:
            pass


@router.get("/demo", response_model=list[DemoPresetSummary])
def list_presets() -> list[DemoPresetSummary]:
    out = []
    for pid, (_, title, desc, domain) in PRESETS.items():
        try:
            r = _load(pid)
        except Exception:
            continue
        out.append(DemoPresetSummary(preset_id=pid, title=title, description=desc, domain=domain,
                                     paper_count=len(r.papers), fixture_provenance=r.fixture_provenance))
    return out


@router.get("/demo/{preset_id}", response_model=AnalysisResult)
def get_preset(preset_id: str) -> AnalysisResult:
    return _load(preset_id)
