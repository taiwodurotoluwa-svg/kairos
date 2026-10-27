from __future__ import annotations

import json
from pathlib import Path
import numpy as np

from app.services.embeddings import FastEmbedEmbedder


def run_tuning(data_path: Path | None = None) -> list[dict]:
    if data_path is None:
        data_path = Path(__file__).resolve().parent.parent / "tests" / "data" / "tuning_pairs.json"

    with open(data_path, "r", encoding="utf-8") as f:
        pairs = json.load(f)

    print(f"Loaded {len(pairs)} pairs from {data_path}")

    # Build texts to embed
    texts_a: list[str] = []
    texts_b: list[str] = []
    labels: list[str] = []

    for item in pairs:
        ca = item["claim_a"]
        cb = item["claim_b"]
        ta = f"{ca['topic_hint'].strip()}: {ca['statement'].strip()}"
        tb = f"{cb['topic_hint'].strip()}: {cb['statement'].strip()}"
        texts_a.append(ta)
        texts_b.append(tb)
        labels.append(item["label"].lower())

    embedder = FastEmbedEmbedder(model_name="BAAI/bge-small-en-v1.5")
    emb_a = embedder.embed(texts_a)
    emb_b = embedder.embed(texts_b)

    # Cosine similarities (dot products since vectors are L2-normalised)
    sims = np.sum(emb_a * emb_b, axis=1)

    thresholds = [round(t, 2) for t in np.arange(0.50, 0.86, 0.05)]
    results = []

    print("\n" + "=" * 65)
    print(f"{'Threshold':<12} | {'Precision':<10} | {'Recall':<10} | {'F1':<10} | {'TP/FP/FN/TN':<15}")
    print("-" * 65)

    best_thresh = 0.65
    max_thresh_with_recall = None

    for thresh in thresholds:
        tp = fp = fn = tn = 0
        for sim, label in zip(sims, labels):
            pred_related = sim >= thresh
            is_related = label == "related"

            if pred_related and is_related:
                tp += 1
            elif pred_related and not is_related:
                fp += 1
            elif not pred_related and is_related:
                fn += 1
            else:
                tn += 1

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        if recall >= 0.85:
            max_thresh_with_recall = thresh

        row = {
            "threshold": thresh,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "tn": tn,
        }
        results.append(row)
        print(f"{thresh:<12.2f} | {precision:<10.3f} | {recall:<10.3f} | {f1:<10.3f} | {f'{tp}/{fp}/{fn}/{tn}':<15}")

    print("=" * 65)
    chosen = max_thresh_with_recall if max_thresh_with_recall is not None else 0.65
    print(f"\nRecommended threshold (highest threshold with Recall >= 0.85): {chosen:.2f}")

    return results


if __name__ == "__main__":
    run_tuning()
