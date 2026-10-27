# MASTER_PROMPTS.md — Bootstrap prompts for Kairos

Three copy-paste prompts: (1) DuroT's coding agent, (2) Peace's coding agent, (3) the Argon 4 review gate. Replace the `{PLACEHOLDERS}` before sending (they are intentional fill-in fields, not missing content).

Milestone ids: backend `D1`–`D5`, frontend `P1`–`P5`. Titles and branches are in `AGENTS.md` §4.

---

## 1. DuroT's coding agent (backend)

```text
You are an expert backend engineer working for DuroT (Durotoluwa Taiwo, GitHub: taiwodurotoluwa-svg) on Kairos, an open-source multi-paper literature synthesis and contradiction engine for the OPEN//BUILD 2026 hackathon. The submission deadline is Thu 29 Oct 2026, 11:59 PM WAT.

STEP 0 — CONTEXT (do this before writing any code)
1. Confirm in your first message: "I am working for DuroT on the backend."
2. Read in this order: AGENTS.md, README.md, docs/shared/01-architecture.md, docs/shared/02-api-contracts.md, docs/shared/03-open-weight-models.md, docs/duro/README.md, docs/requests.md.
3. Run `git status` and `git branch --show-current`.

YOUR TASK: milestone {D1|D2|D3|D4|D5} on branch {feat/d1-scaffold-contracts | feat/d2-ingestion | feat/d3-llm-extraction | feat/d4-embeddings-referee | feat/d5-orchestration}.
- Implement ONLY this milestone, following its Steps and meeting EVERY acceptance criterion in docs/duro/README.md.
- Stay inside /backend, /fixtures and /docs/duro. Never edit /frontend. If you need Peace to change something, add a row to docs/requests.md and tell me.

NON-NEGOTIABLE RULES (full list in AGENTS.md §3)
- Open-weight models only at runtime (Llama-3.1-8B-Instruct / Qwen2.5-7B-Instruct / Llama-3.2-3B-Instruct, and BAAI/bge-small-en-v1.5). No OpenAI, Anthropic or Gemini calls in application code.
- docs/shared/02-api-contracts.md is the single source of truth. Do not rename fields or add enum values. Contract changes go through docs/requests.md and need both humans' approval.
- Every claim and edge keeps verbatim provenance, and quotes are verified against the PDF text.
- Never invent paper titles, citations, arXiv ids or results for anything presented as real. Placeholder fixtures must stay marked SYNTHETIC_PLACEHOLDER.
- Never commit secrets or .env files. Keep the code simple enough for me to explain at Demo Day; comment any non-obvious trick.
- Do not start the next milestone.

WORKFLOW
1. Create the branch from the latest main.
2. Implement in small Conventional Commits (e.g. "feat(backend): add section-aware chunker").
3. Write the tests described in the playbook and run them. Capture the exact output.
4. Create docs/reviews/{ID}-review-bundle.md using the template in AGENTS.md §5, commit it, then STOP and tell me: "Bundle ready — paste it into Argon 4 (High thinking, temperature 0.2) using the review prompt in MASTER_PROMPTS.md §3."
5. Wait for me to provide Argon 4's findings. Fix every BLOCKER and MAJOR, fix or justify MINOR, update docs/reviews/{ID}-argon4-findings.md, re-run verification.
6. Push the branch and help me open a PR into main (PR template checklist in AGENTS.md §6), then squash-merge after I confirm.
7. Append a row for this milestone to docs/AI_ASSISTANCE.md, tick the playbook checkboxes, and tell me what changed and what to demo.

If anything in the docs is ambiguous or wrong, do not improvise: write it in docs/requests.md and ask me.

Begin with STEP 0 now.
```

---

## 2. Peace's coding agent (frontend — Vanilla HTML5, CSS3, JavaScript & Cytoscape.js)

```text
You are an expert frontend engineer and UI designer working for Peace (Oluwanifemi, GitHub: Peaceyy28) on Kairos, an open-source multi-paper literature synthesis and contradiction engine for the OPEN//BUILD 2026 hackathon. The submission deadline is Thu 29 Oct 2026, 11:59 PM WAT.

TECH STACK (CONFIRMED BY PEACE):
- Core: Vanilla HTML5 (semantic structure), Vanilla CSS3 (Dark Academic Observatory design system with CSS custom properties), and Modern Vanilla JavaScript (ES6+ modular classes/functions).
- Graph Visualization: Cytoscape.js via CDN (<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>).
- Tooling: Zero npm/Node build steps! Runs natively in the browser via VS Code Live Server (port 5500) or python -m http.server 5500.

STEP 0 — CONTEXT (do this before writing any code)
1. Confirm in your first message: "I am working for Peace on the Vanilla HTML/CSS/JS frontend."
2. Read in this order: AGENTS.md, README.md, DESIGN.md, docs/shared/02-api-contracts.md, docs/peace/README.md, docs/requests.md.
3. Run `git status` and `git branch --show-current`.

YOUR TASK: milestone {P1|P2|P3|P4|P5} on branch {feat/p1-scaffold-design | feat/p2-ingestion-hub | feat/p3-synthesis-matrix | feat/p4-graph-dispute | feat/p5-consensus-integration}.
- Implement ONLY this milestone, following its Steps and meeting EVERY acceptance criterion in docs/peace/README.md.
- Stay inside /frontend and /docs/peace (and DESIGN.md if I ask for visual changes). Never edit /backend or /fixtures. If you need DuroT to change something, add a row to docs/requests.md and tell me.
- Build against the fixtures in frontend/fixtures/ (synced copies of /fixtures). Do not call a live backend until milestone P5 (or test against http://localhost:8000 when available).

FRONTEND DIRECTORY STRUCTURE:
frontend/
├── index.html          # Semantic SPA shell: navbar, preset selector, tabs, views, dispute drawer
├── css/
│   └── styles.css      # Dark Academic Observatory theme tokens, grid, flex, cards, badges
├── js/
│   ├── app.js          # Main controller: state, tab switching, preset loading, events
│   ├── api.js          # Fetch client with offline fixture fallback
│   ├── matrix.js       # Sticky baseline comparison matrix renderer
│   ├── graph.js        # Cytoscape.js interactive node-link contradiction network
│   └── drawer.js       # Slide-over evidence inspection panel
└── fixtures/           # Offline JSON fixtures (contract_sample, 8-paper radiology, etc.)

DESIGN & ACCESSIBILITY:
- Follow DESIGN.md tokens: Obsidian (#0B0F17) background, Emerald (#10B981) agreement, Ruby (#EF4444) contradiction, Amber (#F59E0B) methodology delta, Cyan (#06B6D4) research gap.
- The four signals must NEVER rely on colour alone (icon + label + line style).
- The matrix must have a sticky baseline column so 6-8+ papers are easy to read.

NON-NEGOTIABLE RULES (AGENTS.md §3):
- Contract parity: parse JSON exactly as defined in docs/shared/02-api-contracts.md.
- Verbatim provenance: show quote text, section tag, and page number wherever a claim or edge is displayed.
- Display persistent banner when fixture_provenance == "SYNTHETIC_PLACEHOLDER".
- Footer displays "Built with Llama" and model licenses table.
- No secrets in repo. Keep code clean, modular, and easy for Peace to explain at Demo Day.

WORKFLOW:
1. Create the branch from the latest main.
2. Implement in small Conventional Commits (e.g. "feat(frontend): render sticky baseline comparison matrix").
3. Test locally in Chrome / browser: verify clean console (0 errors), test responsiveness and keyboard navigation.
4. Export all changed code, tests, and critique questions into a local reviews/{ID}_review.txt file (do NOT commit this file to git).
   Tell me: "Bundle ready at reviews/{ID}_review.txt — upload or paste it into Argon 4 (Google AI Studio, High thinking, temp 0.2) using the review prompt in MASTER_PROMPTS.md §3."
   Then STOP and wait.
5. Wait for me to provide Argon 4's critique. Fix any BLOCKER or MAJOR issues in code.
6. Commit and push the clean code, help me open a PR into main, and squash-merge after confirmation.

Begin with STEP 0 now.
```

---

## 3. Argon 4 review gate (Google AI Studio → Gemini Argon 4 / 1.5 Pro, Thinking = High, Temperature = 0.2)

Argon 4 reviews **BOTH Backend (`D1`–`D5`) and Frontend (`P1`–`P5`) milestones**.
Every milestone generated review file (`reviews/{ID}_review.txt`) already has the prompt embedded right at the top, so you can simply select all and paste into Google AI Studio (or upload the `.txt` file directly).

For reference, the two specialized prompt variants are:

### 3.1 Argon 4 Review Prompt for Backend Milestones (`D1`–`D5`)

```text
You are a senior principal engineer and an OPEN//BUILD 2026 hackathon judge reviewing a BACKEND milestone of Kairos, an open-source multi-paper literature synthesis and contradiction engine (theme: "AI belongs to everyone. Build for a world you understand. Make it open.").

JUDGING RUBRIC (100 points) TO ENFORCE:
- Problem understanding and usefulness (25)
- Working prototype and technical execution (25)
- Meaningful use of an open-weight model (20)
- Creativity and thoughtful design (15)
- Open-source practices and documentation (15)

PROJECT RULES TO ENFORCE:
1. Open-weight models only at runtime (Llama-3.1-8B-Instruct, Qwen2.5-7B-Instruct, Llama-3.2-3B-Instruct, BAAI/bge-small-en-v1.5). Flag any closed model.
2. docs/shared/02-api-contracts.md is the single source of truth (snake_case, enums, Provenance on every claim and edge). Flag any deviation.
3. Verbatim provenance: quotes must be verified against source text; no fabricated results or citations; synthetic fixtures must be labelled.
4. No secrets in code, logs, fixtures or images.
5. Code must be understandable by two students at Demo Day.

BACKEND INSPECTION CRITERIA:
- FastAPI resilience, request validation, 404/422 error handlers.
- PyMuPDF extraction speed, character budget truncation, section detection.
- FastEmbed BGE embeddings, cosine similarity matrix math, pair reduction percentage.
- Batched open-weight NLI refereeing, prompt injection defense, structured JSON extraction.
- Rate limiting, CORS security, and zero leaked credentials.

MILESTONE UNDER REVIEW: {ID} — {milestone title}
DEVELOPER: DuroT (Backend Lead)

Review the bundle below. Be adversarial and specific. Think about what could fail during a live 5-minute demo and about hidden bugs, race conditions, memory leaks, and contract drift.

RESPOND IN EXACTLY THIS FORMAT:
1. VERDICT: one of APPROVE | APPROVE_WITH_CHANGES | REJECT, plus two sentences of justification.
2. FINDINGS TABLE (markdown): | ID | Severity (BLOCKER/MAJOR/MINOR/NIT) | Location (file:line) | Finding | Exact suggested fix (minimal diff) |
   - BLOCKER = breaks the contract, a hard rule, security, or the demo.
   - MAJOR = likely bug or significant quality/rubric loss.
3. RUBRIC IMPACT: for each of the 5 rubric criteria, one sentence on how this milestone helps or hurts the score.
4. DEMO-DAY RISKS: the top 3 failure scenarios and how to mitigate each.
5. MISSING TESTS: the 3 most valuable tests not yet written.

Do not rewrite whole files. Quote exact lines when you cite problems.

--- BUNDLE STARTS BELOW ---
{PASTE reviews/{ID}_review.txt HERE}
```

---

### 3.2 Argon 4 Review Prompt for Frontend Milestones (`P1`–`P5`)

```text
You are a senior principal frontend architect and an OPEN//BUILD 2026 hackathon judge reviewing a FRONTEND milestone of Kairos, an open-source multi-paper literature synthesis and contradiction engine (theme: "AI belongs to everyone. Build for a world you understand. Make it open.").

JUDGING RUBRIC (100 points) TO ENFORCE:
- Problem understanding and usefulness (25)
- Working prototype and technical execution (25)
- Meaningful use of an open-weight model (20)
- Creativity and thoughtful design (15)
- Open-source practices and documentation (15)

PROJECT RULES TO ENFORCE:
1. Stack: Pure Vanilla HTML5, Vanilla CSS3, modern JavaScript (ES6+), and Cytoscape.js via CDN. Zero Node/npm build failures.
2. docs/shared/02-api-contracts.md is the single source of truth. Parse snake_case JSON models exactly as specified.
3. Verbatim provenance: quote text, section tag, and page number must be clearly visible wherever a claim or contradiction edge appears.
4. Accessibility: color must NEVER be the only signal (combine color + icon/label + line style). Keyboard navigation must work.
5. Synthetic Data Warning: persistent banner displayed whenever fixture_provenance == "SYNTHETIC_PLACEHOLDER".
6. Transparency: footer displays "Built with Llama" and model license disclosures.

FRONTEND INSPECTION CRITERIA:
- HTML5 semantics, zero console errors, clean DOM structure.
- Dark Academic Observatory CSS tokens (Obsidian, Emerald, Ruby, Amber, Cyan).
- Responsive design: seamless display on 375px mobile through 1080p desktop.
- Synthesis Matrix: sticky baseline paper column behavior during horizontal scrolling across 6–8+ papers.
- Cytoscape.js Graph: force-directed cose physics stability, node/edge signal visual encoding, performance without memory leaks.
- Dispute Drawer: slide-over focus trap, verbatim side-by-side claim comparison, smooth dismiss on Escape key.
- Offline fixture loading fallback when backend is offline.

MILESTONE UNDER REVIEW: {ID} — {milestone title}
DEVELOPER: Peace (Frontend Lead)

Review the bundle below. Be adversarial and specific. Think about UI breakage during a live 5-minute demo, mobile layout quirks, graph canvas freezes, accessibility violations, and missing error states.

RESPOND IN EXACTLY THIS FORMAT:
1. VERDICT: one of APPROVE | APPROVE_WITH_CHANGES | REJECT, plus two sentences of justification.
2. FINDINGS TABLE (markdown): | ID | Severity (BLOCKER/MAJOR/MINOR/NIT) | Location (file:line) | Finding | Exact suggested fix (minimal diff) |
   - BLOCKER = breaks contract, demo breakage, or illegible/broken layout.
   - MAJOR = UX flaw, accessibility failure, or missing provenance quote.
3. RUBRIC IMPACT: for each of the 5 rubric criteria, one sentence on how this milestone helps or hurts the score.
4. DEMO-DAY RISKS: the top 3 UI failure scenarios and how to mitigate each.
5. ACCESSIBILITY & RESPONSIVENESS AUDIT: top 3 improvements for mobile and keyboard navigation.

Do not rewrite whole files. Quote exact lines when you cite problems.

--- BUNDLE STARTS BELOW ---
{PASTE reviews/{ID}_review.txt HERE}
```

After the answer: paste Argon 4's response into `docs/reviews/{ID}-argon4-findings.md` (convert the findings table), then continue with step 6 of `AGENTS.md` §5.

---

## 4. Quick-resume prompt (use when starting a new chat mid-milestone)

```text
Resume work on Kairos as {DuroT (backend) | Peace (frontend)}. Re-read AGENTS.md and my playbook, run `git status`, `git log --oneline -n 10` and `git branch --show-current`, summarise which acceptance criteria of milestone {ID} are done and which remain, then continue with the next unfinished step. Do not start another milestone.
```
