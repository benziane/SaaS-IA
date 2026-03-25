"""
Embedding Service - Generates vector embeddings using sentence-transformers.

Uses all-MiniLM-L6-v2 (384 dimensions) by default - fast, lightweight, free.
Falls back gracefully if sentence-transformers is not installed.
"""

import structlog
from typing import Optional

logger = structlog.get_logger()

# Model name - all-MiniLM-L6-v2 is the sweet spot: fast, small (80MB), good quality
DEFAULT_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# Lazy-loaded model singleton
_model = None
_model_name = None


def _get_model(model_name: str = DEFAULT_MODEL):
    """Lazy-load the sentence-transformers model (singleton)."""
    global _model, _model_name
    if _model is not None and _model_name == model_name:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(model_name)
        _model_name = model_name
        logger.info("embedding_model_loaded", model=model_name, dim=EMBEDDING_DIM)
        return _model
    except ImportError:
        logger.warning(
            "sentence_transformers_not_installed",
            msg="pip install sentence-transformers to enable vector search. Falling back to TF-IDF.",
        )
        return None
    except Exception as e:
        logger.error("embedding_model_load_failed", error=str(e))
        return None


def is_available() -> bool:
    """Check if the embedding service is available."""
    return _get_model() is not None


def get_model_name() -> str:
    """Get the current embedding model name."""
    return _model_name or DEFAULT_MODEL


def embed_text(text: str, model_name: str = DEFAULT_MODEL) -> Optional[list[float]]:
    """Generate embedding for a single text string.

    Returns a list of floats (384 dimensions) or None if unavailable.
    """
    model = _get_model(model_name)
    if model is None:
        return None
    try:
        # Truncate to model max length (256 tokens ~ 1000 chars for safety)
        text = text[:2000].strip()
        if not text:
            return None
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()
    except Exception as e:
        logger.error("embedding_failed", error=str(e), text_length=len(text))
        return None


def embed_texts(texts: list[str], model_name: str = DEFAULT_MODEL) -> list[Optional[list[float]]]:
    """Generate embeddings for multiple texts in batch (much faster than one-by-one).

    Returns a list of embeddings (or None for empty/failed texts).
    """
    model = _get_model(model_name)
    if model is None:
        return [None] * len(texts)
    try:
        # Truncate and filter
        cleaned = [t[:2000].strip() for t in texts]
        # Encode non-empty texts in batch
        non_empty_indices = [i for i, t in enumerate(cleaned) if t]
        non_empty_texts = [cleaned[i] for i in non_empty_indices]

        if not non_empty_texts:
            return [None] * len(texts)

        embeddings = model.encode(non_empty_texts, normalize_embeddings=True, batch_size=32)

        # Map back to original indices
        result: list[Optional[list[float]]] = [None] * len(texts)
        for idx, emb in zip(non_empty_indices, embeddings):
            result[idx] = emb.tolist()

        return result
    except Exception as e:
        logger.error("batch_embedding_failed", error=str(e), count=len(texts))
        return [None] * len(texts)
