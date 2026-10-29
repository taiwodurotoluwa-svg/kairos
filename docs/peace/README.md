# Frontend Execution Playbook — Peace

**Developer:** Oluwanifemi (Peace) (`Peaceyy28`, `oluwanifemipeace3@gmail.com`)  
**Workspace:** `/frontend`, `/docs/peace`  
**Stack (Approved):** **Vanilla HTML5, Vanilla CSS3, Modern JavaScript (ES6+), Cytoscape.js (CDN)**.  
**Local Tooling:** Zero Node/npm build steps required! Run with **VS Code Live Server** (port 5500) or `python -m http.server 5500` in `/frontend`.

> [!NOTE]
> Peace has full creative authority over the visual design and layout. The four signals (`AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA`, `RESEARCH_GAP`) must remain visually distinct and accessible (combining colour, icon/label, and line style).

---

## Final Frontend Directory Tree (Target after P5)

```text
frontend/
├── index.html           # Single Page Application shell (header, preset bar, tabs, views, drawer)
├── css/
│   └── styles.css       # Dark Academic Observatory design system (CSS variables, grid, matrix, drawer)
├── js/
│   ├── app.js           # Core state management, view switching, event bus, preset coordinator
│   ├── api.js           # Fetch wrapper with offline fallback to frontend/fixtures/*.json
│   ├── matrix.js        # Pinned-baseline comparison matrix renderer (6-8+ papers)
│   ├── graph.js         # Cytoscape.js interactive node-link contradiction network
│   └── drawer.js        # Slide-over evidence inspection panel (verbatim quotes, page, NLI rationale)
└── fixtures/            # Static local mock fixtures (mirrored from root /fixtures)
    ├── contract_sample.json
    ├── demo_radiology_8papers.json
    ├── demo_llm_quantization_6papers.json
    └── demo_microgrids_6papers.json
```

---

## Argon 4 Frontend Review Protocol (P1–P5)

Argon 4 (Gemini 1.5 Pro with High Thinking, temperature 0.2 in Google AI Studio) reviews **every frontend milestone** before clean code is committed to GitHub.

### What Argon 4 evaluates for Peace's frontend:
| Milestone | Frontend Focus Areas for Argon 4 |
| :--- | :--- |
| **P1: Shell & Design System** | Semantic HTML5 tags, CSS custom properties (`:root`), dark mode aesthetics, preset dropdown reactivity, responsive layout down to 375px, synthetic placeholder warning banner. |
| **P2: Ingestion Hub** | Drag-and-drop dropzone usability, client-side PDF file validation (max 10 files, 20MB limit), arXiv ID/URL input hygiene, pipeline progress state visualization. |
| **P3: Sticky Comparison Matrix** | Pinned baseline paper column stability during horizontal scroll (6–8+ papers), four-signal badge accessibility (icon + color + text label), hover popovers, quote provenance rendering. |
| **P4: Cytoscape Graph & Drawer** | Interactive node-link canvas rendering, force-directed `cose` physics performance, distinct signal edge styles (dashed ruby, solid emerald), slide-over dispute drawer focus trap, side-by-side claim quotes. |
| **P5: Consensus & Integration** | Consensus score ring gauge, research gaps display, live FastAPI vs offline mock toggle, error toast notifications, Markdown/JSON export, keyboard accessibility (tab navigation, escape key to close drawer). |

### Per-Milestone Review Steps for Peace:
1. Finish the milestone code in `frontend/`.
2. Test in browser (`http://127.0.0.1:5500`) and ensure **0 console errors**.
3. Export code, UI verification checklist, and critique questions into `reviews/P{n}_review.txt` (the prompt is embedded at the top).
4. **Do NOT commit the review file to git.** (It is ignored by `.gitignore`).
5. Upload or paste `reviews/P{n}_review.txt` into Argon 4.
6. Address any BLOCKER or MAJOR critique points in `frontend/`.
7. Commit and push clean, production-ready code to GitHub!

---

## Core Rules & Contracts
1. **Contract Parity:** Consume JSON exactly matching `docs/shared/02-api-contracts.md`. All model fields are `snake_case`.
2. **Offline-First:** P1–P4 build entirely against mock fixtures in `frontend/fixtures/`. The API client automatically tries `http://localhost:8000/api/v1/demo/{preset_id}` and falls back to local `./fixtures/{preset_id}.json` if the backend is offline.
3. **Strict Provenance:** Every claim and contradiction edge MUST display `{paper_title, section, page_number, verbatim_quote}`.
4. **Synthetic Data Warning:** Display a persistent warning banner whenever `fixture_provenance == "SYNTHETIC_PLACEHOLDER"`:
   *"Demo Data: Synthetically generated for interface testing. Not peer-reviewed scientific claims."*
5. **Footer Transparency:** Display `"Built with Llama"` and the open-weight model license table from `models[]`.
6. **Local AI Review Workflow:**
   - At the end of each milestone, export all changed code and verification notes into a local text file: `reviews/P{n}_review.txt` (e.g. `reviews/P1_review.txt`).
   - **Do NOT commit review files to GitHub.** (Ignored by `.gitignore`).
   - Upload or paste into Argon 4 (Google AI Studio, High thinking, temp 0.2) using `MASTER_PROMPTS.md` §3.
   - Address feedback in code, then commit and push clean code to GitHub!

---

## Milestone P1 — Vanilla SPA Shell & Dark Observatory Design System
**Branch:** `feat/p1-scaffold-design` | **Depends on:** `contract_sample.json` (exists) & D1 fixtures

### Steps:
1. Create `frontend/` directory structure: `css/styles.css`, `js/app.js`, `js/api.js`, `frontend/fixtures/`.
2. Copy fixtures from `/fixtures` into `frontend/fixtures/`.
3. In `index.html`:
   - Set up HTML5 doctype, meta tags, Inter/JetBrains Mono fonts, and Cytoscape.js CDN:
     `<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>`.
   - Build Header: Kairos logo, Hacktoberfest tag, Preset Selector dropdown (Radiology 8p, Quantization 6p, Microgrids 6p, Sample 3p).
   - Build Synthetic Data Banner: visible when `fixture_provenance == "SYNTHETIC_PLACEHOLDER"`.
   - Build Navigation Tabs: `[Comparison Matrix]`, `[Contradiction Graph]`, `[Consensus & Gaps]`.
   - Build View containers: `<section id="view-matrix">`, `<section id="view-graph">`, `<section id="view-consensus">`.
   - Build Footer: "Built with Llama", model attribution, hackathon info.
4. In `css/styles.css`:
   - Implement design tokens from `DESIGN.md` as CSS Custom Properties (`:root`), giving Peace full freedom to choose colors, surfaces, and theme variables.
   - Dark mode (or Peace's chosen aesthetic) with sleek cards, subtle borders, and smooth transitions.
5. In `js/api.js` & `js/app.js`:
   - Load default preset (`demo_radiology_8papers`) on boot.
   - Wire dropdown switch to re-fetch and dispatch `state:loaded` event to active view.
   - Ensure clean console with 0 errors.

### Acceptance Criteria:
- [ ] SPA loads cleanly in Chrome/Firefox via Live Server or `python -m http.server 5500`.
- [ ] Switching presets dynamically updates state without page reload.
- [ ] Synthetic placeholder banner renders conditionally based on payload.
- [ ] Mobile responsive layout down to 375px.
- [ ] Console shows 0 warnings, 0 syntax errors, 0 failed network requests.
- [ ] Local review file `reviews/P1_review.txt` generated for Argon 4 review.

---

## Milestone P2 — Ingestion Hub & Paper Management
**Branch:** `feat/p2-ingestion-hub` | **Depends on:** P1

### Steps:
1. Add Ingestion Modal / Section in `index.html`:
   - Drag-and-drop zone for 2–10 PDF files.
   - Text input for arXiv IDs (e.g. `2309.12345`) or URLs.
   - "Synthesize Papers" primary CTA button.
2. In `js/ingest.js`:
   - Client-side validation: file type `.pdf`, max 10 files, max 20MB per file.
   - Paper list preview showing file names, sizes, and remove buttons.
   - Mock pipeline progress simulator: 4 steps with animated status pills:
     1. Ingesting & Chunking PDFs...
     2. Extracting Structured Claims (Llama-3.1-8B)...
     3. Pre-filtering & Cosine Clustering (BGE)...
     4. NLI Contradiction Refereeing & Synthesis...

### Acceptance Criteria:
- [ ] Dropzone accepts drag-and-drop or file browser selection.
- [ ] Validates paper count (min 2, max 10) and prevents non-PDF uploads.
- [ ] Simulated or live progress steps update dynamically.
- [ ] Local review file `reviews/P2_review.txt` generated for Argon 4 review.

---

## Milestone P3 — Pinned-Baseline Synthesis Matrix
**Branch:** `feat/p3-synthesis-matrix` | **Depends on:** P1 (+ D1 fixtures)

### Steps:
1. In `js/matrix.js`:
   - Render comparison matrix: rows = topic clusters & claims, columns = papers.
   - **Pinned/Sticky Baseline Column:** Paper 1 stays fixed on the left while Papers 2–8 scroll horizontally.
   - Each cell displays:
     - Agreement badge: `AGREE` (Emerald Check), `CONTRADICT` (Ruby Cross), `METHODOLOGY_DELTA` (Amber Triangle), `RESEARCH_GAP` (Cyan Circle).
     - Hover popover showing verbatim quote, section, and page number.
   - Baseline Paper selector dropdown allowing user to swap which paper serves as the baseline.
2. In `css/styles.css`:
   - Add `.matrix-table`, `.sticky-col`, `.signal-badge` with dark observatory styling.

### Acceptance Criteria:
- [ ] Matrix handles 8 papers cleanly with smooth horizontal scroll.
- [ ] Pinned baseline column never obscures headers or scrolls out of view.
- [ ] Signals are distinguished by both colour AND icon/label.
- [ ] Clicking a cell triggers quote display or opens dispute details.
- [ ] Local review file `reviews/P3_review.txt` generated for Argon 4 review.

---

## Milestone P4 — Cytoscape.js Contradiction Graph & Dispute Drawer
**Branch:** `feat/p4-graph-dispute` | **Depends on:** P3

### Steps:
1. In `js/graph.js`:
   - Initialize Cytoscape container inside `#view-graph`.
   - Node definitions: Papers (circles sized by claim count, labeled with paper title/author).
   - Edge definitions: Cross-paper relations (`CONTRADICT`, `AGREE`, `METHODOLOGY_DELTA`).
   - Visual encoding:
     - Ruby thick dashed line = `CONTRADICT`.
     - Emerald solid line = `AGREE`.
     - Amber dotted line = `METHODOLOGY_DELTA`.
   - Layout: `cose` (Compound Spring Embedder) force-directed physics layout with fit-to-view.
   - Controls: Zoom In, Zoom Out, Reset Fit, Filter by Signal type checkboxes.
2. In `js/drawer.js`:
   - Slide-over inspection drawer on the right edge.
   - Triggered when clicking any contradiction edge or matrix dispute cell.
   - Displays side-by-side claim comparison:
     - Paper A: Title, Section, Page, Verbatim Quote.
     - Paper B: Title, Section, Page, Verbatim Quote.
     - Referee analysis: NLI confidence score and verbatim reasoning explanation.
   - Escape key and close button smoothly dismiss the drawer.

### Acceptance Criteria:
- [x] Cytoscape graph renders 8 papers and all cross-paper edges without node overlap.
- [x] Zoom and pan work smoothly at 60fps.
- [x] Clicking any edge opens the dispute drawer with verbatim quote evidence.
- [x] Accessible edge list table provided below canvas for keyboard and screen-reader users.
- [ ] Local review file `reviews/P4_review.txt` generated for Argon 4 review.

---

## Milestone P5 — Consensus Summary, Live Integration & Final Polish
**Branch:** `feat/p5-consensus-integration` | **Depends on:** P4 (+ D5 backend)

### Steps:
1. In `js/consensus.js`:
   - Render Overall Consensus Score gauge/ring (e.g. 56% Consensus).
   - Render Key Scientific Agreements list with supporting paper citations.
   - Render Top Contradictions callout cards with dispute severity.
   - Render Identified Research Gaps with potential future exploration notes.
2. Live Backend Connection:
   - Configure toggle in navbar: `[Demo Presets (Offline)]` vs `[Live Pipeline (FastAPI)]`.
   - When Live is selected, submit multi-part form to `POST /api/v1/analyze`.
3. Export Features:
   - "Export Synthesis Report" button: downloads comprehensive Markdown summary or JSON payload.
4. Final accessibility, responsive styling, and presentation audit.

### Acceptance Criteria:
- [x] Consensus view accurately reflects stats and clusters from active payload.
- [x] Seamless fallback between live FastAPI server and local mock presets.
- [x] Markdown export generates clean formatted report.
- [x] Local review file `reviews/P5_review.txt` generated for Argon 4 review.

---

## Verification & Testing Guide
Since this is pure Vanilla HTML/CSS/JS:
- Open `frontend/index.html` in Chrome / Firefox using Live Server (`http://127.0.0.1:5500/frontend/index.html`).
- Open Developer Tools (`F12`), check Console tab: must show **0 errors**.
- Test mobile viewports using device emulation (iPhone 14, iPad, 1080p Desktop).
