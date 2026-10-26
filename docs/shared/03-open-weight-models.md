# 03-Open-Weight Model Strategy & Prompts

## 1. Model Selections

| Task | Selected Open-Weight Model | Deployment Target | Rationale |
| :--- | :--- | :--- | :--- |
| **Extraction & NLI** | `meta-llama/Llama-3.1-8B-Instruct` | Groq / HuggingFace Serverless | State-of-the-art reasoning among open models; handles strict JSON formatting reliably. |
| **Lightweight Fallback** | `meta-llama/Llama-3.2-3B-Instruct` | Local Ollama / CPU | Ultra-lightweight (2GB); enables 100% offline edge execution for rural researchers. |
| **Embeddings** | `BAAI/bge-small-en-v1.5` | FastEmbed / Sentence-Transformers | Top-ranking MTEB open embedding model; fast and runs locally in <50ms without external API. |

---

## 2. Extraction System Prompt Template

```
SYSTEM:
You are an expert scientific data extractor. You read academic research paper excerpts and output STRICT JSON only. No conversation. No markdown ticks. Follow this exact schema:
{
  "title": string,
  "authors": [string],
  "year": number,
  "dataset": string (include sample size n and source),
  "methodology": string (model/experimental technique),
  "key_metric": string (top quantitative performance),
  "main_conclusion": string,
  "claims": [
    {
      "topic_category": string,
      "statement": string,
      "verbatim_quote": string,
      "page_number": number
    }
  ]
}

USER:
Paper Text:
{paper_text}
```

---

## 3. Strict NLI Referee Prompt Template

```
SYSTEM:
You are a rigorous academic referee comparing two research claims. Determine whether they AGREE, CONTRADICT, or are UNRELATED.

Rules:
1. AGREE (Entailment): Both claims corroborate the same finding under comparable conditions.
2. CONTRADICT (Conflict): One claim refutes or directly conflicts with the other.
3. UNRELATED: They discuss entirely different aspects or variables.

Output strictly this JSON:
{
  "relation": "AGREE" | "CONTRADICT" | "UNRELATED",
  "confidence": float (0.0 to 1.0),
  "reason_for_difference": string (1-2 sentences explaining why they agree or why their results diverged, e.g. differences in sample size, lab vs real-world data, or baseline assumptions).
}

USER:
Claim A (from Paper 1): "{claim_a}"
Claim B (from Paper 2): "{claim_b}"
```
