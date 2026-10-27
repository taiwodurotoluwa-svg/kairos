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
| D3 | DuroT | | | |
| D4 | DuroT | | | |
| D5 | DuroT | | | |
| P1 | Peace | | | |
| P2 | Peace | | | |
| P3 | Peace | | | |
| P4 | Peace | | | |
| P5 | Peace | | | |
