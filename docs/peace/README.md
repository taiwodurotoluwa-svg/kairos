# Frontend Engineering Roadmap (Oluwanifemi / Peace)

* **Developer:** Oluwanifemi Peace (`Peaceyy28`)
* **Role:** Frontend UI/UX, Cytoscape Contradiction Graph, Comparison Matrix, Consensus Dashboard.
* **Goal:** Build an aesthetic, intuitive, and responsive web application for Kairos.

---

## The 5 Phased Tasks & PR Flow

### Task P1: Project Scaffold, Design Tokens, & Paper Dropzone
* **Branch:** `peace/task-p1-scaffold-dropzone`
* **Files to create/modify:** `frontend/src/app/`, `frontend/src/components/Dropzone.tsx`, `frontend/src/types/`
* **Scope:**
  * Initialize Next.js 14 / React with Tailwind CSS using tokens from `DESIGN.md`.
  * Build beautiful drag-and-drop file upload zone accepting 3 to 5 PDFs with file badges.
  * Add **"Try Sample Datasets"** one-click selector (Radiology, Hallucinations, Microgrids) for instant demoing.
* **Argon 4 Review Gate:** Review upload validation, accessibility, and drag-and-drop state transitions.
* **PR:** Merge `peace/task-p1-scaffold-dropzone` into `main`.

---

### Task P2: Side-by-Side Comparison Matrix Table
* **Branch:** `peace/task-p2-comparison-table`
* **Files to create/modify:** `frontend/src/components/ComparisonTable.tsx`
* **Scope:**
  * Responsive table comparing Paper Title/Year, Dataset ($n$, source), Methodology, Key Metric, and Main Conclusion.
  * Sticky column headers with horizontal scrolling support.
  * Search/filter bar to highlight specific variables (e.g. "Accuracy", "ResNet").
* **Argon 4 Review Gate:** Review mobile/tablet responsiveness and typography hierarchy.
* **PR:** Merge `peace/task-p2-comparison-table` into `main`.

---

### Task P3: Interactive Contradiction Node Graph (The Wow Factor)
* **Branch:** `peace/task-p3-contradiction-graph`
* **Files to create/modify:** `frontend/src/components/ContradictionGraph.tsx`, `frontend/src/components/DisputeModal.tsx`
* **Scope:**
  * Render interactive graph network using Cytoscape.js, React Flow, or Force-Graph.
  * Nodes: Papers (Indigo) and Claims (Cyan).
  * Edges: **Green lines** for Agreements, **Red lines** for Contradictions.
  * Clicking any Red/Green edge opens a **Slide-over Drawer / Modal**:
    * Displays Claim A vs Claim B side-by-side.
    * Highlights verbatim quoted text and page numbers from each paper.
    * Displays the AI Referee's diagnosis of why their results diverged.
* **Argon 4 Review Gate:** Review canvas rendering performance, edge click hitboxes, and modal layout.
* **PR:** Merge `peace/task-p3-contradiction-graph` into `main`.

---

### Task P4: Consensus Executive Summary & Export Dossier
* **Branch:** `peace/task-p4-consensus-summary`
* **Files to create/modify:** `frontend/src/components/ConsensusSummary.tsx`, `frontend/src/utils/export.ts`
* **Scope:**
  * Visual card split into "Where the Science Agrees" and "Active Controversies".
  * 1-Click **Export Synthesis Dossier** (downloads formatted Markdown report or BibTeX citations).
* **Argon 4 Review Gate:** Review export formatting and summary card layout.
* **PR:** Merge `peace/task-p4-consensus-summary` into `main`.

---

### Task P5: Full API Hookup, Loading States, & Vercel Deployment
* **Branch:** `peace/task-p5-integration-deploy`
* **Files to create/modify:** `frontend/src/services/api.ts`, `frontend/src/app/page.tsx`
* **Scope:**
  * Connect frontend state to Duro's backend (`/api/synthesize` and `/api/sample/{id}`).
  * Implement polished skeleton loaders and animated progress steps ("Extracting sections... Matching claims... Refereeing contradictions...").
  * Deploy to Vercel and verify live production link works seamlessly.
* **Argon 4 Review Gate:** Final audit on end-to-end user experience, error toasts, and responsive layout.
* **PR:** Merge `peace/task-p5-integration-deploy` into `main`.
