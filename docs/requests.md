# Cross-Developer Requests and Contract Change Log

Use this file for **anything one developer needs from the other**, and for every contract change. Agents never edit the other developer's workspace; they add a row here and tell their human.

## How to use
1. Add a new row at the **bottom** of the table. IDs are sequential: `REQ-001`, `REQ-002`, ...
2. `Type`: `CONTRACT` (shape/enum/endpoint change), `FIXTURE`, `ENV`, `BUG`, `INFO`, `DEPLOY`.
3. `Status`: `OPEN` → `ACKNOWLEDGED` → `DONE` or `REJECTED` (with reason in `Resolution`).
4. **A `CONTRACT` change is only `DONE` when** both humans approved, `docs/shared/02-api-contracts.md` and both `schemas.py` and `types.ts` are updated, `schema_version` is bumped and `test_contract.py` passes.
5. Keep entries short, concrete and dated (WAT).

## Log

| ID | Date (WAT) | From → To | Type | Request | Status | Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| REQ-001 | 2026-10-26 | DuroT → Peace | CONTRACT | Contract `1.0.0` is published in `docs/shared/02-api-contracts.md`. Please review field names, enums and the four semantic signals before P1 finishes. | OPEN | |
| REQ-002 | 2026-10-26 | DuroT → Peace | FIXTURE | `fixtures/contract_sample.json` (3 synthetic papers) is available now so you can start P1 immediately. Larger 8/6/6-paper placeholder fixtures arrive with D1. | DONE | Committed with the documentation set. |
| REQ-003 | 2026-10-26 | Peace → DuroT | FIXTURE | P3 needs the **8-paper** placeholder fixture early (spec: ≥ 2 edges of each relation, ≥ 2 gaps, cross-references valid). Please merge D1 fixtures first and notify here. | OPEN | |
| REQ-004 | 2026-10-26 | DuroT → Peace | INFO | Every fixture has `fixture_provenance`. Show a persistent banner for `SYNTHETIC_PLACEHOLDER`. Demo Day presets will be `REAL_PIPELINE_OUTPUT` only. | OPEN | |
| REQ-005 | 2026-10-26 | Peace → DuroT | ENV | `public/fixtures` holds committed copies of `/fixtures/*.json` (Vercel root = `frontend`). When you change a fixture, tell me so I run `npm run sync:fixtures` and commit; `check:fixtures` will fail otherwise. | OPEN | |
| REQ-006 | 2026-10-26 | Peace → DuroT | DEPLOY | Once the backend is deployed (D5), post the base URL here and add the Vercel origin to `CORS_ALLOW_ORIGINS`. | OPEN | |
| REQ-007 | 2026-10-26 | DuroT → Peace | CONTRACT | Analysis uses `POST /analyze` (202 + `analysis_id`) → SSE `GET /analyze/{id}/events` (`progress`/`complete`/`failed`) → `GET /analyze/{id}`. If SSE is blocked, poll `GET /analyze/{id}` every 1.5 s. | OPEN | |
| REQ-008 | 2026-10-26 | DuroT ↔ Peace | INFO | Both of us choose the 3 demo topics and the real, openly licensed papers for each (D5 step 7). Draft `fixtures/presets_manifest.json` together by Wed 28 Oct. Do **not** invent arXiv ids. | OPEN | |
| REQ-009 | 2026-10-27 | Peace ↔ DuroT | ARCH | Frontend stack simplified from Next.js/Tailwind to Vanilla HTML5, CSS3, ES6 JavaScript, and Cytoscape.js (CDN). Eliminates Node build overhead and allows direct Live Server execution. | DONE | Docs, playbooks and prompts updated across repo. |
| REQ-010 | 2026-10-27 | DuroT ↔ Peace | WORKFLOW | Milestone review bundles are local `.txt` files (`reviews/{ID}_review.txt`) for Google AI Studio (Argon 4). Never commit or push review files to GitHub. | DONE | Added to `.gitignore`; untracked from git; playbooks updated. |
| REQ-011 | 2026-10-28 | Peace → DuroT | INFO | `README.md` lines 82 & 97–111 still reference `npm install` and `npm run dev` on port 3000 instead of Vanilla HTML5/CSS3/ES6 (`python -m http.server 5500 --directory frontend` or VS Code Live Server on port 5500) per `REQ-009`. Also note for Demo Day: root `/fixtures/*.json` and `frontend/fixtures/*.json` are currently `SYNTHETIC_PLACEHOLDER`; when baking `REAL_PIPELINE_OUTPUT` from `fixtures/presets_manifest.json`, please mirror updated files to `frontend/fixtures/`. | OPEN | |

## Request template (copy a row)

```markdown
| REQ-0NN | YYYY-MM-DD | From → To | TYPE | What exactly you need and why it blocks you | OPEN | |
```
