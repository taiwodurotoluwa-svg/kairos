"""
Mirror pre-baked AnalysisResult fixtures from root /fixtures/*.json into /frontend/fixtures/*.json.
Usage:
    python -m scripts.sync_fixtures
"""

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ROOT_FIXTURES = REPO_ROOT / "fixtures"
FRONTEND_FIXTURES = REPO_ROOT / "frontend" / "fixtures"

FIXTURE_FILES = [
    "contract_sample.json",
    "demo_radiology_8papers.json",
    "demo_llm_quantization_6papers.json",
    "demo_microgrids_6papers.json",
]


def sync_fixtures() -> None:
    if not FRONTEND_FIXTURES.exists():
        print(f"[SYNC] {FRONTEND_FIXTURES} does not exist yet on this branch; skipping until frontend is merged.")
        return

    copied = 0
    for fname in FIXTURE_FILES:
        src = ROOT_FIXTURES / fname
        dst = FRONTEND_FIXTURES / fname
        if src.exists():
            shutil.copyfile(src, dst)
            copied += 1
            print(f"[SYNC] Mirrored {src.name} -> frontend/fixtures/{dst.name}")
    print(f"[SYNC] Done ({copied} fixture files mirrored).")


if __name__ == "__main__":
    sync_fixtures()
