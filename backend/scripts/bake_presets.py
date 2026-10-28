"""
Bake the 3 real demo presets (radiology, llm_quantization, microgrids) from real CC-BY arXiv papers.
Usage:
    python -m scripts.bake_presets
"""

import asyncio
import json
import sys
import time
from pathlib import Path

from app.config import Settings
from app.schemas import AnalysisMode, AnalysisResult, FixtureProvenance
from app.services.embeddings import get_embedder
from app.services.jobs import JobStore
from app.services.llm.client import LLMClient
from app.services.pipeline import run_pipeline

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES_DIR = REPO_ROOT / "fixtures"
ENV_PATH = REPO_ROOT / "backend" / ".env"

PRESET_FILENAMES = {
    "radiology": "demo_radiology_8papers.json",
    "llm_quantization": "demo_llm_quantization_6papers.json",
    "microgrids": "demo_microgrids_6papers.json",
}


async def bake_all_presets() -> None:
    base_settings = Settings(_env_file=str(ENV_PATH)) if ENV_PATH.exists() else Settings()
    settings = Settings(
        groq_api_key=base_settings.groq_api_key,
        groq_model="qwen/qwen3.8-27b",
        hf_token=base_settings.hf_token,
        hf_model=base_settings.hf_model,
        ollama_base_url=base_settings.ollama_base_url,
        max_paper_chars=8500,
        llm_max_concurrency=1,
        llm_max_retries=10,
        job_timeout_seconds=900,
        similarity_threshold=0.70,
    )

    manifest_path = FIXTURES_DIR / "presets_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    embedder = get_embedder(settings)
    job_store = JobStore()

    for preset in manifest["presets"]:
        pid = preset["preset_id"]
        if pid not in PRESET_FILENAMES:
            continue
        out_path = FIXTURES_DIR / PRESET_FILENAMES[pid]
        arxiv_ids = [p["arxiv_id"] for p in preset["papers"]]
        print(f"\n[BAKE] Starting preset '{pid}' ({len(arxiv_ids)} arXiv papers: {arxiv_ids})...", flush=True)
        t_start = time.perf_counter()

        aid = f"demo-{pid}-v1"
        job_store.create_job(aid)
        llm_client = LLMClient(settings)

        result = await run_pipeline(
            analysis_id=aid,
            raw_files=[],
            arxiv_ids=arxiv_ids,
            job_store=job_store,
            settings=settings,
            llm_client=llm_client,
            embedder=embedder,
        )

        # Convert to DEMO mode with REAL_PIPELINE_OUTPUT provenance
        baked_dict = result.model_dump(mode="json")
        baked_dict["mode"] = AnalysisMode.DEMO.value
        baked_dict["preset_id"] = pid
        baked_dict["fixture_provenance"] = FixtureProvenance.REAL_PIPELINE_OUTPUT.value
        baked_dict["warnings"] = [
            w for w in baked_dict.get("warnings", [])
            if "SYNTHETIC_PLACEHOLDER" not in w
        ]

        validated = AnalysisResult.model_validate(baked_dict)
        out_path.write_text(
            json.dumps(validated.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        elapsed = time.perf_counter() - t_start
        print(
            f"[BAKE] Completed '{pid}' in {elapsed:.1f}s -> {out_path.name} "
            f"(papers={len(validated.papers)}, claims={len(validated.claims)}, "
            f"edges={len(validated.edges)}, gaps={len(validated.gaps)}, "
            f"reduction={validated.stats.pair_reduction_pct}%)",
            flush=True,
        )


if __name__ == "__main__":
    asyncio.run(bake_all_presets())
