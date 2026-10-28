---
version: 2.2.0
name: Kairos
theme: Sapphire Nightfall Whisper (Light Editorial Workspace)
description: A clean, human academic research workspace in midnight ink, deep slate, and sapphire, with crisp paper surfaces and restrained multi-modal evidence signals, optimized for daylight research reading.
---

# DESIGN.md — Kairos "Sapphire Nightfall Whisper" Design System

## 0. Authority & Design Philosophy (`Peaceyy28`)

**Peace (`Peaceyy28`) holds creative authority** over the visual identity, spatial layout, typography, and theme system of Kairos.

The approved aesthetic direction for Kairos is **Sapphire Nightfall Whisper (Light Editorial Workspace)**:
- **Calm, credible, and evidence-focused:** Designed like a serious archival research workspace and scholarly journal rather than a neon AI dashboard or generic SaaS template.
- **Exact, purposeful palette:**
  - `#0474C4` (Vibrant Sapphire): Interactive focus rings, active indicator lines, and primary callouts.
  - `#5379AE` (Steel Slate): Secondary structural borders and metadata hints.
  - `#4C70A2` (Steel Slate Deep): High-contrast secondary text and table column headers (5.1:1).
  - `#2C444C` (Deep Slate Teal): High-contrast indicator borders and dark dividers.
  - `#A8C4EC` (Frosted Sky): Subtle hairline grid borders and quiet container frames.
  - `#06457F` (Midnight Navy): Authoritative headings, brand wordmark, and primary actions (9.8:1).
  - `#262B40` (Midnight Ink Charcoal): High-contrast primary reading text and verbatim quotes (14.5:1).
  - `#FFFFFF` (Pure Paper White): Clean background canvas and primary card surfaces.
- **Flat, architectural hierarchy:** Pure hairline dividers (`1px solid`), tabular numbers, structured evidence grids, generous reading whitespace, and strong editorial typography (`Newsreader` serif for masthead and verbatim quotes, `Inter` for UI controls and tables, `JetBrains Mono` for page numbers, metrics, and identifiers). No gratuitous rounded pills, glowing shadows, or AI template cards.
- **Colour communicates meaning, never decoration:** Chromatic treatments are strictly reserved for evidence status (`AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA`, `RESEARCH_GAP`) and genuine warnings (`SYNTHETIC_PLACEHOLDER` provenance). Neutral metadata uses muted slate.

### Non-Negotiable Contract & Accessibility Rules
1. **Multi-modal evidence signals:** The four semantic signals (`AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA`, `RESEARCH_GAP`) must stay visually distinct and **never rely on colour alone** (always combine colour + icon/symbol + explicit text label + border/line style).
2. **Strict verbatim provenance:** Every displayed claim or comparison edge must visibly show its verbatim quote, section name, and page number (`p. {page_number} · {SECTION}`).
3. **Unmistakable synthetic provenance notice:** Whenever `fixture_provenance === "SYNTHETIC_PLACEHOLDER"`, display a persistent warning banner with the exact text:
   > *"Demo Data: Synthetically generated for interface testing. Not peer-reviewed scientific claims."*

---

## 1. Semantic Token System

All styling in `frontend/css/styles.css` is driven by CSS Custom Properties on `:root`:

### 1.1 Surfaces, Text, Borders & Interactive Accents

| Semantic Token | Value | Role & Usage |
| :--- | :--- | :--- |
| `--color-bg` | `#FFFFFF` *(Paper White)* | Page canvas background |
| `--color-surface` | `#FFFFFF` *(Paper White)* | Primary cards, panels, matrix cells, drawer |
| `--color-surface-2` | `#F0F4FA` *(Archival Slate Wash)* | Table headers, secondary panels, inputs |
| `--color-surface-3` | `#E2ECF8` *(Soft Sapphire Wash)* | Hover states, active row/tab highlight |
| `--color-ink` | `#262B40` *(Midnight Ink — 14.5:1)* | Primary headings, body copy, verbatim quotes |
| `--color-ink-muted` | `#4C70A2` *(Steel Slate — 5.1:1)* | Secondary text, labels, metadata captions |
| `--color-ink-faint` | `#5379AE` *(Steel Slate)* | Non-essential hints, structural dividers |
| `--color-accent` | `#06457F` *(Midnight Navy — 9.8:1)* | Primary actions, active tab indicator, links |
| `--color-accent-hover` | `#0474C4` *(Vibrant Sapphire)* | Primary button/control hover state |
| `--color-accent-contrast` | `#FFFFFF` *(Pure White)* | Text on solid primary accent buttons |
| `--color-accent-subtle` | `#F0F4FA` *(Soft Sky Wash)* | Selected tab/row background |
| `--color-line` | `#A8C4EC` *(Frosted Sky Line)* | Default 1px borders, table rules, dividers |
| `--color-line-strong` | `#5379AE` *(Steel Slate)* | Active input borders, emphasized card edges |
| `--color-focus-ring` | `#0474C4` *(Vibrant Sapphire)* | `2px solid` keyboard `:focus-visible` outline |

*(All primary and secondary text contrast ratios meet or exceed WCAG 2.1 AA 4.5:1.)*

### 1.2 Evidence-Status & Warning Tokens

| Status / Enum | Token Prefix | Values (`Solid` / `Soft BG` / `Border`) | Icon & Line Cue |
| :--- | :--- | :--- | :--- |
| **Agreement** (`AGREE`) | `--signal-agree` | `#1A6335` / `#EEF7F1` / `#82C49C` | `✓` · Label: `"Agree"` · Solid 2px line |
| **Contradiction** (`CONTRADICT`) | `--signal-contradict` | `#9E2325` / `#FBECEB` / `#D48D8E` | `⚠` · Label: `"Contradiction"` · Solid 3px line |
| **Methodology Delta** (`METHODOLOGY_DELTA`) | `--signal-delta` | `#7D5514` / `#FDF6E9` / `#CFA76B` | `≈` · Label: `"Methodology difference"` · Dashed `[6,4]` 2px |
| **Research Gap** (`RESEARCH_GAP`) | `--signal-gap` | `#06457F` / `#F0F4FA` / `#A8C4EC` | `◌` · Label: `"Research gap"` · Dotted 2px outline |
| **System / Provenance Warning** | `--status-warning` | `#8A4B08` / `#FFF8E1` / `#FFE082` | `!` · Reserved for actual warnings & synthetic banner |

---

## 2. Typography & Reading Hierarchy

| Role | Font Stack | Weight | Scale & Line Height |
| :--- | :--- | :--- | :--- |
| **Editorial Titles, Section Headings & Verbatim Quotes** | `--font-serif`: `'Newsreader', Georgia, 'Times New Roman', serif` | `400` (italic quotes), `500–600` (headings) | Brand `1.375rem` (22px), Section `h1`/`h2` `1.25rem–1.5rem`, Quotes `0.9375rem` (15px) / `1.6` |
| **UI Controls, Navigation, Tables & Body Copy** | `--font-sans`: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif` | `400`, `500`, `600` | Body `0.875rem` (14px) / `1.5`, Compact `0.8125rem` (13px) / `1.45` |
| **Metrics, Page Citations, IDs & Latency Stats** | `--font-mono`: `'JetBrains Mono', ui-monospace, SFMono-Regular, monospace` | `400`, `500` | `0.75rem–0.8125rem` (12px–13px) / `1.4` |
