"""Tests for the autonomous background loop."""

import time
import pytest
from src.cognition.autonomous import AutonomousLoop, SpontaneousThought


class TestSpontaneousThought:
    def test_thought_creation(self):
        t = SpontaneousThought("I wonder...", "reflection", "DMN")
        assert t.content == "I wonder..."
        assert t.type == "reflection"
        assert t.source == "DMN"
        assert t.timestamp > 0

    def test_repr(self):
        t = SpontaneousThought("Hello", "insight", "creativity")
        assert "[insight]" in repr(t)
        assert "Hello" in repr(t)


class TestAutonomousLoop:
    def setup_method(self):
        self.loop = AutonomousLoop(
            idle_threshold=0.5,  # very short for testing
            tick_interval=0.2,
        )

    def teardown_method(self):
        self.loop.stop()

    def test_initial_state(self):
        assert self.loop.running is False
        assert self.loop.idle_cycles == 0
        assert self.loop.total_thoughts == 0

    def test_start_stop(self):
        self.loop.start()
        assert self.loop.running is True
        self.loop.stop()
        assert self.loop.running is False

    def test_notify_interaction_resets_idle(self):
        self.loop.idle_cycles = 5
        self.loop.notify_interaction()
        assert self.loop.idle_cycles == 0

    def test_get_state(self):
        state = self.loop.get_state()
        assert "running" in state
        assert "idle_cycles" in state
        assert "total_thoughts" in state
        assert "is_idle" in state

    def test_thought_buffer(self):
        self.loop._add_thought("Test thought", "reflection", "test")
        assert self.loop.total_thoughts == 1
        assert len(self.loop.spontaneous_thoughts) == 1

        thoughts = self.loop.get_new_thoughts(5)
        assert len(thoughts) == 1
        assert thoughts[0].content == "Test thought"
        # Buffer should be drained
        assert len(self.loop.spontaneous_thoughts) == 0

    def test_peek_doesnt_drain(self):
        self.loop._add_thought("Peek test", "insight", "test")
        peeked = self.loop.peek_thoughts(5)
        assert len(peeked) == 1
        # Still in buffer
        assert len(self.loop.spontaneous_thoughts) == 1

    def test_callbacks_registered(self):
        called = {"wander": False}

        def mock_wander():
            called["wander"] = True
            return {"thoughts": ["test thought"], "insights": []}

        self.loop.register_callbacks(mind_wander=mock_wander)
        self.loop._do_mind_wander()
        assert called["wander"] is True

    def test_goal_review_with_callbacks(self):
        called = {}

        def mock_goals():
            called["goals"] = True
            return {"active_goals": 5, "top_goal": "Learn Python"}

        def mock_motivation():
            called["motivation"] = True
            return {"drives": {"curiosity_drive": 0.8}, "boredom": 2}

        self.loop.register_callbacks(
            check_goals=mock_goals,
            get_motivation=mock_motivation,
        )
        self.loop._do_goal_review()
        assert called.get("goals") is True
        assert self.loop.total_thoughts > 0

    def test_self_reflection(self):
        def mock_emotions():
            return {"happiness": 0.7, "curiosity": 0.3, "fear": 0.1}

        self.loop.register_callbacks(get_emotions=mock_emotions)
        self.loop._do_self_reflection()
        assert self.loop.total_thoughts > 0

    def test_idle_tick_cycles(self):
        """Should rotate through different behaviors."""
        self.loop.idle_cycles = 0
        self.loop._idle_tick()  # mind_wander
        self.loop.idle_cycles = 1
        self.loop._idle_tick()  # goal_review
        self.loop.idle_cycles = 2
        self.loop._idle_tick()  # self_reflection
        self.loop.idle_cycles = 3
        self.loop._idle_tick()  # memory_consolidation
