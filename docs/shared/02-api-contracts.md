# 02-API Contracts & Schemas

Single source of truth for communication between Backend (FastAPI) and Frontend (Next.js).

---

## 1. Data Models (Pydantic / TypeScript)

### PaperClaim
```typescript
interface PaperClaim {
  id: string;               // e.g. "claim_p1_01"
  paper_id: string;         // e.g. "paper_01"
  topic_category: string;   // e.g. "Accuracy", "Generalization", "Inference Cost"
  statement: string;        // "ResNet-50 achieves 94.2% diagnostic accuracy on chest X-rays."
  verbatim_quote: string;   // Exact quote from the PDF text
  page_number: number;      // 1-indexed page where quote appears
}
```

### PaperExtraction
```typescript
interface PaperExtraction {
  id: string;               // "paper_01"
  filename: string;         // "smith2024_radiology.pdf"
  title: string;            // "Deep Residual Learning for Automated Chest Radiography"
  authors: string[];        // ["J. Smith", "A. Doe"]
  year: number;             // 2024
  dataset: string;          // "NIH ChestX-ray14 (n = 1,200 curated scans)"
  methodology: string;      // "Fine-tuned ResNet-50 with supervised cross-entropy"
  key_metric: string;       // "94.2% Accuracy, AUC 0.96"
  main_conclusion: string;  // "Deep models surpass baseline human radiologists in clean lab conditions."
  claims: PaperClaim[];
}
```

### ContradictionEdge
```typescript
interface ContradictionEdge {
  id: string;                    // "edge_p1_p2_01"
  source_claim_id: string;       // "claim_p1_01"
  target_claim_id: string;       // "claim_p2_01"
  source_paper_title: string;    // "Smith et al. (2024)"
  target_paper_title: string;    // "Adewale et al. (2025)"
  relation_type: "AGREE" | "CONTRADICT";
  confidence_score: number;      // 0.0 to 1.0
  reason_for_difference: string; // "Smith evaluated on clean curated datasets, while Adewale tested on noisy hospital records with severe motion artifact."
  source_quote: string;
  target_quote: string;
}
```

### ConsensusReport
```typescript
interface ConsensusReport {
  executive_summary: string;
  agreed_findings: string[];     // Bullet points of universal agreement
  conflicting_findings: string[];// Bullet points of disputed questions
  recommended_resolution: string; // What future research is needed
}
```

### SynthesisResponse (Main Payload)
```typescript
interface SynthesisResponse {
  papers: PaperExtraction[];
  edges: ContradictionEdge[];
  consensus: ConsensusReport;
  execution_time_seconds: number;
}
```

---

## 2. API Endpoints

### `POST /api/synthesize`
* **Request:** `multipart/form-data` containing 3 to 5 `.pdf` files.
* **Response:** `200 OK` with JSON matching `SynthesisResponse`.

### `GET /api/sample/{dataset_id}`
* **Params:** `dataset_id` = `radiology` | `hallucination` | `microgrid`
* **Response:** Instant cached `SynthesisResponse` for instantaneous demo day testing.

### `GET /api/health`
* **Response:** `{"status": "ok", "model": "meta-llama/Llama-3.1-8B-Instruct", "backend": "online"}`
