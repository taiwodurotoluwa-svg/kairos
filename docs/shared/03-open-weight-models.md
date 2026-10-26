# 03 — Open-Weight Model Strategy

Everything the models do in Kairos, with exact ids, licences, prompts and known limits. **Runtime code may only call the models in this file.**

## 1. Provider fallback chain

`LLM_PROVIDER_CHAIN=groq,huggingface,ollama` (comma separated, tried in order). All three expose an **OpenAI-compatible** chat-completions API, so one client class (the `openai` Python SDK with a custom `base_url`) serves them all. This is only a transport choice: the models are open-weight.

| Order | Provider | Base URL (env) | Key env | Model env (default) |
| :--- | :--- | :--- | :--- | :--- |
| 1 | Groq | `GROQ_BASE_URL=https://api.groq.com/openai/v1` | `GROQ_API_KEY` | `GROQ_MODEL=llama-3.1-8b-instant` |
| 2 | Hugging Face Inference | `HF_BASE_URL=https://router.huggingface.co/v1` | `HF_TOKEN` | `HF_MODEL=meta-llama/Llama-3.1-8B-Instruct` |
| 3 | Local Ollama | `OLLAMA_BASE_URL=http://localhost:11434/v1` | none (any string, e.g. `ollama`) | `OLLAMA_MODEL=llama3.2:3b` |

A provider is **skipped** when its key env is empty (Groq, HF) or when it is unreachable (Ollama). Fail-over triggers: HTTP 429 (after honouring `Retry-After` once), HTTP ≥ 500, timeout, connection error, or invalid JSON after the corrective retry. HTTP 401/403 disables that provider for the process lifetime and logs a clear error (never the key).

**Request parameters**

| Stage | `temperature` | `max_tokens` | `response_format` |
| :--- | :--- | :--- | :--- |
| 1 Extraction | 0.1 | 1800 | `{"type":"json_object"}` |
| 3 Referee | 0.0 | 900 | `{"type":"json_object"}` |
| 4 Consensus | 0.3 | 700 | `{"type":"json_object"}` |

If a provider rejects `response_format`, retry once without it (the prompts already demand JSON-only output) and rely on the JSON parser and Pydantic validation.

## 2. Model registry and licence compliance

| Role | Model id | Params | Licence | Licence URL |
| :--- | :--- | :--- | :--- | :--- |
| Primary LLM | `meta-llama/Llama-3.1-8B-Instruct` | 8B | Llama 3.1 Community License | https://www.llama.com/llama3_1/license/ |
| Alternative LLM | `Qwen/Qwen2.5-7B-Instruct` | 7B | Apache-2.0 | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct |
| Offline fallback LLM | `meta-llama/Llama-3.2-3B-Instruct` | 3B | Llama 3.2 Community License | https://www.llama.com/llama3_2/license/ |
| Embeddings | `BAAI/bge-small-en-v1.5` | 33M, 384-d | MIT | https://huggingface.co/BAAI/bge-small-en-v1.5 |

**Obligations we meet:**
1. Show **"Built with Llama"** in the UI footer and README (Llama licences require attribution when distributing a product built on them).
2. Include the licence names and links in the in-app model table (`AnalysisResult.models[]`) and README.
3. We **do not redistribute model weights**. Weights are fetched by providers or by the user's own Ollama/FastEmbed install.
4. Meta models on Hugging Face are gated: the person using an HF token must have accepted the licence on the model page.
5. Follow each licence's acceptable-use policy. Kairos only analyses documents the user supplies.
6. "Open weights" ≠ "open source": the README says so explicitly.

## 3. Stage 1 — Structured extraction

### 3.1 System prompt (use verbatim)

```
You are a meticulous scientific information extraction engine. You read excerpts from ONE academic paper and return a single JSON object. You never chat, never explain, and never use markdown.

HARD RULES
1. Output ONLY one JSON object that matches the SCHEMA below. No code fences, no commentary.
2. Use ONLY information present in the PAPER TEXT. If a field is not stated, use the string "Not reported" (or null where the schema allows null). Never guess and never use outside knowledge.
3. Every claim MUST include "verbatim_quote": an EXACT contiguous substring copied character-for-character from the PAPER TEXT, between 10 and 400 characters. Do not paraphrase, correct typos, merge sentences, or add ellipses. Never include [[PAGE n]] or [[SECTION: X]] markers inside a quote.
4. "page_number" is the integer n of the nearest preceding [[PAGE n]] marker before the quote.
5. "section" is the name in the nearest preceding [[SECTION: NAME]] marker and must be one of: ABSTRACT, METHODOLOGY, EXPERIMENTAL_SETUP, RESULTS, DISCUSSION, CONCLUSION, LIMITATIONS, OTHER.
6. Extract between 4 and 6 atomic claims. Prefer claims that contain numbers, comparisons, named datasets or models, or explicit recommendations. Each "statement" must be a single self-contained sentence of at most 280 characters that names its subject (no bare "it", "this method", "our model").
7. Include at least one claim of type CONCLUSION. If the paper states limitations, include one claim of type LIMITATION.
8. "claim_type" is one of: EMPIRICAL_RESULT, METHOD, LIMITATION, CONCLUSION.
9. "topic_hint" is a 2-6 word noun phrase naming what the claim is about (e.g. "long-context accuracy"). Claims about the same question in different papers should use similar wording.
10. "year" is the 4-digit publication year if printed in the text, otherwise null.

SCHEMA
{
  "title": string,
  "authors": [string],
  "year": integer | null,
  "dataset": string,
  "sample_size": string | null,
  "methodology": string,
  "primary_metric": string,
  "limitations": string,
  "core_conclusion": string,
  "claims": [
    {
      "claim_type": "EMPIRICAL_RESULT" | "METHOD" | "LIMITATION" | "CONCLUSION",
      "topic_hint": string,
      "statement": string,
      "metric_value": string | null,
      "section": "ABSTRACT" | "METHODOLOGY" | "EXPERIMENTAL_SETUP" | "RESULTS" | "DISCUSSION" | "CONCLUSION" | "LIMITATIONS" | "OTHER",
      "page_number": integer,
      "verbatim_quote": string
    }
  ]
}
```

### 3.2 User prompt template

```
PAPER FILENAME: {filename}
PAPER TEXT (sectioned, with page markers):
<<<
{sectioned_text}
>>>
Return the JSON object now.
```

### 3.3 Corrective retry (appended as a second user message when parsing/validation fails)

```
Your previous reply was rejected: {error_message}.
Reply again with ONLY the corrected JSON object that satisfies the schema. Do not apologise or explain.
```

### 3.4 After the call
Backend maps the model's flat claim fields into `ExtractedClaim` + `Provenance` (adding `paper_id`, `paper_title`, ids), then runs the quote verifier (§6). The `Provenance.paper_title` is the extracted `title`.

## 4. Stage 2 — Embeddings (`BAAI/bge-small-en-v1.5`)

- **Backend:** `EMBEDDING_BACKEND=fastembed` (default; ONNX, no PyTorch, CPU-friendly). Alternative: `hf_api` (Hugging Face Inference feature-extraction endpoint) when the host cannot run ONNX.
- **Input text per claim:** `"{topic_hint}: {statement}"` (no instruction prefix is used because both sides of every comparison are symmetric claim texts).
- **Post-processing:** L2-normalise every vector, so cosine similarity = dot product.
- **Preload** the model at application startup (and bake it into the Docker image) so the first request is not delayed.

### 4.1 Threshold tuning procedure (done in D4, results recorded here)

BGE similarity scores are compressed into a high range, so a default cannot be trusted blindly.
1. Build `backend/tests/data/tuning_pairs.json`: at least 30 claim pairs written/selected by the humans from real papers, each labelled `related` or `unrelated`.
2. Run `python backend/scripts/tune_threshold.py` to print precision/recall for thresholds 0.50–0.85 in 0.05 steps.
3. Choose the highest threshold with recall ≥ 0.85 on `related` pairs. Update `SIMILARITY_THRESHOLD` default and fill in this table:

| Date | Pairs | Chosen threshold | Precision | Recall | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| _(D4 fills this in)_ | | | | | |

Until then the working default is **0.65**.

## 5. Stage 3 — Strict NLI referee

### 5.1 System prompt (use verbatim)

```
You are a rigorous academic referee performing Natural Language Inference between pairs of research claims taken from different papers. For each pair, decide how the two papers relate. You never chat and never use markdown. Output ONLY one JSON object.

LABELS
- AGREE: Under comparable conditions, both claims support the same finding or point in the same direction.
- CONTRADICT: The claims make incompatible assertions about the SAME question under COMPARABLE conditions (same task, population, dataset type and setting), so both cannot be true at once.
- METHODOLOGY_DELTA: The results or conclusions differ, but the difference is plausibly explained by different datasets, sample sizes, models, hardware, metrics, time horizons or boundary conditions that are visible in the claims or the paper context. This is NOT a true conflict.
- UNRELATED: The claims address different questions or variables.

DECISION RULES
1. If both statements could be true at the same time, the label is NOT CONTRADICT.
2. If the conditions differ in a way that explains the difference, choose METHODOLOGY_DELTA, not CONTRADICT.
3. Use only the information given. Do not use outside knowledge about the papers.
4. Judge each pair independently.

CONFIDENCE
A number from 0.0 to 1.0: 0.9+ means the quotes alone make the label unambiguous; 0.7-0.89 means likely; below 0.7 means uncertain.

EXPLANATION
One or two sentences, at most 60 words. Name BOTH papers using their citation labels. State the deciding factor (for example, benchmark, context length, sample size, dataset cleanliness, or opposite recommendations). Do not quote more than 10 words.

OUTPUT SCHEMA
{"results":[{"pair_id": string, "relation": "AGREE"|"CONTRADICT"|"METHODOLOGY_DELTA"|"UNRELATED", "confidence": number, "explanation": string}]}
The "results" array MUST contain exactly one entry per input pair, using the same "pair_id".
```

### 5.2 User prompt template

```
Evaluate each of the following pairs.

PAIRS (JSON):
{pairs_json}

Return the JSON object now.
```

`pairs_json` is a JSON array of:

```json
{
  "pair_id": "e-p1c2-p2c2",
  "paper_a": {"citation_label": "Example A (2024)", "dataset": "...", "methodology": "..."},
  "claim_a": {"statement": "...", "verbatim_quote": "..."},
  "paper_b": {"citation_label": "Example B (2025)", "dataset": "...", "methodology": "..."},
  "claim_b": {"statement": "...", "verbatim_quote": "..."}
}
```

### 5.3 Validation and post-processing
- `relation` must be one of the four labels; `UNRELATED` pairs are dropped.
- `confidence` is clamped to [0, 1]; non-numeric → retry that pair alone.
- `explanation` truncated to 500 chars (contract limit).
- Pairs missing from `results` are retried once individually.
- `cosine_similarity` is copied from the similarity matrix (not from the model).

### 5.4 Stage 4 — Consensus writer (system prompt, verbatim)

```
You write the executive summary of a multi-paper literature comparison. You are given structured data only: paper metadata, verified relations between claims (with ids), and research gaps. You never chat and never use markdown. Output ONLY one JSON object.

RULES
1. Use ONLY the supplied data. Do not add facts, numbers or papers that are not present.
2. Refer to papers by their citation labels.
3. "executive_summary": at most 120 words, neutral academic tone, covering overall agreement, the main contradictions, and notable gaps.
4. "agreed_findings": up to 5 short bullet strings, each supported by at least one AGREE edge.
5. "top_contradictions": up to 3 objects {"edge_id", "headline"} using ONLY edge_ids with relation CONTRADICT from the input; "headline" is one question-style sentence of at most 25 words. If there are no CONTRADICT edges return an empty list.
6. "recommended_next_steps": 2 to 4 concrete suggestions that follow from the contradictions, methodology differences and gaps.

OUTPUT SCHEMA
{"executive_summary": string, "agreed_findings": [string], "top_contradictions": [{"edge_id": string, "headline": string}], "recommended_next_steps": [string]}
```

User message: a JSON object `{"papers": [...citation_label,title,dataset,methodology,primary_metric], "edges": [...edge_id,relation,confidence,explanation,source_claim,target_claim], "gaps": [...gap_id,paper,statement]}`.

## 6. Quote verification (anti-hallucination, mandatory)

Applies to every claim from Stage 1, before embedding.

1. **Normalise** both quote and page text with the same function: Unicode NFKC, map curly quotes/dashes to ASCII, collapse all whitespace to single spaces, `casefold()`. While normalising, keep an `index_map` from each normalised character back to the index in the original page text.
2. **Exact pass:** search the normalised quote in the normalised text of the claimed page, then the pages ±1, then outward by distance.
3. **Fuzzy pass:** if no exact match, use `rapidfuzz.fuzz.partial_ratio_alignment`; accept the best alignment with score ≥ **92**.
4. On success, **replace the stored quote with the true substring** of the original page text (via `index_map`) and **correct `page_number`** to the page where it was found. The stored quote is therefore guaranteed verbatim.
5. Reject (drop the claim) if no match, if the final quote is shorter than 10 or longer than 600 characters, or if it contains `[[PAGE` / `[[SECTION`.
6. Record counts (`proposed`, `kept`, `dropped`) per paper. If `kept < 2`, add a warning; if `kept == 0`, exclude the paper.

## 7. Known limitations (shown to users and judges)

- **Small models err.** An 8B (or 3B) model can mislabel relations or miss nuance. Mitigations: strict prompts, `temperature` 0–0.1, verbatim quotes shown next to every verdict, confidence scores, and `METHODOLOGY_DELTA` to avoid false contradictions.
- **Quote verification proves a quote exists, not that the claim is correct or that the paper is right.**
- **Layout loss:** tables, figures, equations and footnotes are not parsed; two-column PDFs can reorder text; scanned PDFs are rejected.
- **Language:** English only (the embedding model is English-specific).
- **Truncation:** only a character budget of each paper is read (`MAX_PAPER_CHARS`), so claims in omitted text are not found.
- **Threshold sensitivity:** the similarity threshold trades recall (missed comparisons) against cost.
- **Consensus score** is a simple ratio of edge types, not a meta-analysis.
- **Provider limits:** free tiers are rate limited; response times vary.
- **Licences:** Llama terms apply (attribution, acceptable use). Open weights are not necessarily open source.

## 8. Model-id verification checklist (start of D3, and again before submission)

Provider catalogues change. Before relying on defaults:
1. Open the Groq models page and confirm `llama-3.1-8b-instant` is available; note its free-tier rate limits.
2. Confirm `meta-llama/Llama-3.1-8B-Instruct` is served by the Hugging Face router for your account (and that the licence is accepted).
3. Run `ollama pull llama3.2:3b`.
4. If a default id has changed, update `.env.example`, this file's §1 table and `AnalysisResult.models` generation in the same PR, **keeping the model open-weight**. Choose `Qwen/Qwen2.5-7B-Instruct` (Apache-2.0) as the first substitute.
5. Record the verified date and provider limits in `docs/requests.md` (row type `INFO`).
