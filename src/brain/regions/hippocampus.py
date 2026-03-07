"""
Hippocampus - Memory formation, storage, and retrieval.

In the real brain:
- Converts short-term memories to long-term
- Spatial memory and navigation
- Pattern completion (fill in missing info from partial cues)

For Manas, this is the persistent memory store:
- Now powered by ChromaDB for actual infinite vector scaling
- Retains original biological concepts:
  - Emotional memories are stronger
  - Frequently accessed memories are stronger
  - Unused memories fade (forgetting curve)
  - Consolidation strengthens important memories
"""

import logging
import time
import numpy as np
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any

from ...neurotransmitters.chemistry import NeurochemicalSystem

logger = logging.getLogger(__name__)


@dataclass
class Memory:
    id: str
    content: str
    memory_type: str
    emotional_valence: float
    emotional_intensity: float
    importance: float
    timestamp: float
    access_count: int = 0
    last_accessed: float = 0.0
    context: str = ""
    associations: str = ""
    decay_rate: float = 0.999
    tier: str = "short_term"


class Hippocampus:
    """
    Infinite Vector Memory System powered by ChromaDB.
    Maintains the biological simulation of memory decay and emotional weighting.
    """

    def __init__(self, neurochem: NeurochemicalSystem, db_path: str = None):
        self.neurochem = neurochem

        if db_path is None:
            # We use a dedicated directory for Chroma data
            db_path = str(Path.home() / "manas" / "data" / "chroma_db")

        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.db_path = db_path
        
        # Load ChromaDB
        self._init_chroma()

    def _init_chroma(self):
        """Initializes the local ChromaDB client and collection."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Use persistent local storage
            self.chroma_client = chromadb.PersistentClient(path=self.db_path)
            
            # Create or get the main 'hippocampus' collection
            self.collection = self.chroma_client.get_or_create_collection(
                name="hippocampus",
                metadata={"hnsw:space": "cosine"}
            )
            logger.debug(f"Hippocampus: ChromaDB active at {self.db_path}.")
            self.has_chromadb = True
            
        except (ImportError, Exception) as e:
            # Silencing the error for the user as requested, but keeping it for debugging
            logger.debug(f"Hippocampus: ChromaDB failed (expected on 3.14): {e}")
            self.has_chromadb = False

    def store(
        self,
        content: str,
        memory_type: str = "episodic",
        context: str = "",
        importance: float = 0.5,
        tier: str = "short_term",
    ) -> Memory:
        """
        Store a new memory in ChromaDB.

        Emotional state at time of encoding affects memory strength.
        High cortisol (fear/stress) -> stronger memory formation.
        High dopamine (reward) -> stronger positive memories.
        """
        if not self.has_chromadb:
            return None

        emotions = self.neurochem.get_emotional_state()
        levels = self.neurochem.get_levels()

        # Emotional valence: positive or negative experience
        valence = levels["dopamine"] - levels["cortisol"]
        valence = np.clip(valence, -1.0, 1.0)

        # Emotional intensity: stronger emotions = stronger memories
        intensity = max(
            emotions.get("fear", 0),
            emotions.get("happiness", 0),
            emotions.get("anxiety", 0),
        )

        # Cortisol (stress) makes memories stick harder (trauma)
        if levels["cortisol"] > 0.6:
            importance = min(1.0, importance + 0.2)
            intensity = min(1.0, intensity + 0.2)

        now = time.time()
        memory_id = f"mem_{int(now * 1000)}_{np.random.randint(10000)}"

        memory = Memory(
            id=memory_id,
            content=content,
            memory_type=memory_type,
            emotional_valence=valence,
            emotional_intensity=intensity,
            importance=importance,
            timestamp=now,
            last_accessed=now,
            context=context,
            tier=tier
        )

        # Store in ChromaDB
        # The built-in embedding function handles text -> vector automatically
        try:
            doc_text = f"{content}\n[Context: {context}]" if context else content
            
            self.collection.add(
                documents=[doc_text],
                metadatas=[{
                    "memory_type": memory_type,
                    "tier": tier,
                    "importance": float(importance),
                    "emotional_intensity": float(intensity),
                    "emotional_valence": float(valence),
                    "timestamp": float(now),
                    "last_accessed": float(now),
                    "access_count": 0,
                    "decay_rate": 0.999
                }],
                ids=[memory_id]
            )
        except Exception as e:
            logger.error(f"Hippocampus: Failed to store memory in ChromaDB: {e}")

        return memory

    def search(self, query: str, memory_type: str = None, limit: int = 5) -> list[Dict[str, Any]]:
        """General memory search (alias for recall)."""
        return self.recall(query, memory_type, limit)

    def recall(self, query: str, memory_type: str = None, limit: int = 5) -> list[Dict[str, Any]]:
        """
        Recall memories using ChromaDB Vector Search.
        
        Biologically inspired: we ask Chroma for a larger candidate pool (e.g. limit*4),
        then rerank them locally based on emotional intensity, importance, and recency.
        """
        if not self.has_chromadb or self.collection.count() == 0:
            return []

        if not query:
            # If no query, return strongest recent memories
            return self.get_strongest_memories(limit)

        try:
            # Metadata filter
            where_clause = None
            if memory_type:
                where_clause = {"memory_type": memory_type}

            # Query ChromaDB (get 4x what we need so we can re-rank by emotion)
            fetch_limit = min(limit * 4, self.collection.count())
            
            results = self.collection.query(
                query_texts=[query],
                n_results=fetch_limit,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )

            if not results["ids"] or not results["ids"][0]:
                return []

            # Extract raw results
            candidates = []
            for i in range(len(results["ids"][0])):
                doc = results["documents"][0][i]
                meta = results["metadatas"][0][i]
                dist = results["distances"][0][i]
                mem_id = results["ids"][0][i]

                # Chroma uses cosine distance (0 is exact match). 
                # Convert to similarity score (1.0 is exact match).
                similarity = max(0.0, 1.0 - (dist / 2.0))

                candidates.append({
                    "id": mem_id,
                    "content": doc,
                    "similarity": similarity,
                    **meta
                })

            # Re-rank based on biological factors
            now = time.time()
            scored_memories = []
            
            for mem in candidates:
                # 1. Semantic similarity (base score 0-1)
                sim_score = mem["similarity"]

                # 2. Emotional intensity & Importance boost
                # Highly emotional/important memories jump forward
                emotion_boost = mem.get("emotional_intensity", 0.5) * 0.2
                importance_boost = mem.get("importance", 0.5) * 0.2

                # 3. Recency & Access frequency
                age_days = (now - mem.get("timestamp", now)) / 86400
                recency_penalty = min(0.3, age_days * 0.01) # Slowly decay score over time
                
                access_boost = min(0.2, mem.get("access_count", 0) * 0.02)

                # Final composite heuristic score
                final_score = sim_score + emotion_boost + importance_boost + access_boost - recency_penalty

                scored_memories.append((final_score, mem))

            # Sort by final score descending
            scored_memories.sort(key=lambda x: x[0], reverse=True)
            top_memories = [m[1] for m in scored_memories[:limit]]

            # Strengthen accessed memories (like real brain)
            for mem in top_memories:
                self._strengthen_memory(mem["id"], mem)

            return top_memories

        except Exception as e:
            logger.error(f"Hippocampus: ChromaDB recall failed: {e}")
            return []

    def _strengthen_memory(self, memory_id: str, current_meta: dict):
        """Accessing a memory strengthens it (like real recall)."""
        if not self.has_chromadb:
            return

        try:
            new_count = current_meta.get("access_count", 0) + 1
            now = time.time()
            
            # Update metadata in ChromaDB
            current_meta["access_count"] = new_count
            current_meta["last_accessed"] = float(now)
            
            self.collection.update(
                ids=[memory_id],
                metadatas=[current_meta]
            )
        except Exception:
            pass

    def consolidate(self):
        """
        Memory consolidation with Ebbinghaus forgetting curve.
        Purges low-importance short-term memories that haven't been accessed.
        """
        if not self.has_chromadb or self.collection.count() == 0:
            return

        now = time.time()
        logger.info("Hippocampus: Starting memory consolidation...")

        try:
            # We can't do complex math in Chroma where clauses easily,
            # so we fetch all short_term memories to evaluate them
            results = self.collection.get(
                where={"tier": "short_term"},
                include=["metadatas"]
            )
            
            if not results["ids"]:
                return
                
            purged = 0
            promoted = 0
            to_delete = []
            
            for i, mem_id in enumerate(results["ids"]):
                meta = results["metadatas"][i]
                
                age_seconds = now - meta.get("timestamp", now)
                last_access = now - meta.get("last_accessed", now)
                access_count = meta.get("access_count", 0)
                importance = meta.get("importance", 0.5)
                intensity = meta.get("emotional_intensity", 0.5)
                
                # Highly emotional or important memories get promoted
                if importance > 0.8 or intensity > 0.8 or access_count >= 3:
                    meta["tier"] = "long_term"
                    self.collection.update(ids=[mem_id], metadatas=[meta])
                    promoted += 1
                    continue
                
                # Forgetting curve: if older than 1 hour and not accessed, delete
                if age_seconds > 3600 and last_access > 3600 and importance < 0.6:
                    to_delete.append(mem_id)
                    purged += 1
            
            if to_delete:
                self.collection.delete(ids=to_delete)
                
            logger.info(f"Hippocampus: Consolidation complete. Promoted {promoted}, Purged {purged}.")
                
        except Exception as e:
            logger.error(f"Hippocampus: Consolidation failed: {e}")

    def promote_to_long_term(self, memory_ids: list[str]) -> int:
        """Promote specific memories to long-term storage."""
        if not self.has_chromadb or not memory_ids:
            return 0
            
        try:
            results = self.collection.get(ids=memory_ids, include=["metadatas"])
            if not results["ids"]:
                return 0
                
            metadatas = results["metadatas"]
            for m in metadatas:
                m["tier"] = "long_term"
                
            self.collection.update(ids=results["ids"], metadatas=metadatas)
            return len(results["ids"])
        except Exception:
            return 0

    def get_memory_count(self) -> dict:
        """Count memories by type and tier."""
        if not self.has_chromadb:
            return {"total": 0}

        try:
            total = self.collection.count()
            # Approximation since Chroma doesn't have aggregate group by
            return {
                "total": total,
                "engine": "chromadb",
                "status": "online"
            }
        except Exception:
            return {"total": 0, "status": "error"}

    def get_strongest_memories(self, limit: int = 10) -> list[Dict[str, Any]]:
        """Get the most important memories (simulated by fetching a batch and sorting)."""
        if not self.has_chromadb or self.collection.count() == 0:
            return []
            
        try:
            # Fetch a decent chunk (up to 100) and sort by importance locally
            fetch_limit = min(100, self.collection.count())
            results = self.collection.get(
                limit=fetch_limit,
                include=["documents", "metadatas"]
            )
            
            if not results["ids"]:
                return []
                
            mems = []
            for i in range(len(results["ids"])):
                mems.append({
                    "id": results["ids"][i],
                    "content": results["documents"][i],
                    **results["metadatas"][i]
                })
                
            # Sort by importance * emotional_intensity descending
            mems.sort(key=lambda x: x.get("importance", 0.5) * x.get("emotional_intensity", 0.5), reverse=True)
            return mems[:limit]
        except Exception:
            return []
