# AGENTS.md — ScholarMesh (Read First, Every Session)

You are an expert autonomous AI coding agent working on **ScholarMesh**, an open-source, multi-paper comparative synthesis and contradiction mapping engine for university students and researchers.

Built for the **OPEN//BUILD Hackathon 2026** (organised by OSCA Ile-Ife, GDG On Campus OAU, She Code Africa OAU, and Microsoft Student Ambassadors OAU).  
Theme: *"AI belongs to everyone. Build for a world you understand. Make it open."*  
Deadline: **Thursday, October 29, 2026, 11:59 PM WAT**.

---

## 0. Before You Write Any Code

1. **Identify which human developer you are working for:**
   * **Durotoluwa (DuroT):** GitHub: `taiwodurotoluwa-svg` | Email: `taiwodurotoluwa@gmail.com`
     * Scope: **Backend Engine, PyMuPDF Extraction, Open-Weight Model Pipeline, Embeddings & NLI Referee, FastAPI Endpoints.**
     * Your task roadmap is: [`docs/duro/README.md`](file:///docs/duro/README.md).
   * **Oluwanifemi (Peace):** GitHub: `Peaceyy28` | Email: `oluwanifemipeace3@gmail.com`
     * Scope: **Frontend UI/UX, Paper Uploader, Side-by-Side Comparison Table, Interactive Cytoscape/Force Graph, Consensus Summary View.**
     * Your task roadmap is: [`docs/peace/README.md`](file:///docs/peace/README.md).
2. **Review Shared Specifications:** Read `docs/shared/` in order (`01-architecture.md`, `02-api-contracts.md`, `03-open-weight-models.md`). The JSON schemas in `02-api-contracts.md` are the single source of truth.
3. **Check Cross-Teammate Requests:** Read `docs/requests.md` before making any schema or endpoint changes.
4. **Work Strictly on Your Assigned Task:** Do not implement features out of scope. Complete tasks sequentially (D1 → D5 or P1 → P5).

---

## 1. Product Summary (The 30-Second Pitch)

When a student or researcher reads 3 to 5 academic papers on the same topic, comparing them manually across browser tabs is tedious, overwhelming, and prone to missed contradictions. **ScholarMesh** ingests 3–5 PDF research papers simultaneously and generates:
1. **A Structured Comparison Table:** A side-by-side matrix comparing datasets, methodologies, metrics, and core conclusions.
2. **An Interactive Contradiction Graph:** A visual network where paper claim nodes are linked by **Green lines** (Agreements / Entailment) and **Red lines** (Contradictions / Conflicts), with interactive modals explaining *why* they diverge.
3. **A Consensus Executive Summary:** Synthesized overview highlighting scientific agreement vs. active controversies.

---

## 2. Hard Architectural Rules

1. **Meaningful Open-Weight AI Only:** All AI inference MUST use open-weight models (`meta-llama/Llama-3.1-8B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct`, or `Qwen2.5-7B-Instruct` for extraction & NLI; `BAAI/bge-small-en-v1.5` or `sentence-transformers` for embeddings). Closed/proprietary LLMs (OpenAI GPT-4, Anthropic Claude) are strictly forbidden in runtime code.
2. **Strict Grounding & Provenance:** Every extracted claim and contradiction MUST reference the exact paper title, section/page, and verbatim supporting quote. Hallucinations disqualify academic tools.
3. **No Mock Data in Final Backend:** Backend endpoints must perform real extraction and inference, with graceful fallbacks (Groq API -> HuggingFace Serverless -> Local Ollama).
4. **Keep Secrets Secret:** Never commit API keys (`.env` is in `.gitignore`).

---

## 3. The 5-Stage Task & Review Loop (Argon 4 Review Gate)

Work is divided into 5 clear milestones for Backend (D1–D5) and 5 for Frontend (P1–P5). For each task, the agent and developer MUST follow this exact loop:

```
[Agent Implements Task] 
        ↓
[Automated Tests / Visual Check] 
        ↓
[Agent Formats Code & Context for Argon 4 Review] 
        ↓
[Human Submits to Gemini Argon 4 (Playground - High Settings)] 
        ↓
[Agent Applies Argon 4 Suggestions & Fixes] 
        ↓
[Agent Helps Human Create & Push Feature Branch] 
        ↓
[Pull Request Created & Merged into main] (5 clean PR merges total)
```

### Git Branching & PR Convention
* Backend branches: `durot/task-d1-extraction`, `durot/task-d2-structured-extraction`, `durot/task-d3-nli-referee`, `durot/task-d4-api-endpoints`, `durot/task-d5-test-deploy`
* Frontend branches: `peace/task-p1-scaffold-dropzone`, `peace/task-p2-comparison-table`, `peace/task-p3-contradiction-graph`, `peace/task-p4-consensus-summary`, `peace/task-p5-integration-deploy`
* Commit messages follow Conventional Commits: `feat(backend): ...`, `test(api): ...`, `fix(ui): ...`.

---

## 4. Definition of Done (For Any Task)

* All acceptance criteria for the task in `docs/duro/README.md` or `docs/peace/README.md` pass.
* Unit tests pass (backend pytest or frontend build/lint).
* Argon 4 review feedback addressed.
* Feature branch pushed and PR created on GitHub.
* Code is simple, well-commented, and easily explainable by the human developer.

---

## 5. AI-Use Disclosure & Open-Source Integrity

As required by the OPEN//BUILD Challenge Brief:
* Both developers must thoroughly understand and be able to defend every line of code submitted during the Demo Day presentation.
* Disclose AI-assisted development tools in the repository `README.md`.
* No plagiarised code or fabricated benchmark metrics.

---

## 6. Development Commands

### Backend (Python 3.10+)
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
pytest tests/ -v
```

### Frontend (Next.js 14 / React)
```bash
cd frontend
npm install
npm run dev                    # Runs on http://localhost:3000
npm run build
```
