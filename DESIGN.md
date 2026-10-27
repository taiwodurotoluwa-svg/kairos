---
version: 1.0.0
name: Kairos
theme: Dark Academic Observatory
description: A calm, high-contrast dark interface for reading across many papers at once. Three signal colours carry meaning (agree, contradict, methodology difference); a violet signal marks research gaps.
---

# DESIGN.md — Kairos "Dark Academic Observatory"

## 0. Creative override clause (Peaceyy28 authority)

The tokens in this file are the **default baseline** so that every coding agent produces a cohesive UI from P1 to P5 without waiting on design decisions.

**Peace (`Peaceyy28`) has full creative authority** to change the visual aesthetic, spatial layout, animations, typography or theme at any point. Agents must follow Peace's instructions over this file when they conflict. Two conditions must always hold:

1. The four semantic signals stay **visually distinct from each other and from every other UI colour**, and stay bound to the API enums: `AGREE`, `CONTRADICT`, `METHODOLOGY_DELTA` (edge `relation`) and `RESEARCH_GAP` (`ResearchGap.signal`). Colour is never the only cue (see §3).
2. Quote text, section name and page number stay visible wherever a claim or edge is shown (hard rule 3 in `AGENTS.md`).

If Peace changes tokens, she updates this file in the same PR (she may edit it alone) and she updates the CSS custom properties in `frontend/css/styles.css` accordingly.

---

## 1. Colour tokens

### Surfaces and text

| Token | Hex | Use |
| :--- | :--- | :--- |
| `bg` | `#0B0F17` | Page background (Obsidian Slate) |
| `surface` | `#111827` | Cards, panels, table body |
| `surface-2` | `#1A2233` | Inputs, table header, raised elements |
| `surface-3` | `#243049` | Hover and selected states |
| `line` | `#2B3752` | Default borders and dividers |
| `line-strong` | `#3D4B6B` | Focus-adjacent borders, active inputs |
| `ink` | `#E5E7EB` | Primary text |
| `ink-muted` | `#9CA3AF` | Secondary text |
| `ink-faint` | `#6B7280` | Captions, disabled (never for essential info) |
| `accent` | `#60A5FA` | Primary buttons, links, focus ring |
| `accent-strong` | `#3B82F6` | Button hover |

### Semantic signals (bound to API enums)

| Signal | Enum | Solid | Soft background | Border | Icon | Line style |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Emerald Consensus | `AGREE` | `#10B981` | `rgba(16,185,129,0.14)` | `rgba(16,185,129,0.45)` | `Check` | solid, 2px |
| Crimson Contradiction | `CONTRADICT` | `#EF4444` | `rgba(239,68,68,0.14)` | `rgba(239,68,68,0.45)` | `AlertTriangle` | solid, 3px |
| Amber Methodology Delta | `METHODOLOGY_DELTA` | `#F59E0B` | `rgba(245,158,11,0.14)` | `rgba(245,158,11,0.45)` | `GitCompare` | dashed `[6,4]`, 2px |
| Violet Research Gap | `RESEARCH_GAP` | `#A78BFA` | `rgba(167,139,250,0.14)` | `rgba(167,139,250,0.45)` | `Telescope` | dotted node outline |

Contrast of each solid colour against `bg` is at least 5:1.

### Paper palette (graph node rings and table header chips)

Ten cool, desaturated hues, deliberately **excluding green, red, amber and violet** so they cannot be confused with signals. Index = `PaperMetadata.palette_index`.

`0 #38BDF8` · `1 #60A5FA` · `2 #22D3EE` · `3 #818CF8` · `4 #94A3B8` · `5 #E2E8F0` · `6 #7DD3FC` · `7 #C7D2FE` · `8 #BAE6FD` · `9 #CBD5E1`

Because several are similar, **every paper is also identified by its `short_label` (`P1`…`P10`) printed inside the node and in the chip**. Never rely on ring colour alone.

### Tailwind config (default)

```ts
// frontend/tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#0B0F17",
        surface: { DEFAULT: "#111827", 2: "#1A2233", 3: "#243049" },
        line: { DEFAULT: "#2B3752", strong: "#3D4B6B" },
        ink: { DEFAULT: "#E5E7EB", muted: "#9CA3AF", faint: "#6B7280" },
        accent: { DEFAULT: "#60A5FA", strong: "#3B82F6" },
        agree: { DEFAULT: "#10B981", soft: "rgba(16,185,129,0.14)", border: "rgba(16,185,129,0.45)" },
        contradict: { DEFAULT: "#EF4444", soft: "rgba(239,68,68,0.14)", border: "rgba(239,68,68,0.45)" },
        delta: { DEFAULT: "#F59E0B", soft: "rgba(245,158,11,0.14)", border: "rgba(245,158,11,0.45)" },
        gap: { DEFAULT: "#A78BFA", soft: "rgba(167,139,250,0.14)", border: "rgba(167,139,250,0.45)" },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
        serif: ["var(--font-newsreader)", "Georgia", "serif"],
        mono: ["var(--font-jetbrains)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: { card: "14px", pill: "9999px" },
      boxShadow: {
        card: "0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 24px rgba(0,0,0,0.35)",
        drawer: "-24px 0 64px rgba(0,0,0,0.55)",
      },
      keyframes: {
        "fade-up": { from: { opacity: "0", transform: "translateY(6px)" }, to: { opacity: "1", transform: "none" } },
        "slide-in-right": { from: { transform: "translateX(24px)", opacity: "0" }, to: { transform: "none", opacity: "1" } },
      },
      animation: {
        "fade-up": "fade-up 180ms ease-out both",
        "slide-in-right": "slide-in-right 200ms cubic-bezier(0.2,0.8,0.2,1) both",
      },
    },
  },
  plugins: [],
};
export default config;
```

---

## 2. Typography

| Role | Font | Weight | Size / line-height |
| :--- | :--- | :--- | :--- |
| Page and section headings, quote text | `Newsreader` (serif) or `Instrument Serif` | 500–600 | h1 40/44, h2 28/34, h3 20/28 |
| UI text, tables, buttons | `Inter` | 400/500/600 | body 14/22, small 12/18 |
| Metrics, page badges, ids, confidence | `JetBrains Mono` | 500 | 12–13/18 |

Load with `next/font/google` and expose CSS variables:

```tsx
// frontend/src/app/layout.tsx (excerpt)
import { Inter, Newsreader, JetBrains_Mono } from "next/font/google";
const inter = Inter({ subsets: ["latin"], variable: "--font-inter", display: "swap" });
const newsreader = Newsreader({ subsets: ["latin"], variable: "--font-newsreader", display: "swap", style: ["normal", "italic"] });
const mono = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains", display: "swap" });
// <html className={`${inter.variable} ${newsreader.variable} ${mono.variable}`}>
```

Verbatim quotes render in `font-serif italic` inside a left-bordered block, always followed by a mono badge `p. {page_number} · {SECTION}`.

---

## 3. Signal rendering rules (colour is never the only cue)

| Signal | Colour | Shape / line | Icon | Text label |
| :--- | :--- | :--- | :--- | :--- |
| `AGREE` | emerald | solid 2px edge | check | "Agree" |
| `CONTRADICT` | crimson | solid 3px edge, thickest | triangle-alert | "Contradiction" |
| `METHODOLOGY_DELTA` | amber | dashed edge | git-compare | "Methodology difference" |
| `RESEARCH_GAP` | violet | dotted hollow node outline | telescope | "Research gap" |

Every badge shows icon + label + colour. The graph legend lists all four.

---

## 4. Layout blueprint (single page, `src/app/page.tsx`)

```
┌─ Header: logo "Kairos" · tagline · GitHub link · "Built with Llama" ────────────┐
├─ PresetBar: [Radiology (8)] [LLM Quantization (6)] [Microgrids (6)] [Upload]  ──┤
├─ SyntheticBanner (only if fixture_provenance = SYNTHETIC_PLACEHOLDER) ──────────┤
├─ StatsStrip: papers · claims · pairs checked · pair reduction % · latency  ─────┤
├─ Tabs: [ Synthesis Matrix ] [ Contradiction Graph ] [ Consensus & Gaps ] ───────┤
│   (default tab: Synthesis Matrix)                                               │
├─ Footer: model + licence table · AI-assistance note · repo link ────────────────┤
└─────────────────────────────────────────────────────────────────────────────────┘
```

Container max width 1280px, page padding 24px (16px under 640px). Section spacing 32px. Cards use `rounded-card border border-line bg-surface shadow-card`.

### 4.1 Sticky-baseline Synthesis Matrix (6–8+ papers)

- **Orientation:** rows are attributes; **columns are papers**. Attributes (in order): `Dataset`, `Sample size`, `Methodology`, `Primary metric`, `Limitations`, `Core conclusion`.
- **Columns:** column 0 = attribute labels (sticky, `left: 0`, width 168px). The **pinned baseline paper** is rendered immediately after, also sticky (`left: 168px`). All remaining papers scroll horizontally, each `min-width: 280px`, `max-width: 320px`.
- **Pinning:** each paper header has a pin button (`Pin` icon). Exactly one baseline at a time, default = `P1`. Pinning re-orders columns client-side (baseline first, others in `short_label` order).
- **Relation-to-baseline row** (directly under the header): three counters per non-baseline paper derived from `edges` between that paper and the baseline — `✓ n` (agree), `⚠ n` (contradict), `≈ n` (methodology delta). Zero counts are dimmed.
- **Conflict highlighting toggle** "Highlight conflicting methodologies" (default ON): in the `Methodology` and `Dataset` rows, cells of papers that share a `METHODOLOGY_DELTA` edge with the baseline get the amber soft background and amber left border; in the `Core conclusion` row, cells of papers that share a `CONTRADICT` edge with the baseline get the crimson soft background and crimson left border.
- **Search/filter box:** case-insensitive substring; non-matching cells dim to 35% opacity, matches wrap the matched text in `<mark>` styled with `bg-accent/25`.
- **Density:** cell text 13px/20px, clamp to 5 lines with a "Show more" toggle per cell.
- **Sticky mechanics (reference):**

```tsx
<div className="relative overflow-x-auto rounded-card border border-line">
  <table className="min-w-max border-separate border-spacing-0 text-sm">
    <thead>
      <tr>
        <th className="sticky left-0 z-30 w-[168px] bg-surface-2 p-3 text-left">Attribute</th>
        <th className="sticky left-[168px] z-20 w-[300px] bg-surface-2 p-3 shadow-[8px_0_16px_-8px_rgba(0,0,0,0.6)]">Baseline</th>
        {others.map((p) => (<th key={p.paper_id} className="min-w-[280px] max-w-[320px] bg-surface-2 p-3">{/* chip + title + pin */}</th>))}
      </tr>
    </thead>
    {/* tbody mirrors the same sticky classes on the first two cells of every row */}
  </table>
</div>
```

### 4.2 Contradiction Graph

- **Canvas:** `react-force-graph-2d` (dynamic import, `ssr: false`), height `clamp(480px, 70vh, 760px)`, dark background `bg`.
- **Nodes = claims.** Radius `6 + 2 * degree` (cap 16). Fill `surface-2`; **ring** = paper palette colour (2.5px); the paper `short_label` is drawn inside nodes with radius ≥ 10, otherwise on hover. Research-gap nodes: hollow, dotted violet outline, telescope marker.
- **Labels:** show claim `topic_hint` only on hover, on selection, or when zoom ≥ 1.8. Never label everything.
- **Edges:** colour/width/dash per §3. Opacity 0.9 normally, 0.15 when another node/edge is focused. `linkHoverPrecision = 8` so thin edges stay clickable. Arrowheads off.
- **Filter bar** (above canvas, sticky within the tab):
  1. **Cluster pills** — one pill per `TopicCluster.label` with claim count; multi-select; "All" resets.
  2. **Paper chips** — `P1…Pn`, toggle visibility of a paper's nodes.
  3. **Relation toggles** — `Agree`, `Contradict`, `Methodology`, `Gaps`, each with its signal icon.
  4. **"Isolate contradictions"** switch — shows only `CONTRADICT` edges and their endpoint nodes (everything else hidden, not dimmed).
  5. **Min confidence** slider, default 0.50, step 0.05.
  6. A live counter: "Showing {e} of {E} relations across {n} papers".
- **Interaction:** hover edge → tooltip with relation + confidence; click edge → open Dispute Drawer; click node → focus its neighbours (others dim); click background → clear focus; double-click background → zoom to fit.
- **Accessible alternative:** an **edge list** below the canvas (a real `<table>`) with the same filters applied. Each row has a button that opens the same drawer. Keyboard users never need the canvas.
- **Legend** (bottom-left of canvas): the four signals with icon, label and line sample.

### 4.3 Dispute Inspection Drawer (slide-over)

- Right-side drawer, width `min(560px, 100vw)`, `role="dialog" aria-modal="true"`, focus trap, `Esc` closes, overlay click closes, return focus to the trigger.
- **Header:** relation badge (icon + label), confidence as mono `0.93`, cosine similarity as mono `sim 0.91`, close button.
- **Body:**
  1. **Two quote cards** side by side (stacked under 640px). Each: paper chip (`P2`), citation label, paper title (2-line clamp), the verbatim quote (serif italic, left border in the paper colour), and the mono badge `p. 7 · RESULTS`. Underneath each: the claim `statement` and `metric_value` if present.
  2. **Referee explanation** block tinted with the relation's soft colour: heading "Why they differ" (or "Why they agree" for `AGREE`) and the `explanation` text.
  3. **Context row:** each paper's `dataset`, `sample_size`, `methodology` in a compact two-column table.
  4. Actions: **Copy citation block** (both quotes with page numbers), **Previous / Next dispute** (cycles through the currently filtered edge list; also `←` / `→`).
- Motion: `animate-slide-in-right`; disabled when `prefers-reduced-motion`.

### 4.4 Consensus & Gaps tab

- **Score ring:** SVG ring showing `consensus_score` (0–100) with the label "Consensus score". Colour: crimson < 40, amber 40–69, emerald ≥ 70. Under it, the formula tooltip from `02-api-contracts.md` §6.
- **Executive summary** card (serif, 16/26).
- Two columns: **Where the papers agree** (emerald check list) and **Top contradictions** (crimson list; each item is a button that opens the Dispute Drawer for its `edge_id`).
- **Research gaps panel:** violet cards, one per `gaps[]` entry, showing statement, quote with `p. N · SECTION`, and `reason`. Show first 6 with "Show all".
- **Recommended next steps** numbered list.
- **Export Literature Review** button group: `Markdown`, `LaTeX` (see `docs/peace/README.md` P5 for exact templates).

### 4.5 Ingestion Hub (P2)

- Dropzone card with dashed border; drag-over state uses `accent` border and `surface-3` background.
- Paper cards (one per file or arXiv id): filename/id, size, remove button, status chip. Counter "6 of 10 papers (min 2)".
- arXiv input accepts bare ids or URLs, validates client-side with the same normalisation rules as the backend, and shows inline errors.
- **Pipeline progress** stepper with seven labelled steps mapped to `PipelineStage`, a progress bar from `progress_pct`, and the latest `message`.

---

## 5. Responsive behaviour

| Breakpoint | Behaviour |
| :--- | :--- |
| ≥ 1280px | Full layout; matrix shows baseline + ~3 papers without scrolling |
| 768–1279px | Matrix scrolls horizontally; filter bar wraps to two rows |
| < 768px | Tabs become a segmented control; drawer is full-screen; quote cards stack; graph height 55vh with an edge-list-first layout (list above canvas) |

---

## 6. Motion and states

- Durations 150–220ms, `ease-out`. Skeleton shimmer for loading; spinners only inside buttons.
- Respect `prefers-reduced-motion: reduce`: disable translate/scale animations and the graph's continuous force simulation after it settles (`cooldownTicks = 120`).
- Empty states: friendly serif headline + one primary action ("Load a preset" / "Add papers").
- Error states: inline callout with the API `message`, a **Retry** button and, when a preset exists, a **Load demo preset instead** button.

## 7. Content rules

- Tone: precise, calm, academic. No hype words.
- Always show a small "Built with Llama" line in the footer and the model/licence table (`models[]` from the result).
- When `fixture_provenance = SYNTHETIC_PLACEHOLDER`, show a persistent amber banner: **"Synthetic placeholder data — not real research."**
