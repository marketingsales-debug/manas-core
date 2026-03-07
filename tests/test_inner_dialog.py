"""Tests for BrocasArea inner dialog."""

import pytest
from src.brain.mechanisms.language import BrocasArea, SemanticNetwork


class TestInnerDialog:
    def setup_method(self):
        self.semantic_net = SemanticNetwork()
        self.brocas = BrocasArea(self.semantic_net)

    def test_run_inner_dialog_returns_string(self):
        comprehension = {"intent": "question", "entities": ["python"]}
        emotions = {"curiosity": 0.7, "fear": 0.1}
        reasoning = {"confidence": 0.6, "action": "respond"}

        result = self.brocas.run_inner_dialog(
            comprehension, emotions, reasoning,
        )
        assert isinstance(result, str)
        assert len(result) > 0

    def test_inner_dialog_reflects_question(self):
        comprehension = {"intent": "question", "entities": ["machine", "learning"]}
        emotions = {"curiosity": 0.5}
        reasoning = {"confidence": 0.5, "action": "proceed"}

        result = self.brocas.run_inner_dialog(comprehension, emotions, reasoning)
        assert "asking" in result.lower()

    def test_inner_dialog_reflects_appreciation(self):
        comprehension = {"intent": "appreciation", "entities": []}
        emotions = {"happiness": 0.8}
        reasoning = {"confidence": 0.7, "action": "proceed"}

        result = self.brocas.run_inner_dialog(comprehension, emotions, reasoning)
        assert "gratitude" in result.lower() or "good" in result.lower()

    def test_inner_dialog_with_memories(self):
        comprehension = {"intent": "statement", "entities": ["test"]}
        emotions = {"neutral": 0.3}
        reasoning = {"confidence": 0.5, "action": "proceed"}

        result = self.brocas.run_inner_dialog(
            comprehension, emotions, reasoning,
            memories=["I remember something about tests"],
        )
        assert "recall" in result.lower() or "remember" in result.lower()

    def test_inner_dialog_stored_in_buffer(self):
        comprehension = {"intent": "statement", "entities": []}
        emotions = {"neutral": 0.3}
        reasoning = {"confidence": 0.5, "action": "proceed"}

        self.brocas.run_inner_dialog(comprehension, emotions, reasoning)
        assert len(self.brocas.inner_speech_buffer) == 1

    def test_high_confidence_reasoning(self):
        comprehension = {"intent": "statement", "entities": []}
        emotions = {"neutral": 0.3}
        reasoning = {"confidence": 0.9, "action": "execute"}

        result = self.brocas.run_inner_dialog(comprehension, emotions, reasoning)
        assert "confident" in result.lower()

    def test_low_confidence_reasoning(self):
        comprehension = {"intent": "statement", "entities": []}
        emotions = {"neutral": 0.3}
        reasoning = {"confidence": 0.2, "action": "wait"}

        result = self.brocas.run_inner_dialog(comprehension, emotions, reasoning)
        assert "not sure" in result.lower()
