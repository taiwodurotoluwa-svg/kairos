You are a Principal Software Architect, Open-Source Maintainer, and Elite Hackathon Strategist.

Generate a complete, production-grade set of 10 Markdown specification files for an open-source AI hackathon project named **"Kairos"**. 

Write every file to a **Zero-Ambiguity Agentic Engineering Standard**:
- No vague summaries, placeholders, or `// ... rest of code` truncations.
- Every data model must be fully typed in both Python (Pydantic v2) and TypeScript.
- Every system prompt, folder tree, API route, environment variable, and Git workflow rule must be explicitly written out so autonomous coding agents can execute tasks without guessing.

---

## 1. HACKATHON CONTEXT & JUDGING ALIGNMENT
- **Project Name:** Kairos
- **Event:** OPEN//BUILD 2026 (Hacktoberfest Challenge organized by Open Source Community Africa [OSCA] Ile-Ife).
- **Theme:** "AI belongs to everyone. Build for a world you understand. Make it open."
- **Timeline & Format:**
  - Challenge Window: October 25–29, 2026 (5 days).
  - Submission Deadline: Thursday, October 29, 2026 at 11:59 PM WAT.
  - Virtual Demo Day (Top 7 Teams): Saturday, October 31, 2026 at 4:00 PM WAT (3-minute slide pitch + 5-minute live prototype demo).
  - Team Size: Strictly 2 enrolled university students.
- **100-Point Judging Rubric & Target Awards (₦150,000 Pool):**
  1. **Problem Understanding & Usefulness (25 pts):** Clear user persona (university students, thesis writers, academic researchers) and high real-world utility.
  2. **Working Prototype & Technical Execution (25 pts):** Fast, crash-proof live demo handling 6–8+ research papers simultaneously.
  3. **Meaningful Use of an Open-Weight Model (20 pts):** Using open-weight Embeddings (`BAAI/bge-small-en-v1.5`) + Open-Weight Instruct LLMs (`meta-llama/Llama-3.1-8B-Instruct` / `Qwen/Qwen2.5-7B-Instruct` / `Llama-3.2-3B-Instruct`) in a multi-stage deterministic pipeline—not a generic chatbot wrapper.
  4. **Creativity & Thoughtful Design (15 pts):** Visual consensus/contradiction graph + pinned comparison matrix + research gap detection.
  5. **Open-Source Practices & Documentation (15 pts):** Clean GitHub monorepo, MIT License, model license compliance disclosures, reproducible setup, and explicit AI-assistance transparency.
  - **Target Prizes:** 1st Place (₦50,000), Best Open-Source Practice (₦15,000), Most Creative Solution (₦20,000).

---

## 2. THE PRODUCT PITCH & MULTI-PAPER SCALING ARCHITECTURE (6–8+ PAPERS)
### The Problem
When university students, final-year thesis writers, or researchers conduct a literature review across 6 to 8 academic papers on the same topic, they have to juggle dozens of PDF tabs, manually cross-check methodologies, and figure out why Paper A reports 94% accuracy while Paper D reports 61%. Existing "Chat with PDF" tools hallucinate citations, blur claims across documents, and fail completely when comparing more than 2 files.

### The Kairos Solution
Kairos is an open-source **Multi-Paper Literature Synthesis & Contradiction Engine**:
1. **Multi-Paper Ingestion (2 to 10 PDFs + ArXiv Links):** Users drag-and-drop 6–8 PDF research papers (or paste ArXiv IDs/URLs).
2. **Section-Aware Parsing (`PyMuPDF`):** Extracts text while prioritizing high-signal sections (`Abstract`, `Methodology`, `Experimental Setup`, `Results`, `Conclusion` / `Limitations`) and preserving exact page numbers.
3. **Structured Claim & Metadata Extraction (Open-Weight LLM Stage 1):** Runs concurrent async extraction (`Llama-3.1-8B-Instruct` via Groq/HuggingFace Inference API, with local `Llama-3.2-3B-Instruct` Ollama fallback) to pull structured study metadata (`Dataset`, `Sample Size`, `Methodology`, `Primary Metric`, `Core Conclusion`) and 4–6 atomic empirical claims per paper—each anchored to a verbatim quote and page number.
4. **Vector Clustering & $O(N^2)$ Pre-Filtering (`BAAI/bge-small-en-v1.5` Stage 2):**
   - Naive pairwise comparison across 8 papers (40+ claims) requires ~780 LLM calls, causing timeouts.
   - Kairos embeds all claims into 384-dimensional vectors using open-weight `BAAI/bge-small-en-v1.5`, builds a cross-paper cosine similarity matrix in <50ms, groups claims into **Semantic Topic Clusters**, and filters out unrelated pairs (cosine similarity < 0.65). This reduces LLM referee calls by ~85%.
   - Claims that have zero semantic matches in any other paper are automatically flagged as **Unverified Research Gaps**.
5. **Strict NLI Referee (Open-Weight LLM Stage 3):** Candidate cross-paper claim pairs (cosine similarity >= 0.65) are evaluated in parallel batches by the open-weight LLM acting as a Natural Language Inference (NLI) referee. It outputs:
   - `AGREE` (Entailment / Consensus)
   - `CONTRADICT` (Direct Empirical Conflict)
   - `METHODOLOGY_DELTA` (Different outcomes explained by differing datasets, hardware, or boundary conditions)
   - Plus a concise synthesis explaining *why* they differ, backed by verbatim quotes from both papers.
6. **Three High-Signal Frontend Views (Designed for 6–8+ Papers):**
   - **View 1: Pinned Synthesis Matrix Table:** A horizontally scrollable comparison table (`Dataset | Sample Size | Methodology | Key Metric | Limitations | Conclusion`) where users can **Pin 1 Paper as Baseline** on the left and compare it side-by-side against Papers 2–8, with a quick filter for *"Highlight Conflicting Methodologies"*.
   - **View 2: Filtered Interactive Contradiction Graph:** A force-directed / Cytoscape node graph where nodes are claims (color-coded or badged by Paper ID) and edges are colored **EMERALD GREEN (`AGREE`)**, **CRIMSON RED (`CONTRADICT`)**, or **AMBER (`METHODOLOGY_DELTA`)**. Includes **Topic Cluster Filter Pills** and an **"Isolate Contradictions"** toggle so 8 papers never look cluttered. Clicking any edge opens the **Dispute Inspection Drawer** showing side-by-side verbatim PDF quotes, page numbers, and the NLI explanation.
   - **View 3: Consensus Executive Summary & One-Click Export:** Displays overall Consensus Score, Top Contradictions, Identified Research Gaps, and a 1-click **Export to Markdown / LaTeX Literature Review** button.

---

## 3. TEAM ROLES & MONOREPO DELEGATION
- **Repository Structure:** Single Monorepo (`/backend`, `/frontend`, `/docs`, `/fixtures`) to prevent cross-developer merge conflicts and satisfy the single-repository submission requirement.
- **Backend Engineer:** Durotoluwa (DuroT)
  - GitHub: `taiwodurotoluwa-svg` | Email: `taiwodurotoluwa@gmail.com`
  - Workspace: `/backend` and `/fixtures`
  - Stack & Scope: Python 3.11+, FastAPI, `PyMuPDF` (`fitz`), `arxiv` / `httpx` fetcher, `sentence-transformers` / FastEmbed or HF API (`BAAI/bge-small-en-v1.5`), Open-Weight LLM Client (Groq / HuggingFace / Ollama unified adapter), NumPy cosine similarity clustering & pre-filter, async NLI referee pipeline, Pydantic v2 schemas, Pytest suite.
- **Frontend Engineer:** Oluwanifemi Peace (Peace)
  - GitHub: `Peaceyy28` | Email: `oluwanifemipeace3@gmail.com`
  - Workspace: `/frontend`
  - Stack & Scope: Next.js 14 (App Router), TypeScript, Tailwind CSS, Lucide Icons, Multi-PDF (6–8+) Drag-and-Drop + ArXiv URL Input, Pinned Comparison Matrix Table, Interactive Graph (`react-force-graph-2d` or `cytoscape`), Topic Cluster Filter Bar, Dispute Inspection Slide-Over Modal, Instant Demo Dataset Switcher, Markdown/LaTeX Export.

---

## 4. AGENT WORKFLOW, MILESTONES & "ARGON 4" QUALITY GATE
1. **Identity & Scope Lock:** Every coding agent must read `AGENTS.md` first, confirm whether its human operator is **DuroT (Backend)** or **Peace (Frontend)**, and never modify files outside its assigned workspace without logging an async request in `docs/requests.md`.
2. **Parallel Mock-First Execution:** Milestone 1 creates a deterministic static fixture (`fixtures/demo_radiology_8papers.json`, `fixtures/demo_llm_quantization_6papers.json`, `fixtures/demo_microgrids_6papers.json`) matching `docs/shared/02-api-contracts.md`. Peace's frontend builds against these fixtures immediately in P1–P4 while Duro's backend builds the live pipeline in D1–D4. P5 and D5 connect live APIs with automatic fallback to pre-baked demo fixtures.
3. **10 Sequential Milestones (5 Backend + 5 Frontend):**
   - **Backend (DuroT):**
     - `D1`: FastAPI scaffold, CORS, Pydantic v2 contract models, and `/api/v1/demo/{preset_id}` serving the 3 pre-baked 6–8 paper datasets.
     - `D2`: Multi-PDF (`PyMuPDF`) & ArXiv link ingestion service with section-aware chunking, page-number tracking, and `asyncio` concurrency for 6–8+ files.
     - `D3`: Unified Open-Weight LLM Client (Groq `llama-3.1-8b-instant` / HF Inference / Local Ollama `llama3.2:3b`) + Structured Claim & Metadata Extractor with strict JSON validation and retry logic.
     - `D4`: `BAAI/bge-small-en-v1.5` Embedding Service + NumPy Cosine Similarity Pre-Filter ($\ge 0.65$), K-Means/Agglomerative Topic Clustering, Research Gap detector, and Batched Async NLI Referee (`AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA`).
     - `D5`: End-to-end `/api/v1/analyze` orchestration endpoint, SSE/progress status reporting, rate-limit protection, Pytest suite, and Dockerfile / `requirements.txt` verification.
   - **Frontend (Peace):**
     - `P1`: Next.js 14 App Router scaffold, Academic Dark-Mode Design System (`DESIGN.md`), Mock/Live API Client switcher, and Instant Demo Preset Selector bar.
     - `P2`: Multi-Paper Ingestion Hub supporting 2–10 PDF drag-and-drop cards + ArXiv ID input, file validation, and step-by-step pipeline progress indicator.
     - `P3`: Pinned Side-by-Side Synthesis Matrix Table for 6–8+ papers (sticky baseline paper column, horizontal scroll, conflict row highlighting, search/filter).
     - `P4`: Interactive Consensus & Contradiction Graph (`AGREE` green, `CONTRADICT` crimson, `METHODOLOGY_DELTA` amber) + Topic Cluster Filter Pills + Slide-Over Dispute Inspection Modal with verbatim quotes and page badges.
     - `P5`: Executive Consensus Summary Card, Research Gaps panel, 1-click Markdown/LaTeX export, responsive polish, and end-to-end integration with Duro's live FastAPI backend.
4. **The "Argon 4" Review Gate (Google AI Studio — High Reasoning Effort, Temp 0.2):**
   - At the end of each milestone (`D1`–`D5` and `P1`–`P5`), the coding agent MUST generate an **Argon 4 Review Bundle** containing: (a) Milestone ID, (b) `git diff --stat` and modified code, (c) Verification test output, and (d) Edge-case questions.
   - The human developer pastes this bundle into the Argon 4 Review Agent (Google AI Studio, High Thinking mode, Temperature 0.2).
   - Only after addressing Argon 4's audit findings may the developer open a Pull Request (`feat/d1-scaffold`, etc.) and merge to `main`, creating 10 clean, verifiable PR merges across the project.
5. **Non-Negotiable Hard Rules:**
   - **100% Open-Weight Models Only:** Never call closed proprietary models (no `gpt-4o`, `claude-3.5`, or `gemini` inside runtime application code). Document every model ID, parameter count, and license (Llama 3.1 Community License, Apache-2.0, MIT) in the UI and README.
   - **Strict Verbatim Provenance:** Every claim and contradiction edge MUST carry `{ paper_id, paper_title, section, page_number, verbatim_quote }`.
   - **5-Second Live Demo Safety:** Judges only give 5 minutes for the live demo. The app must include 3 one-click pre-analyzed 6–8 paper datasets so the team can demonstrate both instant multi-paper graph exploration (0 latency) AND a live upload during the presentation.

---

## 5. REQUIRED OUTPUT: 10 COMPLETE MARKDOWN FILES
Generate the complete, unabridged Markdown content for all 10 files below. Do not skip sections or use placeholders:

1. `AGENTS.md` — Master instruction manual read first by every coding agent: Developer Identity Detection (`DuroT` vs `Peace`), workspace boundaries, Hard Rules, Argon 4 Review Gate protocol, Git branch/commit/PR naming conventions, Definition of Done, and OPEN//BUILD AI-Assistance Disclosure log template.
2. `DESIGN.md` — "Dark Academic Observatory" UI/UX specification: color tokens (Obsidian slate backgrounds, Emerald `#10B981` Consensus, Crimson `#EF4444` Contradiction, Amber `#F59E0B` Methodology Delta), typography (`Inter`, `Newsreader`/`Instrument Serif`, `JetBrains Mono`), 6–8+ paper sticky matrix table layout specs, node graph visual hierarchy, and dispute drawer micro-interactions.
3. `README.md` — Public Hackathon Repository Landing Page engineered for full marks on the 15-point Open-Source Rubric: Badges, Problem & User Persona, How Kairos Scales to 6–8+ Papers ($O(N^2)$ Embedding Pre-Filter diagram), Open-Weight Model & License Compliance Table, Monorepo Architecture, Reproducible 5-Minute Local Setup, Demo Day Guide, Team Credits, and AI-Assisted Contributions Acknowledgement.
4. `docs/shared/01-architecture.md` — End-to-end system architecture: ASCII/Mermaid dataflow diagram, PDF + ArXiv ingestion pipeline, BGE embedding similarity matrix math, async NLI batching strategy for 8 papers, and latency budget (<15s live, <100ms cached/preset).
5. `docs/shared/02-api-contracts.md` — Single Source of Truth API specification: Exact Pydantic v2 models and matching TypeScript interfaces for `PaperMetadata`, `ExtractedClaim`, `TopicCluster`, `ClaimComparisonEdge`, `ResearchGap`, `ConsensusReport`, REST endpoints (`POST /api/v1/analyze`, `GET /api/v1/demo/{preset_id}`, `GET /api/v1/health`), error codes, and a complete sample JSON payload.
6. `docs/shared/03-open-weight-models.md` — Open-Weight Model Strategy: Provider fallback chain (Groq -> HuggingFace -> Local Ollama), exact model IDs and licenses, exact System & User Prompts for Stage 1 (Structured JSON Claim Extraction) and Stage 3 (Strict NLI Referee), plus Stage 2 (`BAAI/bge-small-en-v1.5`) cosine similarity threshold tuning and known model limitations.
7. `docs/duro/README.md` — Backend Execution Playbook for DuroT: Exact `/backend` directory tree, step-by-step instructions, code skeletons, and acceptance criteria for Milestones `D1` through `D5`, plus the Argon 4 verification checklist for each milestone.
8. `docs/peace/README.md` — Frontend Execution Playbook for Peace: Exact `/frontend` directory tree, step-by-step instructions, component hierarchies, and acceptance criteria for Milestones `P1` through `P5` (specifically detailing how to render 6–8+ papers cleanly in the table and graph), plus the Argon 4 verification checklist for each milestone.
9. `docs/requests.md` — Cross-Developer Async Contract Change Log template with initial seed entries between DuroT and Peace.
10. `MASTER_PROMPTS.md` — Copy-pasteable bootstrapping prompts for: (1) DuroT's Coding Agent, (2) Peace's Coding Agent, and (3) The Argon 4 High-Reasoning Code Review Gate in Google AI Studio.

### OUTPUT DELIVERY INSTRUCTION
To prevent output token truncation across these 10 comprehensive files:
- Deliver **Batch 1 (Files 1 to 5)** in full detail first, then immediately deliver **Batch 2 (Files 6 to 10)** in full detail (or generate all 10 files inside a downloadable `.zip` archive if code execution is available). Never abbreviate schemas or prompts.