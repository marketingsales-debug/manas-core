"""Tests for EmbeddingEngine and semantic memory recall."""

import os
import pytest
import numpy as np
from src.memory.embeddings import EmbeddingEngine


class TestEmbeddingEngine:
    def setup_method(self):
        self.engine = EmbeddingEngine()

    def test_embed_returns_vector(self):
        vec = self.engine.embed("Hello, world!")
        if not self.engine.available:
            pytest.skip("Embedding model not available")
        assert vec is not None
        assert vec.shape == (EmbeddingEngine.EMBEDDING_DIM,)
        assert vec.dtype == np.float32

    def test_similar_texts_have_high_similarity(self):
        if not self.engine.available:
            pytest.skip("Embedding model not available")
        v1 = self.engine.embed("The cat sat on the mat")
        v2 = self.engine.embed("A cat was sitting on a mat")
        v3 = self.engine.embed("Quantum computing breakthrough in physics")
        sim_related = EmbeddingEngine.similarity(v1, v2)
        sim_unrelated = EmbeddingEngine.similarity(v1, v3)
        # Related texts should be more similar than unrelated ones
        assert sim_related > sim_unrelated
        assert sim_related > 0.5

    def test_batch_embed(self):
        if not self.engine.available:
            pytest.skip("Embedding model not available")
        texts = ["Hello", "World", "Python programming"]
        vecs = self.engine.batch_embed(texts)
        assert vecs is not None
        assert len(vecs) == 3
        assert all(v.shape == (EmbeddingEngine.EMBEDDING_DIM,) for v in vecs)

    def test_find_most_similar(self):
        if not self.engine.available:
            pytest.skip("Embedding model not available")
        query = self.engine.embed("machine learning")
        candidates = self.engine.batch_embed([
            "deep learning neural networks",
            "cooking Italian pasta",
            "artificial intelligence research",
            "gardening tips for spring",
        ])
        results = EmbeddingEngine.find_most_similar(query, candidates, top_k=2)
        assert len(results) == 2
        # ML should be most similar to AI/deep learning, not cooking/gardening
        top_indices = [idx for idx, _ in results]
        assert 0 in top_indices or 2 in top_indices

    def test_vector_serialization(self):
        vec = np.random.randn(EmbeddingEngine.EMBEDDING_DIM).astype(np.float32)
        blob = EmbeddingEngine.vector_to_bytes(vec)
        restored = EmbeddingEngine.bytes_to_vector(blob)
        np.testing.assert_array_almost_equal(vec, restored)

    def test_similarity_with_none(self):
        assert EmbeddingEngine.similarity(None, None) == 0.0
        vec = np.random.randn(EmbeddingEngine.EMBEDDING_DIM).astype(np.float32)
        assert EmbeddingEngine.similarity(vec, None) == 0.0

    def test_find_most_similar_empty(self):
        query = np.random.randn(EmbeddingEngine.EMBEDDING_DIM).astype(np.float32)
        assert EmbeddingEngine.find_most_similar(query, [], top_k=5) == []
        assert EmbeddingEngine.find_most_similar(None, [], top_k=5) == []

    def test_embed_unavailable_returns_none(self):
        engine = EmbeddingEngine()
        engine._loaded = True
        engine._model = None  # Force unavailable
        assert engine.embed("test") is None
        assert engine.batch_embed(["test"]) is None


class TestSemanticRecall:
    """Test hippocampus semantic recall (requires embedding model)."""

    def test_semantic_recall_finds_related_memories(self, tmp_data_dir):
        """Memories should be found by meaning, not just keywords."""
        from src.neurotransmitters.chemistry import NeurochemicalSystem
        from src.brain.regions.hippocampus import Hippocampus

        neurochem = NeurochemicalSystem()
        hippo = Hippocampus(
            neurochem, db_path=os.path.join(tmp_data_dir, "test_memories.db"),
        )

        if not hippo.embedder.available:
            pytest.skip("Embedding model not available")

        # Store memories using specific words
        hippo.store("The python programming language is great for AI", "semantic")
        hippo.store("I had breakfast with scrambled eggs this morning", "episodic")
        hippo.store("Machine learning models need training data", "semantic")
        hippo.store("The weather is sunny and warm today", "episodic")

        # Query using DIFFERENT words (semantic, not keyword match)
        results = hippo.recall("artificial intelligence coding", limit=2)
        assert len(results) > 0
        # Should find python/ML memories, NOT breakfast/weather
        contents = [m.content.lower() for m in results]
        assert any("python" in c or "machine" in c for c in contents)

    def test_keyword_fallback_when_no_embeddings(self, tmp_data_dir):
        """Should fall back to keyword search when embeddings unavailable."""
        from src.neurotransmitters.chemistry import NeurochemicalSystem
        from src.brain.regions.hippocampus import Hippocampus

        neurochem = NeurochemicalSystem()
        hippo = Hippocampus(
            neurochem, db_path=os.path.join(tmp_data_dir, "test_fallback.db"),
        )
        # Store a memory (may or may not have embedding)
        hippo.store("Python is a great programming language", "semantic")

        # Keyword search should always work
        results = hippo._keyword_recall("Python", limit=5)
        assert len(results) > 0
        assert "Python" in results[0].content

    def test_embed_all_memories(self, tmp_data_dir):
        """Batch embedding migration should work."""
        from src.neurotransmitters.chemistry import NeurochemicalSystem
        from src.brain.regions.hippocampus import Hippocampus

        neurochem = NeurochemicalSystem()
        hippo = Hippocampus(
            neurochem, db_path=os.path.join(tmp_data_dir, "test_batch.db"),
        )

        if not hippo.embedder.available:
            pytest.skip("Embedding model not available")

        # Store memories (they should already have embeddings)
        hippo.store("Test memory one", "semantic")
        hippo.store("Test memory two", "episodic")

        stats = hippo.get_embedding_stats()
        assert stats["total_memories"] == 2
        assert stats["model_available"] is True

    def test_embedding_stats(self, tmp_data_dir):
        """Embedding stats should report correctly."""
        from src.neurotransmitters.chemistry import NeurochemicalSystem
        from src.brain.regions.hippocampus import Hippocampus

        neurochem = NeurochemicalSystem()
        hippo = Hippocampus(
            neurochem, db_path=os.path.join(tmp_data_dir, "test_stats.db"),
        )

        stats = hippo.get_embedding_stats()
        assert "total_memories" in stats
        assert "embedded" in stats
        assert "coverage" in stats
        assert "model_available" in stats
