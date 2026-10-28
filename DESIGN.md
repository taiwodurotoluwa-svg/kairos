---
version: 3.0.0
name: Kairos
theme: Editorial Kinetic Science
description: An original, high-contrast editorial research product in canvas white, midnight ink, electric iris, sunset coral, and lagoon teal. Combines experimental academic typography with bold paper compositions, tactile physical borders, and multi-modal evidence signals.
---

# DESIGN.md — Kairos "Editorial Kinetic Science" Design System

## 0. Authority & Design Philosophy (`Peaceyy28`)

**Peace (`Peaceyy28`) holds creative authority** over the visual identity, spatial layout, typography, and theme system of Kairos for OPEN//BUILD 2026.

### Core Creative Concept
> **"Research was never meant to whisper. It was meant to debate."**  
> *Every paper is a voice. Kairos lets the evidence meet.*

Kairos is an open-source literature synthesis and contradiction engine for scientific papers. It is not an ordinary summarisation chatbot or a sterile enterprise dashboard. The interface communicates curiosity, investigation, intellectual tension, and discovery.

### Signature Aesthetic Pillars
1. **Editorial Freedom & Scientific Rigour:** Experimental editorial typography (`Newsreader` serif italics alongside geometric `Plus Jakarta Sans` and monospace `Space Mono`) paired with structured scientific grids and verbatim provenance citations.
2. **Tactile Paper Surfaces & Physical Borders:** High-contrast `1.5px` and `2px` midnight ink (`#0A0F1D`) outlines with offset box-shadows (`3px 3px 0 #0A0F1D`, `5px 5px 0 #0A0F1D`, `7px 7px 0 #0A0F1D`). Layered research paper compositions with subtle dynamic tilts (`rotate(-8deg)`, `rotate(9deg)`).
3. **Intentional Chromatic Tension:** High-contrast palette where color represents intellectual relationships:
   - **Canvas Background:** `#F8FAFC`
   - **Midnight Ink:** `#0A0F1D` (text, borders, referee panel, footer)
   - **Electric Iris:** `#4F46E5` (primary brand, active focus, key highlights)
   - **Sunset Coral:** `#FF3366` (contradictions, Study A claim cards, brand period `kairos.`)
   - **Electric Lagoon / Teal:** `#00D2C4` / `#DDFBF6` (agreements, Study B claim cards)
   - **Sunflower Gold:** `#FFB703` (methodology differences, text highlights, referee accents, VS badge)
   - **Emerald Mint:** `#10B981` (system health pulse, live engine status)

---

## 1. Master Design Tokens

All styling in `frontend/css/styles.css` is driven by CSS Custom Properties on `:root`:

### 1.1 Color Palette & Surfaces

| Token | Hex Value | Role & Usage |
| :--- | :--- | :--- |
| `--site-primary` | `#4F46E5` | Electric Iris: primary actions, focus rings, lead kickers |
| `--site-on-primary` | `#FFFFFF` | Text on electric iris actions |
| `--site-secondary` | `#0A0F1D` | Midnight Ink: high-contrast text, borders, dark cards, footer |
| `--site-on-secondary` | `#FFFFFF` | Text on midnight ink surfaces |
| `--site-background` | `#F8FAFC` | Clean canvas background |
| `--site-on-background`| `#0A0F1D` | Default body and heading ink |
| `--site-accent-coral` | `#FF3366` | Sunset Coral: brand dot, contradictions, Study A cards |
| `--site-coral-soft`   | `#FFE3EA` | Soft coral wash for contradiction cards |
| `--site-accent-teal`  | `#00D2C4` | Lagoon Teal: agreements, Study B badges |
| `--site-teal-soft`    | `#DDFBF6` | Soft teal wash for agreement cards |
| `--site-accent-gold`  | `#FFB703` | Sunflower Gold: VS badge, methodology diffs, text highlights |
| `--site-accent-mint`  | `#10B981` | Emerald Mint: connected status pulse, successful validations |
| `--site-surface-iris` | `#E9E7FF` | Soft iris wash for evidence network feature card |

### 1.2 Multi-Modal Evidence Signals

Per OPEN//BUILD accessibility and contract rules, evidence signals **never rely on color alone**. Every signal couples color + icon/symbol + text label + line style:

| Signal Enum | Accent Color | Soft Surface | Icon | Text Label | Line Pattern |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `AGREE` | `#00B8A9` / `#10B981` | `#DDFBF6` | `✓` | Agree | Solid 2px |
| `CONTRADICT` | `#FF3366` | `#FFE3EA` | `⚠` | Contradiction | Solid 3px |
| `METHODOLOGY_DELTA` | `#D97706` / `#FFB703`| `#FEF3C7` | `≈` | Methodology difference | Dashed 2px `[6,4]` |
| `RESEARCH_GAP` | `#4F46E5` | `#E9E7FF` | `◌` | Research gap | Dotted 2px `[3,3]` |

---

## 2. Typography & Reading Hierarchy

| Role | Font Family | Weights | Usage & Characteristics |
| :--- | :--- | :--- | :--- |
| **Headings & Verbatim Quotes** | `"Newsreader", Georgia, serif` | `400` (italic quotes), `500`, `600` | Section titles (`h2 em`), verbatim quotes (`blockquote`), annotations (`.annotation`) |
| **Product UI & Body Copy** | `"Plus Jakarta Sans", "Inter", sans-serif` | `400`, `500`, `700`, `800`, `900` | Brand wordmark (`kairos.`), hero display typography, buttons, inputs |
| **Metadata, IDs & Telemetry** | `"Space Mono", monospace` | `400`, `700` | Overlines, step numbers, timestamps, paper page citations (`p. 08`), telemetry metrics |

---

## 3. Component Architecture & Master Layout

### 3.1 Top Navigation Bar (`.topbar`)
- Brand wordmark `kairos<span>.</span>` with coral period.
- Navigation links (`How it works`, `Dispute lab`, `Ingestion hub`, `Evidence map`).
- Preset corpus selector (`#preset-select`) styled with tactile midnight border.
- Engine status pill: pulsing green dot (`.pulse`) + `RESEARCH, CONNECTED`.

### 3.2 Hero Showcase (`.hero`)
- Split layout: Left editorial statement (`Research was never meant to whisper.`), primary CTAs ("Enter the dispute lab ↗", "Ingest research papers ↓").
- Right interactive paper art (`.hero-art`): Dashed orbit lines, tilted Study A card (`rotate(-8deg)`), tilted Study B card (`rotate(9deg)`), circular stamp badge (`SAME FIELD. NEW QUESTIONS.`), and handwritten editorial annotation (`wait, how?`).

### 3.3 Ticker Ribbon (`.ticker`)
- Monospace uppercase banner: `01 / Read across papers · 02 / Find the friction · 03 / Follow the evidence · Curiosity is a method ↗`.

### 3.4 The Dispute Lab (`#dispute`)
- Split-screen face-off:
  - **Study A Claim:** Sunset Coral card (`#FFE3EA`), verbatim quote, sample size, year.
  - **VS. Badge:** Sunflower Gold circle with 3px shadow (`transform: rotate(-9deg)`).
  - **Study B Claim:** Electric Lagoon card (`#DDFBF6`), verbatim quote, sample size, year.
  - **Referee Panel (`.referee`):** Deep Midnight Ink container with gold overline (`Referee notes / preview`), NLI rationale explanation, and interactive angle inspector button.

### 3.5 Ingestion Hub (`#ingest`) — Milestone P2
- Interactive drag-and-drop zone (`.dropzone`) accepting 2–10 PDF files (max 20MB per file).
- ArXiv ID/URL text input with instant regex validation.
- Staged papers queue with file metadata, size in KB/MB, and removal buttons.
- Primary CTA: `Synthesize Papers ↗` triggering the 4-stage pipeline simulator:
  1. `Ingesting & Chunking PDFs...`
  2. `Extracting Structured Claims (Llama-3.1-8B)...`
  3. `Pre-filtering & Cosine Clustering (BGE)...`
  4. `NLI Contradiction Refereeing & Synthesis...`

### 3.6 Synthesis Views (`#workspace` / `#library`)
- Multi-modal signal legend strip (`AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA`, `RESEARCH_GAP`) with live counts.
- Open-weight pipeline telemetry strip (`stats` object from API contract).
- View tab bar: `Comparison Matrix` (P3), `Contradiction Graph` (P4), `Consensus & Gaps` (P5).

### 3.7 Academic Footer (`.footer`)
- Midnight Ink background with gold italic accent `<em>better questions.</em>`.
- Open-weight attribution: `"Built with Llama"`, MIT License, GitHub link.
- Mandatory research limitation disclaimer: academic reading aid, not clinical decision software.
- Collapsible Open-Weight Model & Licence Registry table (`models[]`).
