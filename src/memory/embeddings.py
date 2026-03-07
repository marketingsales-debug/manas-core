"""
Embedding Engine — Semantic vector representations for memory.

In the real brain:
- Distributed representations: concepts encoded as firing patterns
- Similar concepts have similar patterns (neural similarity)
- Semantic priming: activating one concept primes related ones

For Manas:
- Uses sentence-transformers for dense vector embeddings
- Cosine similarity for semantic recall (vs keyword matching)
- Graceful fallback when model unavailable
- Thread-safe singleton pattern for the heavy model
"""

import numpy as np
from typing import Optional
import threading
import logging

logger = logging.getLogger(__name__)

# Singleton lock for model loading
_model_lock = threading.Lock()
_model_instance = None
_model_available: Optional[bool] = None


def _get_model():
    """
    Lazy-load the sentence-transformers model (singleton).

    Uses all-MiniLM-L6-v2: 384-dim, fast, ~80MB.
    Only loads once across the entire process.
    """
    global _model_instance, _model_available

    if _model_available is False:
        return None

    if _model_instance is not None:
        return _model_instance

    with _model_lock:
        # Double-check after acquiring lock
        if _model_instance is not None:
            return _model_instance

        try:
            from sentence_transformers import SentenceTransformer
            _model_instance = SentenceTransformer("all-MiniLM-L6-v2")
            _model_available = True
            logger.info("EmbeddingEngine: loaded all-MiniLM-L6-v2")
            return _model_instance
        except Exception as e:
            _model_available = False
            logger.warning(f"EmbeddingEngine: model unavailable ({e}), falling back to keyword search")
            return None


class EmbeddingEngine:
    """
    Generates and compares semantic vector embeddings.

    - embed(text) -> 384-dim numpy array
    - similarity(a, b) -> float (0.0 to 1.0)
    - batch_embed(texts) -> list of vectors
    - find_most_similar(query_vec, candidates) -> ranked indices

    Falls back gracefully if sentence-transformers isn't available.
    """

    EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dimension

    def __init__(self):
        self._model = None
        self._loaded = False

    @property
    def model(self):
        if not self._loaded:
            self._model = _get_model()
            self._loaded = True
        return self._model

    @property
    def available(self) -> bool:
        return self.model is not None

    def embed(self, text: str) -> Optional[np.ndarray]:
        """
        Embed a single text into a 384-dim vector.

        Returns None if model is unavailable.
        """
        if not self.available:
            return None

        try:
            # Truncate very long texts (transformer limit ~256 tokens)
            text = text[:1000]
            vector = self.model.encode(text, normalize_embeddings=True)
            return np.array(vector, dtype=np.float32)
        except Exception as e:
            logger.warning(f"EmbeddingEngine: embed failed ({e})")
            return None

    def batch_embed(self, texts: list[str]) -> Optional[list[np.ndarray]]:
        """
        Embed multiple texts in a batch (faster than one-by-one).

        Returns None if model is unavailable.
        """
        if not self.available or not texts:
            return None

        try:
            truncated = [t[:1000] for t in texts]
            vectors = self.model.encode(truncated, normalize_embeddings=True)
            return [np.array(v, dtype=np.float32) for v in vectors]
        except Exception as e:
            logger.warning(f"EmbeddingEngine: batch_embed failed ({e})")
            return None

    @staticmethod
    def similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        Cosine similarity between two normalized vectors.

        Returns 0.0-1.0 (higher = more similar).
        Since vectors are L2-normalized, dot product = cosine similarity.
        """
        if vec_a is None or vec_b is None:
            return 0.0
        return float(np.dot(vec_a, vec_b))

    @staticmethod
    def find_most_similar(
        query_vec: np.ndarray,
        candidate_vecs: list[np.ndarray],
        top_k: int = 5,
    ) -> list[tuple[int, float]]:
        """
        Find the most similar vectors to a query.

        Returns list of (index, similarity_score) tuples, sorted by similarity.
        """
        if query_vec is None or not candidate_vecs:
            return []

        # Stack into matrix for vectorized dot product
        matrix = np.vstack(candidate_vecs)
        similarities = matrix @ query_vec

        # Get top-k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        return [(int(idx), float(similarities[idx])) for idx in top_indices]

    @staticmethod
    def vector_to_bytes(vec: np.ndarray) -> bytes:
        """Serialize a vector to bytes for SQLite BLOB storage."""
        return vec.tobytes()

    @staticmethod
    def bytes_to_vector(data: bytes) -> np.ndarray:
        """Deserialize bytes from SQLite BLOB to numpy vector."""
        return np.frombuffer(data, dtype=np.float32)
