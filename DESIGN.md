---
version: 1.1.0
name: Kairos
theme: Peace Creative Freedom & Design System
description: Flexible, accessible design system for Kairos multi-paper synthesis. Peace has 100% creative control over colors, aesthetic, and typography.
---

# DESIGN.md — Kairos Frontend Design Guide & Design System

## 0. Creative Authority & Agent Collaboration (Peaceyy28 Authority)

**Peace (`Peaceyy28`) has 100% full creative freedom** to define the visual identity, aesthetic direction, color palette, typography, spatial layout, and motion design of Kairos.

### Crucial Directive for Coding Agents Working with Peace:
1. **Never force hardcoded colors or a rigid aesthetic onto Peace.**
2. When starting frontend work or discussing design, the agent **MUST ask Peace for her input, preferred color scheme, and aesthetic direction** (e.g., sleek dark observatory, high-contrast dark, minimalist academic/editorial, neon cyberpunk, glassmorphic, or a custom look).
3. If Peace asks for ideas or requests recommendations, the agent should **recommend curated, accessible palettes** (such as the options outlined in Section 1 below) and help iterate on them.
4. All colors, surfaces, borders, and typography should be defined using **CSS Custom Properties (`:root { ... }`)** in `frontend/css/styles.css` so themes can be switched or tuned effortlessly.

### The Only Non-Negotiable Requirements:
1. **Semantic Distinctness & Multi-Modal Cues (Accessibility):**
   The four signals bound to the API must remain visually distinct from each other:
   - `AGREE` (edge `relation`)
   - `CONTRADICT` (edge `relation`)
   - `METHODOLOGY_DELTA` (edge `relation`)
   - `RESEARCH_GAP` (`ResearchGap.signal`)
   
   **Color is NEVER the only cue.** Always combine color with:
   - **Icon:** e.g., Check (`✓`) for agree, AlertTriangle (`⚠`) for contradiction, GitCompare (`≈`) for methodology delta, Telescope (`🔭`) for research gaps.
   - **Text label:** Always show the text ("Agree", "Contradiction", "Methodology difference", "Research gap").
   - **Line / Border Style:** e.g., solid 2px for agree, thick solid 3px for contradiction, dashed `[6, 4]` for methodology delta, dotted outline for research gaps.

2. **Verbatim Provenance:**
   Quote text, section name, and page number must remain visible wherever a claim or edge is displayed (`p. {page_number} · {SECTION}`).

---

## 1. Design Tokens & Palette Options

Instead of mandating rigid hex values, Kairos organizes styling into **CSS Custom Properties (`:root`)**. Peace has full freedom to set these values.

### 1.1 Semantic Token Roles (CSS Variables)

Peace can assign any colors to these tokens in `frontend/css/styles.css`:

```css
:root {
  /* Surface & Background Hierarchy */
  --color-bg: ...;            /* Page background */
  --color-surface: ...;       /* Cards, panels, main table body */
  --color-surface-2: ...;     /* Raised elements, headers, inputs */
  --color-surface-3: ...;     /* Hover states, selected rows */

  /* Borders & Dividers */
  --color-line: ...;          /* Standard card borders & grid dividers */
  --color-line-strong: ...;   /* Active borders, focus rings */

  /* Typography */
  --color-ink: ...;           /* Primary text / headers */
  --color-ink-muted: ...;     /* Secondary text, labels, subheadings */
  --color-ink-faint: ...;     /* Metadata badges, disabled states */

  /* Brand Accent */
  --color-accent: ...;        /* Primary CTA buttons, active tabs, focus ring */
  --color-accent-hover: ...;  /* Primary button hover state */

  /* Semantic Signal 1: Consensus / Agree */
  --signal-agree: ...;        /* Solid signal color */
  --signal-agree-soft: ...;   /* Soft tinted background (e.g. ~14% opacity) */
  --signal-agree-border: ...; /* Signal border (e.g. ~45% opacity) */

  /* Semantic Signal 2: Contradiction / Conflict */
  --signal-contradict: ...;        /* Solid signal color */
  --signal-contradict-soft: ...;   /* Soft tinted background */
  --signal-contradict-border: ...; /* Signal border */

  /* Semantic Signal 3: Methodology Delta */
  --signal-delta: ...;        /* Solid signal color */
  --signal-delta-soft: ...;   /* Soft tinted background */
  --signal-delta-border: ...; /* Signal border */

  /* Semantic Signal 4: Research Gap */
  --signal-gap: ...;          /* Solid signal color */
  --signal-gap-soft: ...;     /* Soft tinted background */
  --signal-gap-border: ...;   /* Signal border */

  /* Typography Families */
  --font-sans: 'Inter', system-ui, -apple-system, sans-serif;
  --font-serif: 'Newsreader', Georgia, serif;
  --font-mono: 'JetBrains Mono', ui-monospace, monospace;

  /* Radii & Shadows */
  --radius-card: 14px;
  --radius-pill: 9999px;
  --shadow-card: 0 1px 0 rgba(255,255,255,0.03) inset, 0 8px 24px rgba(0,0,0,0.35);
  --shadow-drawer: -24px 0 64px rgba(0,0,0,0.55);
}
```

### 1.2 Curated Theme Recommendations (Suggestions for Peace)

If Peace asks the agent for inspiration or recommendations, the agent can present these curated starting points:

#### Option A: "Dark Academic Observatory" (Calm, High-Contrast Slate)
- **Aesthetic:** Deep slate observatory with celestial accents. Ideal for reading dense academic literature.
- `--color-bg`: `#0B0F17` (Obsidian Slate)
- `--color-surface`: `#111827` (Deep Slate)
- `--color-surface-2`: `#1A2233`
- `--color-surface-3`: `#243049`
- `--color-line`: `#2B3752`
- `--color-ink`: `#E5E7EB` / `--color-ink-muted`: `#9CA3AF`
- `--color-accent`: `#60A5FA` (Sky Blue)
- Signals: `--signal-agree`: `#10B981` (Emerald), `--signal-contradict`: `#EF4444` (Crimson), `--signal-delta`: `#F59E0B` (Amber), `--signal-gap`: `#A78BFA` (Violet)

#### Option B: "Midnight Cyber-Academic" (Vivid High Contrast)
- **Aesthetic:** Jet black background with electric, razor-sharp signal colors.
- `--color-bg`: `#090A0F` (True Midnight)
- `--color-surface`: `#12141D`
- `--color-surface-2`: `#1B1E2B`
- `--color-line`: `#2E3447`
- `--color-ink`: `#FFFFFF` / `--color-ink-muted`: `#A0A6B8`
- `--color-accent`: `#38BDF8` (Electric Cyan)
- Signals: `--signal-agree`: `#00E676` (Neon Mint), `--signal-contradict`: `#FF3366` (Hot Coral), `--signal-delta`: `#FFB300` (Electric Amber), `--signal-gap`: `#B388FF` (Neon Amethyst)

#### Option C: "Warm Editorial Graphite" (Sophisticated Paper & Ink)
- **Aesthetic:** Warm dark graphite with literary warmth and muted, elegant jewel tones.
- `--color-bg`: `#121214` (Deep Warm Charcoal)
- `--color-surface`: `#1A1A1E`
- `--color-surface-2`: `#242429`
- `--color-line`: `#32323A`
- `--color-ink`: `#F4F4F5` / `--color-ink-muted`: `#A1A1AA`
- `--color-accent`: `#E2E8F0` (Frosted Platinum)
- Signals: `--signal-agree`: `#34D399` (Sage Green), `--signal-contradict`: `#F87171` (Warm Terracotta), `--signal-delta`: `#FBBF24` (Topaz), `--signal-gap`: `#C084FC` (Mauve Orchid)

*(Peace can pick any of these, mix and match, or design her own completely custom palette!)*

### 1.3 Paper Palette (`palette_index: 0..9`)

The backend attaches an integer `palette_index` (`0` to `9`) to each paper in `PaperMetadata`.
- In the frontend, map `palette_index` to an array of 10 distinct, desaturated accent colors for paper chips and graph node rings.
- **Rule of thumb:** Keep paper colors distinct from the 4 primary signal hues so users do not confuse a paper ring with a contradiction or agreement edge.
- **Multi-modal reminder:** Always render the paper's `short_label` (`P1`…`P10`) inside node rings or table chips so color is never the only identifier.

---

## 2. Typography

Peace is free to choose any font pairing that delivers clarity, readability, and a premium feel. Recommended defaults:

| Role | Suggested Fonts | Weight | Recommended Scale |
| :--- | :--- | :--- | :--- |
| **Page & Section Headings, Quote Text** | `Newsreader`, `Instrument Serif`, or `Playfair Display` | 500–600 | `h1` 36–42px, `h2` 26–30px, `h3` 18–22px |
| **UI Text, Tables, Buttons, Body** | `Inter`, `Roboto`, or system-ui | 400/500/600 | Body 14px / 22px, Small 12px / 18px |
| **Metrics, Badges, IDs, Page Numbers** | `JetBrains Mono` or `Fira Code` | 500 | 12–13px / 18px |

Include fonts via Google Fonts in `frontend/index.html`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,500;1,6..72,400&display=swap" rel="stylesheet">
```

---

## 3. Signal Rendering Rules (Colour is never the only cue)

Regardless of the color palette Peace chooses, every signal **must combine color + icon + text label + line style**:

| Signal | API Enum | Purpose | Suggested Icon | Text Label | Line / Node Style |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Consensus** | `AGREE` | Papers corroborate findings | Check (`✓`) | "Agree" | Solid line, 2px |
| **Contradiction** | `CONTRADICT` | Papers dispute claim/data | AlertTriangle (`⚠`) | "Contradiction" | Solid line, thick 3px |
| **Methodology Delta** | `METHODOLOGY_DELTA` | Discrepancy in setup/data | GitCompare (`≈`) | "Methodology difference" | Dashed line `[6, 4]`, 2px |
| **Research Gap** | `RESEARCH_GAP` | Unanswered question/void | Telescope (`🔭`) | "Research gap" | Dotted node outline |

Every signal badge must include the icon and text label. The Cytoscape contradiction graph legend must clearly display all four signals.

---

## 4. UI Architecture & Feature Blueprint (Vanilla HTML5 / CSS3 / ES6 JS)

```
┌─ Header: logo "Kairos" · tagline · Preset Selector · GitHub link · "Built with Llama" ──┐
├─ SyntheticBanner (only if fixture_provenance = SYNTHETIC_PLACEHOLDER) ─────────────────┤
├─ StatsStrip: papers · claims · pairs checked · pair reduction % · latency ─────────────┤
├─ Navigation Tabs: [ Comparison Matrix ] [ Contradiction Graph ] [ Consensus & Gaps ] ─┤
│   (default active tab: Comparison Matrix)                                              │
├─ Main Viewport: #view-matrix | #view-graph | #view-consensus                           │
├─ Slide-over Drawer: #drawer-evidence (Dispute / Claim inspection)                      │
└─ Footer: model + licence table · AI-assistance note · repo link ───────────────────────┘
```

Container max width 1280px, page padding 24px (16px under 640px). Section spacing 32px. Cards use rounded corners, subtle border, surface background, and soft shadow.

### 4.1 Sticky-Baseline Synthesis Matrix (6–8+ papers)

- **Orientation:** Rows are attributes; columns are papers. Attributes (in order): `Dataset`, `Sample size`, `Methodology`, `Primary metric`, `Limitations`, `Core conclusion`.
- **Columns:** Column 0 = attribute labels (sticky, `left: 0`, width 168px). The **pinned baseline paper** is rendered immediately after, also sticky (`left: 168px`). All remaining papers scroll horizontally, each `min-width: 280px`, `max-width: 320px`.
- **Pinning:** Each paper header has a pin button (`Pin` icon). Exactly one baseline at a time, default = `P1`. Pinning reorders columns client-side (baseline first, others in `short_label` order).
- **Relation-to-Baseline Row** (directly under header): Three counters per non-baseline paper derived from `edges` between that paper and the baseline — `✓ n` (agree), `⚠ n` (contradict), `≈ n` (methodology delta). Zero counts are dimmed.
- **Conflict Highlighting Toggle** ("Highlight conflicting methodologies", default ON): In `Methodology` and `Dataset` rows, cells of papers sharing a `METHODOLOGY_DELTA` edge with the baseline get soft delta background and left border. In `Core conclusion` row, cells sharing a `CONTRADICT` edge get soft contradiction background and left border.
- **Search / Filter Box:** Case-insensitive substring; non-matching cells dim to 35% opacity, matches wrap matched text in `<mark>`.
- **Density:** Cell text 13px/20px, clamp to 5 lines with a "Show more" toggle per cell.

### 4.2 Contradiction Network Graph (Cytoscape.js)

- **Canvas Container:** `#cy-container` rendered with Cytoscape.js, height `clamp(480px, 70vh, 760px)`.
- **Nodes = Claims:** Radius `6 + 2 * degree` (cap 16). Fill `var(--color-surface-2)`; ring = paper palette color (2.5px); paper `short_label` drawn inside nodes with radius ≥ 10, otherwise on hover. Research-gap nodes: hollow, dotted outline, telescope marker.
- **Labels:** Show claim `topic_hint` only on hover, selection, or zoom.
- **Edges:** Color/width/dash per Section 3. Opacity 0.9 normally, 0.15 when another node/edge is focused.
- **Filter Bar** (above canvas):
  1. **Cluster Pills:** One pill per `TopicCluster.label` with claim count; multi-select; "All" resets.
  2. **Paper Chips:** `P1…Pn`, toggle visibility of a paper's nodes.
  3. **Relation Toggles:** Agree, Contradict, Methodology, Gaps, each with signal icon.
  4. **"Isolate Contradictions" Switch:** Shows only `CONTRADICT` edges and their endpoint nodes.
  5. **Min Confidence Slider:** Default 0.50, step 0.05.
  6. **Live Counter:** "Showing {e} of {E} relations across {n} papers".
- **Interactions:** Hover edge → tooltip with relation + confidence; click edge → open Dispute Drawer; click node → focus neighbours (others dim); click background → clear focus; double-click background → zoom to fit.
- **Accessible Alternative:** Tabular edge list below canvas (real `<table>`) with the same filters applied. Keyboard users can access all dispute details without needing canvas interactions.
- **Legend** (bottom-left of canvas): The four signals with icon, label, and line sample.

### 4.3 Dispute Inspection Drawer (Slide-Over)

- Right-side slide-over panel, width `min(560px, 100vw)`, `role="dialog" aria-modal="true"`, focus trap, `Esc` closes, overlay click closes.
- **Header:** Relation badge (icon + label), confidence score as mono `0.93`, cosine similarity as mono `sim 0.91`, close button.
- **Body:**
  1. **Two Quote Cards:** Side by side (stacked under 640px). Each contains paper chip (`P2`), citation label, paper title (2-line clamp), verbatim quote (serif italic, left border in paper color), and mono badge `p. 7 · RESULTS`. Underneath each: claim `statement` and `metric_value` if present.
  2. **Referee Explanation Block:** Tinted with relation's soft background: heading "Why they differ" (or "Why they agree") and `explanation` text.
  3. **Context Comparison Row:** Each paper's `dataset`, `sample_size`, `methodology` in a compact two-column layout.
  4. **Actions:** "Copy citation block" (both quotes with page numbers) and Previous / Next dispute buttons (`←` / `→`).

### 4.4 Consensus & Gaps View

- **Consensus Score Ring:** Circular SVG gauge showing `consensus_score` (0–100) with color feedback. Formula tooltip from `02-api-contracts.md` §6.
- **Executive Summary Card:** Polished summary of paper corroborations and conflicts.
- **Two Columns:** "Where the papers agree" (check list) and "Top contradictions" (list with buttons opening the Dispute Drawer for that `edge_id`).
- **Research Gaps Panel:** Cards displaying statement, quote with `p. N · SECTION`, and `reason`.
- **Export Actions:** "Export Literature Review" button group for Markdown and LaTeX downloads.

### 4.5 Ingestion Hub & Presets (P2)

- Dropzone card with dashed border; drag-over state highlights border and background.
- Paper cards (one per file or arXiv ID): filename/id, size, remove button, status chip. Counter "6 of 10 papers (min 2)".
- arXiv input accepts bare IDs or URLs, validates client-side, and shows inline errors.
- **Pipeline Progress Stepper:** Seven labelled steps mapped to `PipelineStage`, progress bar from `progress_pct`, and latest `message`.

---

## 5. Responsive Behaviour

| Breakpoint | Behaviour |
| :--- | :--- |
| **≥ 1280px** | Full layout; matrix shows baseline + ~3 papers without horizontal scrolling. |
| **768–1279px** | Matrix scrolls horizontally; filter bar wraps gracefully to two rows. |
| **< 768px** | Tabs become a segmented control; drawer is full-screen; quote cards stack; graph height 55vh with edge-list-first layout. |

---

## 6. Motion & States

- Durations 150–220ms, `ease-out`. Skeleton shimmer for loading states; spinners only inside buttons.
- Respect `prefers-reduced-motion: reduce`: disable translate/scale animations and graph continuous force simulation after settling.
- Empty states: friendly serif headline + primary action ("Load a preset" / "Add papers").
- Error states: inline callout with API `message`, **Retry** button, and **Load demo preset instead** fallback button.

---

## 7. Content Rules & Attribution

- **Tone:** Precise, calm, academic. No hype words.
- **Footer Attribution:** Always show "Built with Llama" in the footer alongside the model/licence table (`models[]` from the result).
- **Synthetic Data Notice:** When `fixture_provenance = SYNTHETIC_PLACEHOLDER`, show persistent amber banner: **"Synthetic placeholder data — not real research."**
