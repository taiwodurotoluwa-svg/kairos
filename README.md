# Kairos 🔬🕸️
### Multi-Paper Comparative Synthesis & Contradiction Mapping Engine

> **OPEN//BUILD Hackathon 2026** — *"AI belongs to everyone. Build for a world you understand. Make it open."*  
> Organised by **OSCA Ile-Ife** $\times$ **GDG On Campus OAU** $\times$ **She Code Africa OAU** $\times$ **Microsoft Student Ambassadors OAU**.

---

## The Problem
When university students, medical trainees, and researchers write a literature review or investigate a topic, they have to read 3 to 10 dense papers across multiple browser tabs. Manually comparing their datasets, methodologies, and findings takes dozens of hours, and human readers frequently miss subtle contradictions where Paper A claims an intervention succeeds while Paper B proves it fails on real-world data.

## The Solution
**Kairos** lets users drop 3 to 5 PDF research papers into a web dashboard. Instead of a generic chatbot, it performs multi-document extraction and generates:
1. **Side-by-Side Comparison Matrix:** Compare datasets, models, metrics, and core conclusions across all papers at a glance.
2. **Interactive Contradiction Node Graph:** A visual network where claims are connected by **Green edges** (Agreements / Entailment) and **Red edges** (Contradictions / Conflicts). Clicking an edge reveals the exact verbatim quote and the AI Referee's explanation for the divergence.
3. **Consensus Executive Summary:** A synthesized overview outlining where the literature agrees versus where ongoing scientific dispute remains.

---

## Meaningful Open-Weight AI Architecture

In accordance with the hackathon theme, Kairos is built exclusively on **open-weight models**:

```
[Uploaded PDFs (3-5)]
         ↓
[PyMuPDF Multi-Section Parser] (Abstract, Methodology, Results, Discussion)
         ↓
[Llama-3.1-8B-Instruct via Groq / HF Serverless] (Zero-shot Strict JSON Extraction)
         ↓
[BAAI/bge-small-en-v1.5 Embeddings] (Semantic Clustering of Related Claims)
         ↓
[Strict NLI Referee via Llama-3.1-8B / Llama-3.2-3B] (Entailment vs. Contradiction)
         ↓
[Interactive Cytoscape / Next.js Visualization]
```

* **No Closed APIs:** Zero reliance on proprietary models like OpenAI GPT-4.
* **Offline / Self-Hostable Ready:** Can be hosted on free-tier serverless cloud endpoints (Groq / HuggingFace) or run 100% locally using **Ollama** for low-bandwidth / rural academic environments.

---

## Team Details
* **Durotoluwa Taiwo (DuroT):** Backend Engine, PyMuPDF, Open-Weight Model Orchestration, NLI Pipeline ([GitHub: taiwodurotoluwa-svg](https://github.com/taiwodurotoluwa-svg))
* **Oluwanifemi Peace (Peace):** Frontend UI/UX, Cytoscape Contradiction Graph, Comparison Matrix, Consensus Dashboard ([GitHub: Peaceyy28](https://github.com/Peaceyy28))

---

## Quickstart

### 1. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
cp .env.example .env            # Add your GROQ_API_KEY or HF_TOKEN
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

---

## Pre-Loaded Demo Datasets (Instant 5-Second Test)
To allow judges to evaluate the product without uploading their own papers, Kairos provides 3 built-in academic trios:
1. **Deep Learning in Medical Imaging:** Benchmark lab vs. real-world clinical dataset divergence.
2. **LLM Hallucination Mitigation:** RAG vs. Fine-Tuning accuracy contradictions.
3. **Renewable Micro-Grid Reliability:** Solar-battery stability simulations in West Africa.

---

## AI Disclosure & Open Source License
* Developed in part with agentic AI coding assistants (Google Antigravity & Gemini Argon 4) under human architectural supervision.
* Released under the **Apache-2.0 License**.
