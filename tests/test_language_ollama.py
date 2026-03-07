"""Tests for Broca's Area Ollama integration."""

import pytest
from unittest.mock import MagicMock
from src.brain.mechanisms.language import BrocasArea, LanguageSystem, SemanticNetwork


class TestBrocasOllamaIntegration:
    def setup_method(self):
        self.semantic_net = SemanticNetwork()
        self.brocas = BrocasArea(self.semantic_net)

    def test_generate_with_ollama(self):
        mock_ollama = MagicMock()
        mock_ollama.is_available.return_value = True
        mock_ollama.generate.return_value = "I understand your question."

        result = self.brocas.generate_response(
            comprehension={"intent": "question", "raw_text": "What is AI?", "emotional_tone": {}},
            emotional_state={"curiosity": 0.7, "fear": 0.1},
            reasoning={"confidence": 0.6, "action": "respond"},
            ollama=mock_ollama,
        )
        assert result["text"] == "I understand your question."
        assert result["source"] == "ollama"

    def test_fallback_when_ollama_unavailable(self):
        mock_ollama = MagicMock()
        mock_ollama.is_available.return_value = False

        result = self.brocas.generate_response(
            comprehension={"intent": "question", "emotional_tone": {}},
            emotional_state={"curiosity": 0.5},
            reasoning={"confidence": 0.5},
            ollama=mock_ollama,
        )
        assert result["source"] == "template"

    def test_fallback_when_ollama_returns_none(self):
        mock_ollama = MagicMock()
        mock_ollama.is_available.return_value = True
        mock_ollama.generate.return_value = None

        result = self.brocas.generate_response(
            comprehension={"intent": "statement", "emotional_tone": {}},
            emotional_state={"neutral": 0.5},
            reasoning={"confidence": 0.5},
            ollama=mock_ollama,
        )
        assert result["source"] == "template"

    def test_fallback_when_no_ollama(self):
        result = self.brocas.generate_response(
            comprehension={"intent": "appreciation", "emotional_tone": {}},
            emotional_state={"happiness": 0.7},
            reasoning={"confidence": 0.8},
            ollama=None,
        )
        assert result["source"] == "template"
        assert "thank" in result["text"].lower() or "good" in result["text"].lower()

    def test_system_prompt_includes_identity(self):
        mock_ollama = MagicMock()
        mock_ollama.is_available.return_value = True
        mock_ollama.generate.return_value = "test"

        self.brocas.generate_response(
            comprehension={"intent": "statement", "raw_text": "hi", "emotional_tone": {}},
            emotional_state={"neutral": 0.5},
            reasoning={"confidence": 0.5},
            identity_prompt="I am Manas, a brain.",
            ollama=mock_ollama,
        )

        # Check that system prompt was built with identity
        call_args = mock_ollama.generate.call_args
        system_prompt = call_args[0][0] if call_args[0] else call_args[1].get("system_prompt", "")
        assert "Manas" in system_prompt

    def test_system_prompt_includes_emotions(self):
        mock_ollama = MagicMock()
        mock_ollama.is_available.return_value = True
        mock_ollama.generate.return_value = "test"

        self.brocas.generate_response(
            comprehension={"intent": "statement", "raw_text": "hi", "emotional_tone": {}},
            emotional_state={"fear": 0.8, "curiosity": 0.2},
            reasoning={"confidence": 0.5},
            ollama=mock_ollama,
        )

        call_args = mock_ollama.generate.call_args
        system_prompt = call_args[0][0]
        assert "fear" in system_prompt.lower()

    def test_build_ollama_prompt_all_context(self):
        prompt = self.brocas._build_ollama_prompt(
            identity="I am Manas",
            emotions={"joy": 0.8, "fear": 0.1},
            memories=["I learned Python", "I helped a user"],
            reasoning={"action": "respond", "confidence": 0.7},
            comprehension={"intent": "question"},
            conversation="User: Hi\nManas: Hello!",
            inner_thought="I think this is interesting",
            gut_feeling={"valence": "positive", "intensity": 0.6},
            conflict_level=0.1,
            consciousness="active perception",
            motivation="feeling curious",
        )
        assert "Manas" in prompt
        assert "joy" in prompt.lower()
        assert "Python" in prompt
        assert "curious" in prompt.lower()
        assert "INSTRUCTIONS" in prompt


class TestLanguageSystemOllama:
    def test_language_system_passes_ollama(self):
        ls = LanguageSystem()
        # Ollama might or might not be available, but should not crash
        result = ls.generate_response(
            comprehension={"intent": "statement", "emotional_tone": {}},
            emotional_state={"neutral": 0.5},
            reasoning={"confidence": 0.5},
        )
        assert "source" in result
