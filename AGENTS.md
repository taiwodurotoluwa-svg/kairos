# AGENTS.md — Kairos (read this first, every session)

You are an autonomous coding agent working on **Kairos**, an open-source multi-paper literature synthesis and contradiction engine, for the **OPEN//BUILD 2026** hackathon (OSCA Ile-Ife). The theme is *"AI belongs to everyone. Build for a world you understand. Make it open."*

- **Submission deadline:** Thursday **29 Oct 2026, 11:59 PM WAT**. Internal target: submitted by **9:00 PM WAT**.
- **Demo Day (top 7):** Saturday 31 Oct 2026, 4:00 PM WAT (3 min slides + 5 min live demo).
- **Team (exactly two students):** DuroT (backend) and Peace (frontend).

Correctness and honesty matter more than feature count. Judges weigh understanding, effectiveness and documentation over size.

---

## 0. Mandatory start-of-session checklist

1. **Identify who you are working for** (section 1). Do not proceed until this is certain.
2. Read, in order: `README.md`, `docs/shared/01-architecture.md`, `docs/shared/02-api-contracts.md`, `docs/shared/03-open-weight-models.md`, then your developer playbook (`docs/duro/README.md` or `docs/peace/README.md`) and, for Peace, `DESIGN.md`.
3. Read `docs/requests.md` for open cross-developer requests.
4. Run `git status` and `git branch --show-current`. Work only on the milestone branch for the task you were given.
5. Do **only** the milestone you were assigned. Do not start the next one, and do not add features not listed in your playbook unless the human explicitly asks.

---

## 1. Developer identity detection

| Human | Role | GitHub | Email | Owns |
| :--- | :--- | :--- | :--- | :--- |
| **DuroT** (Durotoluwa) | Backend | `taiwodurotoluwa-svg` | `taiwodurotoluwa@gmail.com` | `/backend`, `/fixtures`, `/docs/duro` |
| **Peace** (Oluwanifemi) | Frontend | `Peaceyy28` | `oluwanifemipeace3@gmail.com` | `/frontend`, `/docs/peace` |

Procedure:

1. If the human or the launch prompt states who they are, believe it and confirm it back in your first message ("I am working for DuroT on the backend").
2. Otherwise run `git config user.name`, `git config user.email` and, if available, `gh api user --jq .login`. Match against the table.
3. If still unclear, **stop and ask**: *"Are you DuroT (backend) or Peace (frontend)?"* Never guess and never act as both.
4. Address the human by their name. Write commits as that human (their git identity is already configured on their machine; never change `git config`).

---

## 2. Workspace boundaries

| Path | Owner | Rule |
| :--- | :--- | :--- |
| `/backend/**` | DuroT | Peace's agent must not edit. |
| `/fixtures/**` | DuroT | Peace's agent reads only. Copies live in `/frontend/public/fixtures` (synced by script). |
| `/frontend/**` | Peace | DuroT's agent must not edit. |
| `/docs/duro/**`, `/docs/peace/**` | respective owner | Owner updates status checkboxes and notes only. |
| `/docs/shared/**`, `/AGENTS.md`, `/DESIGN.md`, `/README.md`, `/MASTER_PROMPTS.md`, `/LICENSE` | Both | Change only through a PR approved by **both** humans. `DESIGN.md` may be edited by Peace alone (see its override clause). |
| `/docs/reviews/**`, `/docs/AI_ASSISTANCE.md` | Both | Append-only. |

If you need something outside your workspace, **do not edit it**. Add a row to `docs/requests.md` and tell your human.

---

## 3. Hard rules (violating these can lose points or disqualify the project)

1. **Open-weight models only at runtime.** Allowed: `meta-llama/Llama-3.1-8B-Instruct`, `Qwen/Qwen2.5-7B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct` (LLM) and `BAAI/bge-small-en-v1.5` (embeddings). Forbidden in application code: OpenAI, Anthropic, Google/Gemini proprietary APIs. (Development agents and the Argon 4 review gate are tools, not runtime dependencies, and are disclosed in `docs/AI_ASSISTANCE.md`.)
2. **The models must do real work in a multi-stage pipeline** (extract, embed, referee, summarise). Do not reduce the product to a chat wrapper and do not hard-code outputs in live mode.
3. **Strict verbatim provenance.** Every claim and edge carries `{paper_id, paper_title, section, page_number, verbatim_quote}`. The backend verifies each quote against the PDF text and drops unverifiable claims. The frontend shows quote, section and page wherever a claim or edge is shown.
4. **No fabricated results.** Fixtures marked `SYNTHETIC_PLACEHOLDER` exist only to unblock development and the UI must label them. Demo presets used on Demo Day must be `REAL_PIPELINE_OUTPUT` built from real, openly licensed papers with verified quotes. Never invent benchmark numbers, paper titles, arXiv ids or citations for anything presented as real.
5. **Contract is law.** `docs/shared/02-api-contracts.md` is the single source of truth. Do not rename fields, add enum values or change shapes on one side. Contract changes go through `docs/requests.md`, need both humans' approval and bump `schema_version`.
6. **Keep secrets secret.** Never commit API keys, tokens, `.env` files or personal data. Only `.env.example` is committed. Never paste secrets into the Argon 4 review bundle. Redact them.
7. **Respect model licences.** Show the "Built with Llama" notice and the model/licence table (README and UI footer). Do not redistribute model weights. See `docs/shared/03-open-weight-models.md` §2.
8. **Understandable code.** Both humans must be able to explain every line at Demo Day. Prefer clear, boring code. Add a short comment above any non-obvious trick. Do not paste large opaque generated blocks.
9. **Tests prove it works.** Every milestone ships with passing automated verification (backend: `pytest`; frontend: browser console clean with 0 errors, visual checklist in playbook verified, responsive layout verified).
10. **No scope creep.** If you find a bug or idea outside your milestone, write it in `docs/requests.md` (cross-owner) or your playbook's "Parking lot" section.
11. **Never force-push `main`, never rewrite merged history, never commit directly to `main`.**
12. **Accessibility baseline (frontend):** colour is never the only signal; keyboard-reachable controls; visible focus ring; `prefers-reduced-motion` respected.

---

## 4. Milestones, branches and schedule

Ten milestones, ten squash-merged PRs. Branch names are fixed.

| ID | Owner | Branch | Deliverable | Depends on |
| :--- | :--- | :--- | :--- | :--- |
| **D1** | DuroT | `feat/d1-scaffold-contracts` | FastAPI scaffold, Pydantic contracts, demo endpoints, 3 placeholder fixtures (8/6/6 papers) | none |
| **D2** | DuroT | `feat/d2-ingestion` | Multi-PDF + arXiv ingestion, section-aware chunking, page tracking | D1 |
| **D3** | DuroT | `feat/d3-llm-extraction` | Unified open-weight LLM client, structured extraction, quote verifier | D1, D2 |
| **D4** | DuroT | `feat/d4-embeddings-referee` | BGE embeddings, cosine pre-filter, clustering, gaps, batched NLI referee | D3 |
| **D5** | DuroT | `feat/d5-orchestration` | `/analyze` job + SSE, consensus writer, rate limit, tests, Docker, real presets baked | D4 |
| **P1** | Peace | `feat/p1-scaffold-design` | Vanilla HTML5/CSS3/JS SPA shell, Obsidian CSS design system, mock fixture loader, preset selector | contract file (exists) |
| **P2** | Peace | `feat/p2-ingestion-hub` | 2–10 PDF dropzone, arXiv input, pipeline progress UI | P1 |
| **P3** | Peace | `feat/p3-synthesis-matrix` | Pinned-baseline synthesis matrix for 6–8+ papers | P1 (+ D1 fixtures) |
| **P4** | Peace | `feat/p4-graph-dispute` | Contradiction graph, cluster filters, dispute drawer | P3 |
| **P5** | Peace | `feat/p5-consensus-integration` | Consensus summary, gaps, exports, live integration, deploy | P4, D5 |

**Parallel mock-first rule:** Peace builds P1–P4 against `fixtures/` (`contract_sample.json` already exists; D1 adds the 8/6/6-paper placeholder fixtures within the first session). DuroT builds D1–D4 against real PDFs. P5 and D5 connect them. If D5 slips, P5 ships in **preset-only mode** and live mode becomes a bonus.

**Suggested schedule (WAT):**

| When | Plan |
| :--- | :--- |
| Mon 26 Oct (night) | Repo access, D1, P1 |
| Tue 27 Oct | D2, D3, P2, P3 |
| Wed 28 Oct | D4, P4, start D5/P5 |
| Thu 29 Oct | Finish D5/P5, bake **real** presets, README polish, record fallback demo video, **submit by 9 PM** |
| Fri 30 Oct | Rehearse the 8-minute Demo Day slot |
| Sat 31 Oct | 9 AM top-7 notice; 4 PM Demo Day |

**Cut order if behind (cut from the top, never the bottom):**
1. LaTeX export · 2. arXiv input · 3. SSE (fall back to polling `GET /analyze/{id}`) · 4. Cluster filter pills · 5. Ollama fallback.
**Never cut:** provenance, matrix, contradiction graph, three real presets, README, LICENSE, model disclosure, AI-assistance log.

---

## 5. The Argon 4 review gate (mandatory for BOTH backend and frontend milestones)

**Argon 4** is Gemini Argon 4 (Gemini 1.5 Pro) in Google AI Studio with **Thinking = High** and **Temperature = 0.2**. It serves as the independent quality referee for **BOTH DuroT (Backend D1–D5)** and **Peace (Frontend P1–P5)**.

Every single milestone—backend API or frontend UI—must pass through Argon 4 before its clean code is committed and merged.

- **Backend Milestones (`D1`–`D5`):** Argon 4 reviews FastAPI endpoints, Pydantic schema contracts, PyMuPDF extraction, open-weight LLM integration, BGE embeddings, and NLI contradiction refereeing.
- **Frontend Milestones (`P1`–`P5`):** Argon 4 reviews Vanilla HTML5 semantics, Dark Academic Observatory CSS styling, responsive mobile layouts, sticky baseline matrix UX, Cytoscape.js graph rendering, dispute drawer evidence cards, and accessibility (WCAG AA).

Per-milestone protocol:

1. **Implement** the milestone to the playbook's acceptance criteria.
2. **Verify** locally and capture the exact command and test output.
3. **Bundle into a local text file:** export the complete code of modified files, diff stats, verification logs, and adversarial critique questions to a local file: `reviews/{ID}_review.txt` (or `{ID}_review.txt`).
   > [!IMPORTANT]
   > **DO NOT commit or push review files to GitHub.** Review text bundles are local scratchpads ignored by git via `.gitignore`.
   > **Why `.txt`?** Many AI interfaces and file uploaders (including Google AI Studio) reject certain programming language file extensions (e.g., `.py`, `.ts`, `.sh`) or choke on nested code markdown blocks. A clean `.txt` file is universally accepted, easily pasted, and keeps the public GitHub repository pristine without polluting commit history with massive snapshot dumps.
4. **Hand over:** tell the human: *"Bundle ready at reviews/{ID}_review.txt. Upload or paste it into Argon 4 (Google AI Studio, High thinking, temp 0.2) using the review prompt in MASTER_PROMPTS.md §3."* Then **stop and wait**.
5. The human shares Argon 4's critique with the coding agent.
6. **Triage and fix:** every `BLOCKER` and `MAJOR` finding must be resolved in code before pushing. `MINOR` is fixed or justified. Re-run local verification to ensure everything passes.
7. **Commit & Push clean code:** once the critique is addressed and tests pass, commit the clean, production-ready code and push the branch to GitHub.
8. **Open PR & Merge** after the human confirms. One squash merge per milestone.

### Local review bundle template (`reviews/{ID}_review.txt` — NOT committed to git)

```markdown
# Argon 4 Review Bundle — {ID} ({milestone title})
- Developer: DuroT | Peace
- Coding agent / model used:
- Branch: {branch}   Commit range: {base_sha}..{head_sha}
- Date (WAT):

## 1. Acceptance criteria status
| # | Criterion (copied from playbook) | Status | Evidence |
| - | - | - | - |

## 2. `git diff --stat main...HEAD`
(paste output)

## 3. Code under review
(full text of every new or heavily changed file, each under a `### path` heading and fenced with its language; redact secrets)

## 4. Verification output (verbatim)
(pytest / lint / typecheck / build / vitest output)

## 5. Known risks and edge cases I considered (minimum 5)
-

## 6. Questions for the reviewer (minimum 3)
-

## 7. Contract and rules compliance
- Matches docs/shared/02-api-contracts.md exactly: yes/no (explain)
- Open-weight models only: yes/no
- Provenance preserved: yes/no
- Secrets in diff: none / (list)
```

### AI critique notes (local feedback workflow)

```markdown
# Argon 4 Findings — {ID}
| ID | Severity (BLOCKER/MAJOR/MINOR/NIT) | Location (file:line) | Finding | Resolution |
| - | - | - | - | - |
```

---

## 6. Git workflow

- **Base:** `main` is always deployable. Branch from the latest `main` for every milestone: `git switch main && git pull && git switch -c {branch}`.
- **Commits:** Conventional Commits, small and frequent. Format `type(scope): summary`. Types: `feat`, `fix`, `test`, `docs`, `chore`, `refactor`. Scopes: `backend`, `frontend`, `contracts`, `fixtures`, `docs`, `ci`. Examples: `feat(backend): add section-aware PDF chunker`, `test(backend): cover quote verifier fuzzy path`.
- **Never commit:** `.env`, `node_modules`, `.next`, `venv`, `__pycache__`, uploaded PDFs, model weights.
- **Push** the branch and open a PR into `main` with `gh pr create --base main --head {branch} --title "{ID}: {milestone title}" --body-file .github/pull_request_template.md` (create the template in D1 with the checklist below).
- **PR description checklist** (copy into every PR):
  ```markdown
  ## Milestone
  {ID} — {title}
  ## What changed
  -
  ## Acceptance criteria
  - [ ] all criteria in the playbook are met (link to review bundle §1)
  ## Verification
  - [ ] tests / lint / typecheck / build pass (paste summary)
  ## Argon 4 review gate
  - [ ] local `{ID}_review.txt` generated and reviewed via Argon 4
  - [ ] all BLOCKER / MAJOR feedback addressed in code
  ## Contract
  - [ ] no contract change, OR change logged in docs/requests.md and approved by both
  ## Disclosure
  - [ ] docs/AI_ASSISTANCE.md updated
  ```
- **Merge:** squash-merge your own PR after the Argon 4 gate and checks pass. **PRs that touch `docs/shared/**`, `DESIGN.md` (non-visual rules) or any contract must be approved by the other developer first.**
- After merging, delete the branch and tell the other developer in `docs/requests.md` only if it affects them.
- **Total:** exactly 10 milestone PR merges (plus small `docs`/`chore` PRs if needed).

---

## 7. Definition of Done (every milestone)

- All acceptance criteria in your playbook are met and demonstrated (test output or 1440×900 screenshot saved to `docs/peace/screens/`).
- Automated checks pass (see hard rule 9).
- Argon 4 gate completed (section 5) with no open `BLOCKER`/`MAJOR`.
- PR opened, merged and branch deleted.
- `docs/AI_ASSISTANCE.md` has a new row for this milestone.
- Playbook checkboxes updated.
- The human owner can explain what you wrote.

---

## 8. AI-assistance disclosure (OPEN//BUILD requirement)

The brief requires disclosing significant AI-assisted work and requires both humans to understand what they submit. Append one row per milestone to `docs/AI_ASSISTANCE.md`:

```markdown
| Milestone | Human | Tool / model used | What the AI did | What the human changed or verified |
| - | - | - | - | - |
| D1 | DuroT | Antigravity (Claude Sonnet 5.5) | Drafted scaffold and tests | Reviewed every file, ran tests, fixed X |
```

Rules: be specific and truthful. "AI wrote everything" is acceptable if true; vague or missing entries are not.

---

## 9. Command cheat sheet

```bash
# Backend (from /backend)
python -m venv venv && venv\Scripts\activate        # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env                               # then fill GROQ_API_KEY and/or HF_TOKEN
uvicorn app.main:app --reload --port 8000
pytest -q

# Frontend (from /frontend)
npm install
npm run sync:fixtures                                # copies ../fixtures/*.json into public/fixtures
npm run dev                                          # http://localhost:3000
npm run lint && npm run typecheck && npm run test && npm run build

# Docker (from repo root)
docker build -f backend/Dockerfile -t kairos-backend .
```

---

## 10. When you are stuck

1. Re-read the relevant shared doc and your playbook milestone.
2. Check `docs/requests.md`.
3. If a document is wrong or ambiguous, **do not improvise**: write the problem in `docs/requests.md` and tell your human.
4. If a provider or model id fails, follow `docs/shared/03-open-weight-models.md` §8 instead of switching to a closed model.
