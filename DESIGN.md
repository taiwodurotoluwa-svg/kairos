---
version: 1.0.0
project: Kairos
aesthetic: Academic Editorial Dark Mode (Developer-grade, Clean, High Contrast)
---

# DESIGN.md — Kairos Design System

A modern, high-contrast editorial dark theme built for academic clarity. Uses deep navy-blacks, crisp borders, high-legibility typography, and high-impact semantic badges.

---

## 1. Color Palette

### Base Surfaces
* **Background:** `#090D16` (Deep void midnight)
* **Surface-1 (Cards / Panels):** `#0F172A` (Slate dark)
* **Surface-2 (Inputs / Sub-panels):** `#1E293B` (Muted surface)
* **Surface-3 (Hover / Active):** `#293548`
* **Border Default:** `#334155` (Subtle boundary)
* **Border Strong:** `#475569` (Active / Focus ring)

### Typography Colors
* **Text Primary:** `#F8FAFC` (Pure readable white)
* **Text Secondary:** `#94A3B8` (Soft muted slate)
* **Text Tertiary:** `#64748B` (Captions / metadata)

### Semantic Signals (Graph & Table)
* **Accent Primary:** `#6366F1` (Electric Indigo) / `#38BDF8` (Sky Blue)
* **Agreement (Entailment):** `#10B981` (Emerald Green)
  * Soft badge background: `rgba(16, 185, 129, 0.12)`
  * Glow ring: `rgba(16, 185, 129, 0.35)`
* **Contradiction (Conflict):** `#EF4444` (Crimson Red)
  * Soft badge background: `rgba(239, 68, 68, 0.12)`
  * Glow ring: `rgba(239, 68, 68, 0.35)`
* **Neutral / Unrelated:** `#64748B` (Slate)

---

## 2. Typography

* **Headings & Brand:** `Plus Jakarta Sans` or `Inter`, font-weight 700 / 600.
* **Body Text:** `Inter`, font-weight 400 / 500, line-height 1.6.
* **Metrics & Citations (Monospace):** `JetBrains Mono` or `Geist Mono` for dataset sizes, confidence scores, and raw quotes.

---

## 3. UI Component Specifications

### A. Side-by-Side Comparison Table
* Sticky header with paper title and publication year.
* Columns: `Paper Details | Dataset | Methodology | Key Metric | Conclusion & Core Finding`.
* Zebra striping on hover (`bg-slate-800/40`).
* Metric pill badges (e.g. `94.2% Acc`, `n = 1,200`).

### B. Interactive Contradiction Graph (Cytoscape / React Flow / Force-Graph)
* **Nodes:**
  * Shape: Circle / Rounded Capsule.
  * Color: Indigo for Paper nodes (`#6366F1`), Cyan for Claim nodes (`#38BDF8`).
  * Label: Paper short name (e.g. *Chen et al. (2024)*) + abbreviated claim.
* **Edges:**
  * **Green solid line:** Direct agreement (`AGREE`).
  * **Red dashed/solid line with alert icon:** Direct contradiction (`CONTRADICT`).
* **Interactivity:**
  * Clicking an edge triggers a **Slide-over Drawer / Modal**:
    * Left side: Paper A claim + verbatim page quotation.
    * Right side: Paper B claim + verbatim page quotation.
    * Center pill: AI Referee Diagnosis explaining *why* they disagree (e.g. *"Paper A evaluated on clean lab data; Paper B tested on noisy out-of-distribution hospital records"*).

### C. Consensus Executive Summary Card
* Split into two distinct panels:
  * **Where the Literature Agrees (Green check icon)**
  * **Active Scientific Disputes (Red alert icon)**
* Includes a 1-click **Export Synthesis Dossier** button (Markdown / JSON).
