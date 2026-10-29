# Development & AI-Assistance Disclosure

Per the **OPEN//BUILD 2026** guidelines, this document outlines how our team (**Durotoluwa Taiwo** and **Oluwanifemi Ojewusi (Peace)**, Obafemi Awolowo University, Ile-Ife) designed and built **Kairos**, and where AI development tools were used during the five-day hackathon sprint.

---

## 1. Human Architecture & Engineering Ownership

All core product, architectural, and engineering decisions were made and implemented by the team:

- **Problem & Research Workflow Design (Durotoluwa & Peace):** Identified the multi-paper synthesis bottleneck faced by final-year thesis students comparing 6–10 conflicting papers, and designed the 3-view workflow (*Pinned-Baseline Synthesis Matrix*, *Contradiction Graph & Dispute Drawer*, and *Consensus & Research Gaps Report*).
- **4-Stage Open-Weight Pipeline & $O(N^2)$ Pre-Filter (Durotoluwa):** Designed the two-tier verification architecture combining local `BAAI/bge-small-en-v1.5` (384-d ONNX via FastEmbed) cosine pre-filtering with batched open-weight LLM Natural Language Inference (`Qwen3.8-27B` / `Llama-3.1-8B-Instruct` via Groq and `Llama-3.2-3B` via Ollama), reducing cross-paper referee calls by 65%–98%.
- **Zero-Hallucination Provenance Verification (Durotoluwa):** Engineered the PyMuPDF page-aware parser and deterministic quote verifier (`RapidFuzz` token-set alignment + NFKC normalization) to ensure unverified LLM claims are discarded before reaching the UI.
- **Zero-Build Vanilla SPA & Editorial Design System (Peace):** Pivoted the frontend from a heavy bundler setup to zero-build Vanilla HTML5, CSS3, and ES6 modules with Cytoscape.js, creating the *Editorial Kinetic Science* aesthetic, sticky baseline table, slide-over dispute drawer, and client-side Markdown/JSON report exporter.
- **Benchmark Curation & Production Deployment (Durotoluwa & Peace):** Curated 20 real open-access arXiv papers across Radiology, LLM Quantization, and Islanded Microgrids, baked and verified 92 verbatim scientific claims, and configured production Docker deployment on Render and Vercel.

---

## 2. How AI Development Tools Were Used

During the 5-day build window, we used AI assistants inside our IDE (**Antigravity IDE** and **Google AI Studio / Gemini**) as pair-programming and code-review aids:

| Area | How the Team Used AI Assistance | How the Team Verified & Adapted the Output |
| :--- | :--- | :--- |
| **API Schema & Boilerplate** | Assisted with drafting initial Pydantic v2 schema classes (`schemas.py`) and FastAPI route boilerplate from our API contract specification. | Manually tuned field validators, regex patterns (`paper_id`, edge ordering), and strict `extra="forbid"` rules; verified against contract tests. |
| **Regex & Text Normalization** | Assisted with drafting regular expressions for academic section header detection (`sectioner.py`) and hyphenation cleanup (`pdf_parser.py`). | Tested against real multi-column arXiv PDFs; added custom compound-word preservation (`self-`, `multi-`, `cross-`) and head/tail fallback slicing for unsectioned papers. |
| **Frontend UI & Accessibility** | Assisted with CSS layout scaffolding, SVG gauge stroke math (`consensus.js`), and WCAG ARIA keyboard navigation patterns (`drawer.js`, `matrix.js`). | Designed the multi-page layout (`#overview`, `#ingest`, `#dispute`, `#matrix`), customized typography and color tokens, and tested interactions across all 4 presets on Live Server. |
| **Static Code Review & Unit Tests** | Used Gemini in Google AI Studio to review milestone diffs for edge cases (such as rate-limit backoff, memory cleanup, and keyboard focus traps) and to help expand unit test cases. | Investigated each flagged edge case, implemented fixes (such as Groq free-tier 8k TPM retry backoff, ONNX thread bounding, and SSE reverse-proxy headers), and verified all 106 `pytest` tests pass. |

> **Note:** Distinguish development assistants from Kairos's **runtime AI pipeline**. At runtime, the Kairos application calls **100% open-weight models only** (`Qwen/Qwen3.8-27B`, `meta-llama/Llama-3.1-8B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct`, and `BAAI/bge-small-en-v1.5`) and never invokes any proprietary model API.
