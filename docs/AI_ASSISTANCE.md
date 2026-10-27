# AI-Assistance Disclosure Log

OPEN//BUILD 2026 requires teams to disclose significant AI-assisted work and to understand everything they submit. One row per milestone (append only). Be specific and truthful. See `AGENTS.md` §8.

## Tools used on this project

| Tool | Purpose |
| :--- | :--- |
| Antigravity IDE with Claude / Gemini coding agents | Drafting code, tests and documentation under human direction |
| Gemini Argon 4 (Google AI Studio, Thinking = High, Temperature 0.2) | Independent code-review gate before every merge |
| Runtime models (not development tools) | `meta-llama/Llama-3.1-8B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct`, `BAAI/bge-small-en-v1.5` |

## Milestone log

| Milestone | Human | Tool / model used | What the AI did | What the human changed or verified |
| :--- | :--- | :--- | :--- | :--- |
| Docs | DuroT | Antigravity (Claude Sonnet 5.5) | Drafted AGENTS.md, DESIGN.md, README.md, shared docs, playbooks, prompts, contract sample | Chose scope, team split, name "Kairos", reviewed content |
| D1 | DuroT | Antigravity + Gemini Argon 4 (AI Studio) | Scaffolded FastAPI backend, Pydantic v2 schemas, demo endpoints, fixture generator. Argon 4 reviewed D1 (APPROVE_WITH_CHANGES); resolved F-01..F-06, expanded test suite to 21 passing tests. | Reviewed findings, directed fix of error wrappers, CWD resolution, and cache warming. 21/21 tests verified passing. |
| D2 | DuroT | Antigravity + Gemini Argon 4 (AI Studio) | Implemented PyMuPDF parser, sectioner, arXiv fetcher, and concurrent coordinator. Argon 4 reviewed D2 (APPROVE_WITH_CHANGES); resolved F-01..F-07 (FILE_TOO_LARGE error codes, canonical arXiv deduplication, unsectioned head/tail fallback, sort=False reading order, threading.Lock, marker headroom, cross-source SHA-256 deduplication), expanded test suite to 39 passing tests. | Reviewed findings, directed fix of error codes, fallback tail, and thread safety. 39/39 tests verified passing. |
| D3 | DuroT | Antigravity + Gemini Argon 4 (AI Studio) | Implemented open-weight LLM client with failover chain (Groq -> HF -> Ollama), verbatim prompts, quote verifier with NFKC and RapidFuzz partial ratio alignment, structured claim extraction. Argon 4 reviewed D3 (APPROVE_WITH_CHANGES); resolved F-01..F-06 (claim_id hyphen parity p1-c1, palette_index modulo 10, RawExtraction/RawClaim Pydantic validators, AsyncOpenAI client context manager, retry jitter, secret scrubbing, short-page quote false-positive guard, json.raw_decode for trailing braces, prompt escaping), expanded test suite to 62 passing tests. | Reviewed findings, directed fix of claim_id contract parity, socket leaks, and quote verifier guard. 62/62 tests verified passing. |
| D4 | DuroT | Antigravity + Gemini Argon 4 (AI Studio) | Implemented Embedder protocol (FastEmbed BAAI/bge-small-en-v1.5 and HF fallback), cosine matrix with same-paper masking, pre-cap gap detection, candidate pair pre-filtering with top-k, agglomerative clustering with contract discard rules, and batched NLI referee. Tuned threshold to 0.70 on 36 labelled pairs (F1=0.974). Measured pair reduction: 67.9% (radiology 8-paper) and 52.0% (LLM 6-paper). Argon 4 reviewed D4 (APPROVE_WITH_CHANGES); resolved F-01..F-05 (LLMClient complete_json signature parity, in-place claim mutation for is_research_gap and cluster_id, retry storm guard on provider failure, LLMClient call tracking, numeric paper sorting in clusters), expanded test suite to 81 passing tests. | Reviewed findings, verified real LLMClient integration, in-place mutation invariants, and threshold tuning results. 81/81 tests verified passing. |
| D5 | DuroT | Antigravity + Gemini Argon 4 (AI Studio) | Implemented 5-stage pipeline orchestrator (pipeline.py), deterministic consensus score calculation and Stage 4 consensus writer with edge ID validation (consensus.py), graph assembler with model disclosures (graph_builder.py), JobStore with SSE fanout and replay (jobs.py), sliding-window rate limiter (rate_limit.py), /analyze endpoints with SSE streaming and 15s keep-alive (analyze.py), presets manifest with real CC-BY arXiv IDs, Dockerfile pre-baking BAAI/bge-small-en-v1.5, and backend/README.md. Expanded test suite to 97 passing tests. | Reviewed architecture, validated SSE keep-alive behavior, verified contract ErrorCode alignment, and confirmed all 97 unit and integration tests passing. |
| P1 | Peace | | | |
| P2 | Peace | | | |
| P3 | Peace | | | |
| P4 | Peace | | | |
| P5 | Peace | | | |
