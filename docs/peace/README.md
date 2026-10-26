# Frontend Execution Playbook — Peace

**Developer:** Oluwanifemi (Peace) (`Peaceyy28`, `oluwanifemipeace3@gmail.com`)
**Workspace:** `/frontend`, `/docs/peace` · **Stack:** Next.js 14 (App Router), TypeScript (strict), Tailwind CSS 3, `lucide-react`, `react-force-graph-2d`, `clsx`, `vitest`.

Agents: read `AGENTS.md` first, confirm you are working for **Peace**, then read `DESIGN.md` and `docs/shared/02-api-contracts.md`. Execute one milestone at a time. Peace has full creative authority over the visual design (see `DESIGN.md` §0); the four signal enums stay visually distinct.

**Mock-first rule:** P1–P4 build against fixtures in `/fixtures` (copied into `frontend/public/fixtures`). `fixtures/contract_sample.json` already exists (3 synthetic papers). DuroT's D1 adds 8/6/6-paper placeholder fixtures; if they are not merged yet, build with `contract_sample.json` and re-test with the larger ones when they land.

---

## Final frontend directory tree (target after P5)

```
frontend/
├── .env.example
├── .eslintrc.json
├── next.config.mjs
├── package.json
├── postcss.config.mjs
├── tailwind.config.ts                # tokens from DESIGN.md §1
├── tsconfig.json
├── vitest.config.ts
├── scripts/
│   ├── sync-fixtures.mjs             # copies ../fixtures/*.json → public/fixtures/
│   └── check-fixtures.mjs            # fails if copies differ from ../fixtures
├── public/
│   ├── fixtures/                     # COMMITTED copies (Vercel root dir = frontend)
│   └── favicon.svg
└── src/
    ├── app/
    │   ├── layout.tsx                # fonts, metadata, <html className="dark">
    │   ├── page.tsx                  # single-page app shell
    │   └── globals.css               # Tailwind layers + CSS variables
    ├── components/
    │   ├── layout/
    │   │   ├── Header.tsx
    │   │   └── Footer.tsx            # "Built with Llama", model/licence table
    │   ├── ui/
    │   │   ├── Badge.tsx             # SignalBadge, PageBadge, PaperChip
    │   │   ├── Button.tsx
    │   │   ├── Drawer.tsx            # focus trap, Esc, aria-modal
    │   │   ├── Skeleton.tsx
    │   │   ├── Tabs.tsx
    │   │   └── Toast.tsx
    │   ├── presets/PresetBar.tsx
    │   ├── ingest/
    │   │   ├── IngestionHub.tsx
    │   │   ├── Dropzone.tsx
    │   │   ├── PaperCard.tsx
    │   │   ├── ArxivInput.tsx
    │   │   └── PipelineProgress.tsx
    │   ├── results/
    │   │   ├── ResultsShell.tsx      # banner + stats strip + tabs
    │   │   ├── SyntheticBanner.tsx
    │   │   └── StatsStrip.tsx
    │   ├── matrix/
    │   │   ├── SynthesisMatrix.tsx
    │   │   ├── MatrixToolbar.tsx     # search, highlight toggle
    │   │   └── MatrixCell.tsx
    │   ├── graph/
    │   │   ├── ContradictionGraph.tsx
    │   │   ├── GraphFilterBar.tsx
    │   │   ├── GraphLegend.tsx
    │   │   ├── EdgeList.tsx
    │   │   └── DisputeDrawer.tsx
    │   └── consensus/
    │       ├── ConsensusSummary.tsx
    │       ├── ScoreRing.tsx
    │       ├── ResearchGapsPanel.tsx
    │       └── ExportButtons.tsx
    ├── hooks/
    │   ├── useAnalysis.ts            # preset/live state machine
    │   ├── useAnalysisStream.ts      # SSE with polling fallback
    │   ├── useGraphFilters.ts
    │   └── useMatrixState.ts
    └── lib/
        ├── types.ts                  # copied verbatim from contract §2
        ├── constants.ts              # palette, signal meta, limits
        ├── signals.ts                # relation → colour/icon/label
        ├── relations.ts              # baseline relation counts, edge indexing
        ├── graphData.ts              # filters → nodes/links
        ├── export.ts                 # Markdown + LaTeX builders
        ├── arxiv.ts                  # client-side id normalisation
        └── api/
            ├── client.ts             # KairosApiClient interface + factory
            ├── mockClient.ts
            └── liveClient.ts
```

## Environment variables (`frontend/.env.example`)

```ini
# "mock" = read fixtures from /public/fixtures only; "live" = call the backend
NEXT_PUBLIC_API_MODE=mock
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_REPO_URL=https://github.com/taiwodurotoluwa-svg/kairos
```

`package.json` scripts:

```json
{
  "scripts": {
    "predev": "node scripts/sync-fixtures.mjs",
    "dev": "next dev",
    "prebuild": "node scripts/sync-fixtures.mjs",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "sync:fixtures": "node scripts/sync-fixtures.mjs",
    "check:fixtures": "node scripts/check-fixtures.mjs"
  }
}
```

If `../fixtures` does not exist (Vercel root directory = `frontend`), `sync-fixtures.mjs` must **do nothing and exit 0** so the committed copies in `public/fixtures` are used.

---

## Milestone P1 — Scaffold, design system, API client, preset selector

**Branch:** `feat/p1-scaffold-design` · **Depends on:** none

### Steps
1. Scaffold in `/frontend` with `npx -y create-next-app@14 ./ --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm` (run `--help` first, non-interactive). Remove demo content.
2. Install: `lucide-react`, `clsx`, `react-force-graph-2d`; dev: `vitest`.
3. Apply tokens from `DESIGN.md` §1 to `tailwind.config.ts`; load fonts via `next/font/google` (DESIGN §2); set `<html lang="en" className="dark ...">` and `bg-bg text-ink`.
4. Copy `src/lib/types.ts` **verbatim** from contract §2.
5. `lib/constants.ts` (paper palette, limits 2–10) and `lib/signals.ts` (map every `SemanticSignal` → colour classes, icon, label, dash pattern per DESIGN §3).
6. API client (below). `mockClient` reads `/fixtures/{file}` using the same preset→file registry as the backend: `radiology → demo_radiology_8papers.json`, `llm_quantization → demo_llm_quantization_6papers.json`, `microgrids → demo_microgrids_6papers.json`, `contract_sample → contract_sample.json`. Presets list = those that load successfully.
7. `scripts/sync-fixtures.mjs` and `check-fixtures.mjs`; commit `public/fixtures/`.
8. Build `Header`, `Footer` (Built with Llama + model table from `models[]`), `PresetBar` (buttons with paper counts), `SyntheticBanner`, `Skeleton`, `Toast`, `Button`, `Badge` (SignalBadge, PageBadge, PaperChip).
9. `page.tsx`: header + preset bar + empty state + a minimal JSON "result stub" panel to prove loading works. Loading a preset shows skeleton then `StatsStrip`.
10. Add a `/styleguide` route listing every component state (signals, badges, buttons, skeletons, banner). Save 1440×900 screenshots to `docs/peace/screens/p1-*.png`.

### API client

```ts
// src/lib/api/client.ts
import type { AnalysisResult, DemoPresetSummary, JobCreated, JobState, ProgressEvent, ErrorBody } from "@/lib/types";

export interface AnalyzeInput { files: File[]; arxivIds: string[] }

export interface StreamHandlers {
  onProgress: (e: ProgressEvent) => void;
  onComplete: (e: ProgressEvent) => void;
  onFailed: (err: ErrorBody) => void;
}

export interface KairosApiClient {
  listPresets(): Promise<DemoPresetSummary[]>;
  getPreset(presetId: string): Promise<AnalysisResult>;
  startAnalysis(input: AnalyzeInput): Promise<JobCreated>;
  subscribe(analysisId: string, handlers: StreamHandlers): () => void; // returns unsubscribe
  getJob(analysisId: string): Promise<JobState>;
}

export function createApiClient(): KairosApiClient {
  const mode = process.env.NEXT_PUBLIC_API_MODE ?? "mock";
  return mode === "live" ? new LiveClient(process.env.NEXT_PUBLIC_API_BASE_URL!) : new MockClient();
}
```

### Acceptance criteria (P1)
- [ ] `npm run lint`, `typecheck`, `build` pass; `types.ts` byte-identical to the contract block.
- [ ] Tokens and fonts match `DESIGN.md` (or Peace's documented changes); all four signals visibly distinct; icons + labels present.
- [ ] Preset bar loads each fixture in mock mode and shows paper count; failure shows an error callout.
- [ ] Synthetic banner appears for `SYNTHETIC_PLACEHOLDER` data.
- [ ] `/styleguide` shows every component and state; screenshots saved.
- [ ] `check:fixtures` passes; `public/fixtures` committed.
- [ ] No horizontal page scroll at 390px width.

### Argon 4 checklist (P1)
Type parity with the contract, Tailwind token coverage, font loading performance, a11y of buttons and banner, mock/live switch correctness, hydration issues, bundle weight of `react-force-graph-2d` (must be dynamically imported later).

---

## Milestone P2 — Multi-paper ingestion hub

**Branch:** `feat/p2-ingestion-hub` · **Depends on:** P1

### Steps
1. `Dropzone`: drag-and-drop + click-to-browse for `.pdf` (`application/pdf`); client checks: type, size ≤ 20 MB, total ≤ 80 MB, count ≤ 10, no duplicates (name + size + lastModified).
2. `PaperCard` list with filename, size, remove button, status chip (`Ready`, `Uploading`, `Parsing…`, `Error`); counter "{n} of 10 papers (min 2)".
3. `ArxivInput`: accepts bare ids or URLs, normalises with `lib/arxiv.ts` (formats: `2401.01234`, `2401.01234v2`, `arxiv.org/abs/…`, `arxiv.org/pdf/…(.pdf)`, `cs.CL/0501001`), de-duplicates, inline validation errors mirroring backend `INVALID_ARXIV_ID`.
4. `Analyze` button disabled until `2 ≤ total ≤ 10`; helper text explains why.
5. `PipelineProgress`: seven-step stepper mapped to `PipelineStage` with `progress_pct` bar and latest `message`; in mock mode a **simulated** progress run (clearly labelled "demo simulation") resolves with a preset so the flow is demonstrable without a backend.
6. `useAnalysis` state machine: `idle → ready → submitting → streaming → complete | failed`. Failure shows API `message` + **Retry** + **Load demo preset instead**.
7. Unit tests (`vitest`) for `lib/arxiv.ts` normalisation and file validation helpers.

### Acceptance criteria (P2)
- [ ] 2–10 PDFs can be added by drag-drop or browse; invalid files rejected with specific messages; limits enforced.
- [ ] arXiv ids/URLs normalise exactly like the backend rules; duplicates collapsed.
- [ ] Analyze button state correct at 0, 1, 2, 10, 11 papers.
- [ ] Progress stepper reflects each stage in order; failure state offers Retry and preset fallback.
- [ ] Keyboard: dropzone reachable and operable; remove buttons labelled; errors announced via `aria-live`.
- [ ] `lint`, `typecheck`, `test`, `build` pass; screenshots saved.

### Argon 4 checklist (P2)
File-handling memory, drag-over edge cases, duplicate detection, a11y of dropzone, state-machine dead ends, double-submit protection, regex correctness for arXiv ids.

---

## Milestone P3 — Pinned-baseline synthesis matrix (6–8+ papers)

**Branch:** `feat/p3-synthesis-matrix` · **Depends on:** P1 (use the 8-paper fixture when available)

### Steps
1. `lib/relations.ts` (pure, unit-tested):

```ts
import type { ClaimComparisonEdge, RelationType } from "@/lib/types";

export interface RelationCounts { AGREE: number; CONTRADICT: number; METHODOLOGY_DELTA: number }

/** Counts edges that connect `paperId` with the baseline paper. */
export function countRelationsToBaseline(
  edges: ClaimComparisonEdge[], baselineId: string, paperId: string
): RelationCounts {
  const out: RelationCounts = { AGREE: 0, CONTRADICT: 0, METHODOLOGY_DELTA: 0 };
  for (const e of edges) {
    const a = e.source.paper_id, b = e.target.paper_id;
    if ((a === baselineId && b === paperId) || (a === paperId && b === baselineId)) out[e.relation as RelationType]++;
  }
  return out;
}
```
2. `SynthesisMatrix` per DESIGN §4.1: attribute rows × paper columns; sticky attribute column + sticky pinned baseline; pin button per header (one baseline, default `P1`); horizontal scroll for the rest.
3. Relation-to-baseline row with ✓ / ⚠ / ≈ counters (dim zeros).
4. Conflict highlighting toggle (default ON): amber on `Methodology` and `Dataset` rows for papers with a `METHODOLOGY_DELTA` edge to the baseline; crimson on `Core conclusion` for papers with a `CONTRADICT` edge to the baseline.
5. Search box with `<mark>` highlighting and dimming; "Show more/less" for cells over 5 lines.
6. Responsive per DESIGN §5; sticky shadow cue when scrolled.
7. `useMatrixState` hook (baseline id, search, toggle). Tests for `countRelationsToBaseline` and highlight rules.
8. Wire into `ResultsShell` (tabs; matrix is the default tab).

### Acceptance criteria (P3)
- [ ] 8-paper fixture renders; baseline and attribute columns stay visible while scrolling horizontally.
- [ ] Pinning any paper re-orders columns and recomputes counters/highlights.
- [ ] Highlight rules match the spec exactly; toggle works; zero-count dimming works.
- [ ] Search highlights and dims correctly; clearing restores.
- [ ] Table is a semantic `<table>` with `scope` attributes; pin buttons labelled "Pin {citation_label} as baseline".
- [ ] Works at 1440px, 1024px, 390px (no layout break, scroll hint visible).
- [ ] `lint`, `typecheck`, `test`, `build` pass; screenshots (1440×900 and 390×844) saved.

### Argon 4 checklist (P3)
Sticky positioning + z-index bugs, performance with 10 columns, highlight logic correctness, long-text overflow, a11y semantics, regex-escaping in search (must treat input as literal text).

---

## Milestone P4 — Contradiction graph, cluster filters, dispute drawer

**Branch:** `feat/p4-graph-dispute` · **Depends on:** P3

### Steps
1. `lib/graphData.ts` (pure, unit-tested): `buildGraph(result, filters) -> { nodes, links }` implementing all filters from DESIGN §4.2 (clusters, papers, relations, isolate contradictions, min confidence, gaps toggle). Isolate mode shows only `CONTRADICT` edges and their endpoint nodes.
2. `useGraphFilters` hook (state + derived counts "Showing e of E relations across n papers").
3. `ContradictionGraph` with `next/dynamic(() => import("react-force-graph-2d"), { ssr: false })`; node and link rendering per DESIGN (ring colour = paper palette, `P#` label inside, gap nodes hollow with dotted violet outline; edge colour/width/dash per signal; `linkHoverPrecision={8}`; labels only on hover/selection/zoom ≥ 1.8; `cooldownTicks={120}`; fit to view on first load).
4. `GraphFilterBar`: cluster pills (multi-select + All), paper chips, relation toggles, **Isolate contradictions** switch, min-confidence slider (default 0.50).
5. `GraphLegend` with all four signals.
6. `EdgeList` table with the same filters; each row opens the drawer (keyboard-accessible alternative).
7. `DisputeDrawer` per DESIGN §4.3 (two quote cards, explanation block, context table, copy-citation, prev/next, `←`/`→`, focus trap, `Esc`).
8. Node click → focus neighbours; background click → clear focus.
9. Tests: `buildGraph` for each filter and combination; drawer open/close and focus-restore helper logic.

### Acceptance criteria (P4)
- [ ] 6- and 8-paper fixtures render without clutter: labels hidden by default, filters work, "Isolate contradictions" leaves only red edges and their nodes.
- [ ] Edge colours/dash patterns/icons match the four-signal spec; legend present; colour is never the only cue.
- [ ] Clicking any edge (graph or list) opens the drawer with both quotes, `p. N · SECTION` badges, relation, confidence, similarity and explanation.
- [ ] Prev/Next and arrow keys cycle through the *currently filtered* edges; `Esc` closes; focus returns to the trigger; focus is trapped while open.
- [ ] Cluster pill counts correct; "Showing e of E" accurate.
- [ ] Reduced-motion respected; simulation stops after cooldown.
- [ ] Mobile layout (390px): drawer full-screen, edge list shown above canvas.
- [ ] `lint`, `typecheck`, `test`, `build` pass; screenshots saved.

### Argon 4 checklist (P4)
Canvas performance and memory (re-creating data objects each render), hit-testing reliability for thin edges, SSR/hydration with dynamic import, focus-trap correctness, filter-state coherence, a11y of the graph alternative, handling of 0 edges and 0 clusters.

---

## Milestone P5 — Consensus, gaps, export, live integration, deploy

**Branch:** `feat/p5-consensus-integration` · **Depends on:** P4, D5 (preset-only mode is acceptable if D5 slips)

### Steps
1. `ConsensusSummary` per DESIGN §4.4: `ScoreRing` (colour thresholds), executive summary, agreed findings, top contradictions (each opens the drawer for its `edge_id`), recommended next steps.
2. `ResearchGapsPanel`: violet cards (statement, quote + `p. N · SECTION`, reason), first 6 with "Show all".
3. `lib/export.ts` + `ExportButtons` (templates below), unit-tested including LaTeX escaping.
4. `liveClient.ts`: `POST /analyze` (multipart: repeated `files`, `arxiv_ids` JSON string), SSE via `EventSource` on `events_url` with event names `progress` / `complete` / `failed`, **polling fallback** (`GET /analyze/{id}` every 1.5 s) if SSE errors; parse `ErrorResponse` for failures.
5. Automatic **preset fallback**: if live start fails with a network error or `LLM_PROVIDER_UNAVAILABLE`, show a toast + **Load demo preset** CTA; presets always load from `public/fixtures` when the backend is unreachable.
6. Polish: skeletons, empty/error states, favicon, `<title>` and meta description, Open Graph tags, footer licence table, keyboard pass, Lighthouse accessibility ≥ 90.
7. Deploy to Vercel (root directory `frontend`, env `NEXT_PUBLIC_API_MODE=live`, `NEXT_PUBLIC_API_BASE_URL=<backend URL>`); verify a live preset and a live upload on the deployed site; record the URL in `docs/requests.md`.
8. Write `frontend/README.md` (setup, env, scripts, structure, deploy).

### Export templates (exact)

**Markdown (`kairos-literature-review.md`):**

```markdown
# Literature synthesis — {preset title or "Uploaded papers"}
_Generated by Kairos on {YYYY-MM-DD}. Models: {EXTRACTION model_id}, {EMBEDDING model_id}, {REFEREE model_id}. Data: {fixture_provenance}._

## Executive summary
{consensus.executive_summary}

**Consensus score:** {consensus_score}/100

## Papers
| Label | Citation | Title | Dataset | Methodology | Primary metric |
| - | - | - | - | - | - |
{one row per paper}

## Points of agreement
{each agreed_finding as "- text"}

## Contradictions
{for each top_contradictions entry: "### {headline}" then, for its edge:
- **{source citation_label}** (p. {source.page_number}, {source.section}): "{source.verbatim_quote}"
- **{target citation_label}** (p. {target.page_number}, {target.section}): "{target.verbatim_quote}"
- _Why they differ:_ {explanation}}

## Methodology differences
{for each METHODOLOGY_DELTA edge, same bullet block as above}

## Research gaps
{for each gap: "- **{paper citation_label}** (p. N): {statement} — _{reason}_"}

## Recommended next steps
{numbered list}

## Models and licences
{one line per models[] entry: role — model_id — licence}
Built with Llama.
```

**LaTeX (`kairos-literature-review.tex`):** `\documentclass{article}`, `\usepackage[utf8]{inputenc}`, `\usepackage{hyperref}`, `\usepackage{longtable}`; `\section{Executive summary}`, `\section{Papers}` (a `longtable`), `\section{Points of agreement}` (`itemize`), `\section{Contradictions}`, `\section{Methodology differences}`, `\section{Research gaps}`, `\section{Recommended next steps}` (`enumerate`), and a closing line "Built with Llama." Quotes are placed in `\begin{quote}…\end{quote}` with `(p.~N, SECTION)`. **`escapeLatex` must escape** `\ { } $ & # ^ _ % ~` (backslash → `\textbackslash{}`, `^` → `\textasciicircum{}`, `~` → `\textasciitilde{}`). Downloads use `Blob` + a temporary `<a download>`.

### Acceptance criteria (P5)
- [ ] Consensus tab shows score ring, summary, agreements, contradictions (each opens the drawer), gaps and next steps.
- [ ] Markdown and LaTeX exports match the templates; LaTeX special characters are escaped (unit tests); exported files include licence disclosure.
- [ ] Live mode: upload 3 PDFs → SSE progress → result renders in all three tabs; polling fallback works when SSE is blocked (tested by disabling `EventSource`).
- [ ] Backend outage: preset fallback appears; presets load offline.
- [ ] Real presets (`REAL_PIPELINE_OUTPUT`) show no synthetic banner; placeholder data still does.
- [ ] Deployed Vercel URL works end-to-end; URL recorded; CORS verified.
- [ ] Lighthouse accessibility ≥ 90; no console errors; `lint`, `typecheck`, `test`, `build` pass; screenshots at 1440×900 and 390×844 saved for all tabs.

### Argon 4 checklist (P5)
SSE reconnection and cleanup (memory leaks), export correctness (escaping, encoding), error-state coverage, env handling on Vercel, CORS failures, a11y score evidence, demo-day failure drills (offline, slow provider, empty result).

---

## Demo-day UI checklist (Peace)
- [ ] Presets load instantly with network disabled.
- [ ] Baseline pin, a red edge and the dispute drawer can be shown within 60 seconds.
- [ ] Live upload shows a readable progress stepper.
- [ ] Footer shows "Built with Llama" and the model/licence table.
- [ ] No synthetic banner on any Demo Day preset.

## Parking lot
(Agents: record out-of-scope ideas here and in `docs/requests.md`; do not implement them.)
