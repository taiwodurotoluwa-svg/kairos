# Backend Engineering Roadmap (Durotoluwa / DuroT)

* **Developer:** Durotoluwa Taiwo (`taiwodurotoluwa-svg`)
* **Role:** Backend Engine, PyMuPDF, Open-Weight Model Orchestration, NLI Pipeline, FastAPI.
* **Goal:** Deliver a rock-solid, fully-tested, reproducible Python backend for Kairos.

---

## The 5 Phased Tasks & PR Flow

### Task D1: PyMuPDF Multi-Section Extractor & Chunking Engine
* **Branch:** `durot/task-d1-pdf-extraction`
* **Files to create/modify:** `backend/app/services/extractor.py`, `backend/tests/test_extractor.py`
* **Scope:**
  * Ingest PDF bytes using `pymupdf` (PyMuPDF).
  * Parse page-by-page text with page index tracking.
  * Extract prioritized sections: `Abstract`, `Methodology`, `Results`, `Conclusion`.
  * Unit test on a real sample PDF verifying clean text extraction and page retention.
* **Argon 4 Review Gate:** Review `extractor.py` for section regex robustness and memory efficiency.
* **PR:** Merge `durot/task-d1-pdf-extraction` into `main`.

---

### Task D2: Open-Weight Model Structured Extraction Engine
* **Branch:** `durot/task-d2-structured-extraction`
* **Files to create/modify:** `backend/app/services/llm_client.py`, `backend/app/models/schemas.py`, `backend/tests/test_llm.py`
* **Scope:**
  * Implement unified Open-Weight inference client (Groq / HuggingFace serverless with local Ollama fallback).
  * Format prompt with schema from `docs/shared/03-open-weight-models.md`.
  * Parse model output into Pydantic `PaperExtraction` model with automatic JSON sanitization.
  * Unit tests mocking and verifying real schema validation.
* **Argon 4 Review Gate:** Review JSON schema validation and retry logic on truncated model outputs.
* **PR:** Merge `durot/task-d2-structured-extraction` into `main`.

---

### Task D3: Semantic Topic Matcher & Strict NLI Referee
* **Branch:** `durot/task-d3-nli-referee`
* **Files to create/modify:** `backend/app/services/embeddings.py`, `backend/app/services/referee.py`, `backend/tests/test_referee.py`
* **Scope:**
  * Implement lightweight embedding generation with `fastembed` or `sentence-transformers` (`BAAI/bge-small-en-v1.5`).
  * Cosine similarity matcher to identify cross-paper claim candidate pairs (threshold $\ge 0.65$).
  * Implement NLI referee prompt returning `AGREE` / `CONTRADICT` / `UNRELATED` + `reason_for_difference`.
  * Generate `ConsensusReport` summarizing overall scientific convergence.
* **Argon 4 Review Gate:** Review embedding threshold logic and contradiction accuracy.
* **PR:** Merge `durot/task-d3-nli-referee` into `main`.

---

### Task D4: FastAPI Application Endpoints & Pre-Loaded Demo Trios
* **Branch:** `durot/task-d4-api-endpoints`
* **Files to create/modify:** `backend/app/main.py`, `backend/app/api/routes.py`, `backend/data/sample_trios/`
* **Scope:**
  * `POST /api/synthesize`: Accepts 3–5 uploaded files, coordinates extractor $
ightarrow$ LLM $
ightarrow$ referee $
ightarrow$ response.
  * `GET /api/sample/{dataset_id}`: Serves instant pre-baked high-fidelity responses for Demo Day (Radiology, LLMs, Microgrids).
  * `GET /api/health`: Health status.
  * Add CORS middleware for Next.js frontend (`http://localhost:3000`).
* **Argon 4 Review Gate:** Review error handling, HTTP status codes, and multi-file streaming.
* **PR:** Merge `durot/task-d4-api-endpoints` into `main`.

---

### Task D5: Comprehensive Test Suite, Docker, & Deployment Blueprint
* **Branch:** `durot/task-d5-test-deploy`
* **Files to create/modify:** `backend/tests/`, `backend/Dockerfile`, `render.yaml`, `backend/README.md`
* **Scope:**
  * Full pytest suite covering extraction, schema validation, and API routing.
  * Dockerfile with multi-stage build.
  * Write clear deployment instructions for Render / Railway.
* **Argon 4 Review Gate:** Final security audit (no exposed secrets, clean dependency tree).
* **PR:** Merge `durot/task-d5-test-deploy` into `main`.
