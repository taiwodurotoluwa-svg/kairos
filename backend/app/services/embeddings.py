from __future__ import annotations

import hashlib
from typing import Any, Protocol
import numpy as np

from app.config import Settings, get_settings


class Embedder(Protocol):
    """Protocol for embedding models producing L2-normalised vector representations."""

    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a list of strings into an L2-normalised 2D numpy array of shape (N, D)."""
        ...


class FastEmbedEmbedder:
    """FastEmbed-based local embedding using ONNX runtime (CPU-friendly, no PyTorch)."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        from fastembed import TextEmbedding

        self.model_name = model_name
        self._model = TextEmbedding(model_name)

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        raw = list(self._model.embed(texts))
        arr = np.array(raw, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norms, 1e-12)


class HFApiEmbedder:
    """Hugging Face feature extraction HTTP API fallback when local ONNX cannot run."""

    def __init__(
        self,
        token: str,
        model_name: str = "BAAI/bge-small-en-v1.5",
        base_url: str = "https://api-inference.huggingface.co/pipeline/feature-extraction",
    ) -> None:
        self.token = token
        self.model_name = model_name
        self.endpoint = f"{base_url.rstrip('/')}/{model_name}"

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        import httpx

        headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(
                self.endpoint,
                headers=headers,
                json={"inputs": texts, "options": {"wait_for_model": True}},
            )
            resp.raise_for_status()
            data = resp.json()

        arr = np.array(data, dtype=np.float32)
        if arr.ndim == 3:
            arr = arr.mean(axis=1)

        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norms, 1e-12)


class DeterministicStubEmbedder:
    """Deterministic embedding stub for fast, offline, and reproducible unit tests."""

    def __init__(self, dim: int = 384) -> None:
        self.dim = dim

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dim), dtype=np.float32)

        vecs = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            seed = int.from_bytes(digest[:4], "little")
            rng = np.random.RandomState(seed)
            v = rng.randn(self.dim).astype(np.float32)
            vecs.append(v)

        arr = np.array(vecs, dtype=np.float32)
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        return arr / np.maximum(norms, 1e-12)


_EMBEDDER_INSTANCE: Embedder | None = None


def get_embedder(settings: Settings | None = None) -> Embedder:
    """Retrieve or initialize the configured singleton embedder."""
    global _EMBEDDER_INSTANCE
    if _EMBEDDER_INSTANCE is not None:
        return _EMBEDDER_INSTANCE

    if settings is None:
        settings = get_settings()

    backend = settings.embedding_backend.lower()
    if backend == "fastembed":
        _EMBEDDER_INSTANCE = FastEmbedEmbedder(model_name=settings.embedding_model)
    elif backend == "hf_api":
        _EMBEDDER_INSTANCE = HFApiEmbedder(
            token=settings.hf_token,
            model_name=settings.embedding_model,
        )
    elif backend == "stub":
        _EMBEDDER_INSTANCE = DeterministicStubEmbedder()
    else:
        _EMBEDDER_INSTANCE = FastEmbedEmbedder(model_name=settings.embedding_model)

    return _EMBEDDER_INSTANCE


def reset_embedder_cache() -> None:
    """Reset the singleton instance (useful in tests)."""
    global _EMBEDDER_INSTANCE
    _EMBEDDER_INSTANCE = None
