"""
Working Memory — The brain's short-term attention buffer.

In the real brain (George Miller, 1956):
- Working memory holds 7±2 "chunks" of information
- Extremely fast access (milliseconds)
- Very limited duration (~20 seconds without rehearsal)
- Gate to long-term memory: important items get consolidated

For Manas:
- Circular buffer of the last N user inputs / context items
- Items expire after TTL seconds (simulating natural decay)
- Used to give Ollama short-term conversational context
  without the overhead of full hippocampus recall
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class WorkingMemoryItem:
    """A single item in working memory."""
    content: str
    timestamp: float = field(default_factory=time.time)
    importance: float = 0.5  # 0.0-1.0; high importance extends effective TTL


class WorkingMemory:
    """
    Fixed-capacity short-term memory buffer (Miller's Law: 7±2 items).

    Properties:
    - When at capacity, oldest item is displaced (recency bias)
    - Items have a TTL; stale items are purged on access
    - High-importance items survive longer (simulating rehearsal)
    """

    def __init__(self, capacity: int = 20, ttl_seconds: float = 3600.0):
        self.capacity = capacity        # Context window size
        self.ttl_seconds = ttl_seconds
        self._buffer: deque[WorkingMemoryItem] = deque(maxlen=capacity)
        
        # Virtual Context Tiers
        self.core_memory: Dict[str, str] = {
            "persona": "Manas — Autonomous Self-Aware AI",
            "host": "Unknown User",
            "current_mission": "Real-World Super-Autonomy"
        }
        self.archival_memory: List[str] = []

    # ────────────────────────────────────────────
    # Core API
    # ────────────────────────────────────────────

    def push(self, content: str, importance: float = 0.5):
        """
        Add an item to working memory.

        If at capacity, the deque automatically evicts the oldest item.
        """
        item = WorkingMemoryItem(content=content[:500], importance=importance)
        self._buffer.append(item)

    def get_context(self) -> str:
        """Constructs the full prompt context (Core + Recent)."""
        self._purge_stale()
        core = "\n".join([f"[{k.upper()}]: {v}" for k, v in self.core_memory.items()])
        recent = "\n".join([item.content for item in self._buffer])
        return f"--- CORE MEMORY ---\n{core}\n\n--- RECENT CONTEXT ---\n{recent}"

    def update_core(self, key: str, value: str):
        """Updates persistent core memory chunks."""
        self.core_memory[key] = value

    def archive(self, content: str):
        """Moves content to archival memory (infinite swap)."""
        self.archival_memory.append(content)
        if len(self.archival_memory) > 1000: # Simple cap/roll as placeholder
            self.archival_memory.pop(0)

    def get_all(self, include_stale: bool = False) -> list[str]:
        """Return all live items as strings (most recent last)."""
        if not include_stale:
            self._purge_stale()
        return [item.content for item in self._buffer]

    def peek(self, n: int = 3) -> list[str]:
        """Get the n most recent items."""
        self._purge_stale()
        items = list(self._buffer)
        return [item.content for item in items[-n:]]

    def clear(self):
        """Flush all working memory (e.g., on topic switch)."""
        self._buffer.clear()

    def size(self) -> int:
        """Current number of live items."""
        self._purge_stale()
        return len(self._buffer)

    def is_full(self) -> bool:
        return len(self._buffer) >= self.capacity

    # ────────────────────────────────────────────
    # Internal
    # ────────────────────────────────────────────

    def _effective_ttl(self, item: WorkingMemoryItem) -> float:
        """High-importance items survive longer (importance extends TTL up to 3x)."""
        return self.ttl_seconds * (1.0 + item.importance * 2.0)

    def _purge_stale(self):
        """Remove items whose TTL has expired."""
        now = time.time()
        # Rebuild buffer keeping only live items
        live = deque(maxlen=self.capacity)
        for item in self._buffer:
            age = now - item.timestamp
            if age <= self._effective_ttl(item):
                live.append(item)
        self._buffer = live

    def get_state(self) -> dict:
        """Serializable state summary."""
        self._purge_stale()
        return {
            "capacity": self.capacity,
            "size": len(self._buffer),
            "ttl_seconds": self.ttl_seconds,
            "items": [
                {
                    "content": item.content[:80],
                    "age_s": round(time.time() - item.timestamp, 1),
                    "importance": item.importance,
                }
                for item in self._buffer
            ],
        }
