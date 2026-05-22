"""
classifier/embeddings.py — Multilingual embedding model singleton
Loads paraphrase-multilingual-MiniLM-L12-v2 once at startup
and keeps it in memory for the lifetime of the process.
"""
from __future__ import annotations
import numpy as np
import structlog
from sentence_transformers import SentenceTransformer
from backend.config import settings

log = structlog.get_logger()

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """
    Returns the singleton embedding model, loading it on first call.
    Thread-safe for read-only inference use.
    """
    global _model
    if _model is None:
        log.info(
            "embedding_model.loading",
            model=settings.embedding_model_name,
            cache=str(settings.embedding_cache_dir),
        )
        _model = SentenceTransformer(
            settings.embedding_model_name,
            cache_folder=str(settings.embedding_cache_dir),
        )
        log.info("embedding_model.ready")
    return _model


def embed(texts: list[str]) -> np.ndarray:
    """
    Encode a list of strings into L2-normalized embeddings.
    Returns shape (N, 384) float32 array.
    """
    model = get_embedding_model()
    embeddings = model.encode(
        texts,
        batch_size=settings.embedding_batch_size,
        normalize_embeddings=True,      # L2 normalize → cosine sim = dot product
        show_progress_bar=False,
    )
    return embeddings.astype(np.float32)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cosine similarity between two L2-normalized vectors.
    Since both are normalized, this is just the dot product.
    """
    return float(np.dot(a, b))


def serialize_embedding(embedding: np.ndarray) -> bytes:
    """Serialize a numpy float32 embedding to bytes for SQLite storage."""
    return embedding.astype(np.float32).tobytes()


def deserialize_embedding(data: bytes) -> np.ndarray:
    """Deserialize bytes back to a numpy float32 embedding."""
    return np.frombuffer(data, dtype=np.float32)
