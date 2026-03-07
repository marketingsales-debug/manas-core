"""Tests for Working Memory (Phase 3: Long-Term Memory Tiers)."""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import time
import pytest
from src.memory.working_memory import WorkingMemory


class TestWorkingMemory:

    def test_push_and_get(self):
        wm = WorkingMemory(capacity=7)
        wm.push("hello world")
        wm.push("second item")
        items = wm.get_all()
        assert len(items) == 2
        assert "hello world" in items
        assert "second item" in items

    def test_capacity_evict(self):
        """Oldest item evicted when capacity exceeded (Miller's Law)."""
        wm = WorkingMemory(capacity=3)
        wm.push("first")
        wm.push("second")
        wm.push("third")
        wm.push("fourth")   # should evict "first"
        items = wm.get_all()
        assert len(items) == 3
        assert "first" not in items
        assert "fourth" in items

    def test_ttl_expiry(self):
        """Items expire after TTL seconds."""
        wm = WorkingMemory(capacity=5, ttl_seconds=0.1)
        wm.push("short-lived")
        assert "short-lived" in wm.get_all()
        time.sleep(0.2)
        # After TTL, item should be gone
        assert "short-lived" not in wm.get_all()

    def test_high_importance_extends_ttl(self):
        """High-importance items survive longer than base TTL."""
        wm = WorkingMemory(capacity=5, ttl_seconds=0.1)
        wm.push("important thing", importance=1.0)   # effective TTL = 0.1 * 3 = 0.3s
        wm.push("trivial thing", importance=0.0)      # effective TTL = 0.1s
        time.sleep(0.15)
        items = wm.get_all()
        # Important item should still be there
        assert "important thing" in items
        # Trivial item should be gone
        assert "trivial thing" not in items

    def test_clear(self):
        wm = WorkingMemory(capacity=5)
        wm.push("item1")
        wm.push("item2")
        wm.clear()
        assert wm.size() == 0
        assert wm.get_all() == []

    def test_peek(self):
        wm = WorkingMemory(capacity=7)
        for i in range(5):
            wm.push(f"item-{i}")
        latest = wm.peek(3)
        assert len(latest) == 3
        assert "item-4" in latest

    def test_is_full(self):
        wm = WorkingMemory(capacity=3)
        assert not wm.is_full()
        wm.push("a"); wm.push("b"); wm.push("c")
        assert wm.is_full()

    def test_get_state(self):
        wm = WorkingMemory(capacity=7, ttl_seconds=60)
        wm.push("test state item")
        state = wm.get_state()
        assert state["capacity"] == 7
        assert state["size"] == 1
        assert state["ttl_seconds"] == 60
        assert len(state["items"]) == 1
        assert "test state" in state["items"][0]["content"]
