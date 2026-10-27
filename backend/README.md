# Kairos Backend Engine

FastAPI backend engine for **Kairos** — Multi-Paper Literature Synthesis & Contradiction Mapping Engine. Built for the OPEN//BUILD Hackathon 2026.

Kairos synthesizes 2–10 scientific research papers (via direct PDF uploads or arXiv IDs), extracts empirical claims with verbatim text provenance, maps research gaps, resolves semantic contradictions with open-weight Natural Language Inference (NLI), and streams real-time progress via Server-Sent Events (SSE).

> **Built with Llama**  
> Runtime language models: `meta-llama/Llama-3.1-8B-Instruct` (primary), `meta-llama/Llama-3.2-3B-Instruct` (fallback), and `Qwen/Qwen2.5-7B-Instruct` (alternative). Runtime embeddings: `BAAI/bge-small-en-v1.5` (33M parameters, 384-dimensional dense vectors). **Zero closed models are invoked in runtime application code.**

---

## Architecture Overview

The backend executes a 5-stage synthesis pipeline:

1. **Stage 0: Ingestion & Parsing (`/api/v1/analyze`)**
   - Concurrently parses PDFs using PyMuPDF (`fitz`) and fetches arXiv papers with graceful failure isolation.
   - Computes SHA-256 digests to eliminate duplicates across upload and arXiv streams.
   - Injects section markers (`[[SECTION: X]]`) and page indicators (`[[PAGE n]]`).
2. **Stage 1: LLM Claim Extraction & Quote Verification**
   - Extracts 3–7 structured findings, methodologies, and limitations per paper.
   - Enforces the **Quote Verifier Anti-Hallucination Filter**: extracts must contain a 10–400 character verbatim substring from the source text, normalized with Unicode NFKC and RapidFuzz partial ratio alignment. Hallucinated or drifting quotes are discarded.
3. **Stage 2: Embeddings, Cosine Matrix, Research Gaps & Clustering**
   - Embeds claim texts using `BAAI/bge-small-en-v1.5` via FastEmbed ONNX runtime.
   - Vectorized cosine similarity matrix with strict same-paper pair masking.
   - Evaluates **Research Gaps** *before* top-k pair caps: identifies isolated claims where cross-paper similarity < 0.70.
   - Agglomerative hierarchical clustering partitions claims into shared topic themes.
4. **Stage 3: Strict Academic NLI Referee**
   - Pairs surviving similarity threshold are evaluated in batches by an open-weight LLM referee.
   - Classifies relationships as `AGREE`, `CONTRADICT`, or `METHODOLOGY_DELTA`. Unrelated pairs are pruned.
5. **Stage 4: Deterministic Consensus & Graph Assembly**
   - Computes deterministic consensus score $round(100 \times (A + 0.5D)/(A+C+D))$.
   - Synthesizes executive summary, agreed findings, and top contradiction highlights with strict ID validation.
   - Assembles contract-compliant `AnalysisResult` JSON.

---

## Quickstart

### Prerequisites
- Python 3.11+ (Python 3.11 or 3.12 recommended)
- `pip` or `uv`
- Optional: Groq API key (for fast cloud inference with Llama 3.1 8B), Hugging Face token, or local Ollama instance.

### Installation

```bash
# Clone the repository
git clone https://github.com/taiwodurotoluwa-svg/kairos.git
cd kairos/backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy `.env.example` to `.env` and configure your LLM providers:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `GROQ_API_KEY` | API key for Groq Cloud inference | `""` |
| `GROQ_MODEL` | Primary open-weight model on Groq | `llama-3.1-8b-instant` |
| `HUGGINGFACE_API_KEY` | Secondary failover API key | `""` |
| `OLLAMA_BASE_URL` | Local offline Ollama server URL | `http://localhost:11434/v1` |
| `EMBEDDING_BACKEND` | Embedding backend engine | `fastembed` |
| `SIMILARITY_THRESHOLD` | Empirical cosine similarity cutoff | `0.70` |
| `JOB_TIMEOUT_SECONDS` | Pipeline execution timeout | `90` |
| `ANALYZE_RATE_LIMIT_PER_MINUTE` | Per-IP rate limit | `6` |

---

## API Endpoints

### 1. Health & Readiness
`GET /api/v1/health`  
Returns provider health (`ok` or `degraded`), active LLM provider chain, embedding model readiness, and loaded demo presets.

### 2. Demo Presets (Zero API Key Mode)
- `GET /api/v1/demo/presets`: Lists curated multi-paper presets.
- `GET /api/v1/demo/{preset_id}`: Retrieves pre-computed contract-compliant synthesis fixture in < 100 ms.
  - `demo_radiology_8papers`: 8 chest X-ray deep learning papers.
  - `demo_llm_quantization_6papers`: 6 post-training quantization papers (AWQ vs GPTQ vs SmoothQuant).
  - `demo_microgrids_6papers`: 6 islanded microgrid energy management papers (RL vs MPC).

### 3. Multi-Paper Synthesis
- `POST /api/v1/analyze`: Submit 2 to 10 PDFs (multipart/form-data) and/or arXiv IDs. Returns `202 Accepted` with `analysis_id`, `events_url`, and `result_url`.
- `GET /api/v1/analyze/{analysis_id}/events`: Server-Sent Events (SSE) live progress stream (`progress`, `complete`, `failed`) with 15-second keep-alive comments.
- `GET /api/v1/analyze/{analysis_id}`: Polls active job state (`QUEUED`, `RUNNING`) or returns final completed `AnalysisResult`.

---

## Running the Application

### Development Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Docker Deployment

Build and run using the production Dockerfile:

```bash
# Build from repository root
docker build -f backend/Dockerfile -t kairos-backend .

# Run container (presets run out-of-the-box with zero keys)
docker run -p 8000:8000 --env-file backend/.env kairos-backend
```

The Docker image pre-bakes `BAAI/bge-small-en-v1.5` so cold starts serve requests immediately.

---

## Testing

Run the full automated test suite (contract tests, quote verification, NLI referee, similarity, and integration tests):

```bash
python -m pytest backend/tests -v
```

All 97 unit and integration tests execute in < 8 seconds.

---

## Troubleshooting

1. **`LLM_PROVIDER_UNAVAILABLE` on live analyze:**
   Ensure at least one valid provider key (`GROQ_API_KEY` or `HUGGINGFACE_API_KEY`) is set in `.env`, or that local Ollama is running (`ollama run llama3.2:3b`). Demo presets (`GET /api/v1/demo/{id}`) require zero keys.
2. **`RATE_LIMITED` (HTTP 429):**
   The live analyze endpoint enforces a default sliding window of 6 requests per minute per IP. Adjust `ANALYZE_RATE_LIMIT_PER_MINUTE` in `.env` if necessary.
3. **`PDF_PARSE_FAILED` or `NO_TEXT_LAYER`:**
   Kairos processes native, machine-readable scientific PDFs. Scanned image-only PDFs without an OCR text layer will return a descriptive error and warning.
