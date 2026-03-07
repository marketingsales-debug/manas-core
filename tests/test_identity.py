"""Tests for SelfModel identity and personality."""

import pytest
from src.brain.mechanisms.imagination import SelfModel


class TestSelfModel:
    def test_identity_fields(self):
        sm = SelfModel()
        assert sm.identity["name"] == "Manas"
        assert "origin" in sm.identity
        assert "core_values" in sm.identity
        assert "voice" in sm.identity

    def test_generate_identity_prompt(self):
        sm = SelfModel()
        prompt = sm.generate_identity_prompt()
        assert "Manas" in prompt
        assert "spiking neural network" in prompt
        assert "curious" in prompt.lower() or "open" in prompt.lower()

    def test_generate_identity_prompt_includes_memories(self):
        sm = SelfModel()
        sm.add_life_event("Learned about quantum computing", 0.8)
        prompt = sm.generate_identity_prompt()
        assert "quantum" in prompt.lower()

    def test_evolve_personality_learning(self):
        sm = SelfModel()
        original_openness = sm.personality_drift["openness"]
        sm.evolve_personality("learning", 1.0)
        assert sm.personality_drift["openness"] > original_openness

    def test_evolve_personality_threat(self):
        sm = SelfModel()
        original_neuroticism = sm.personality_drift["neuroticism"]
        sm.evolve_personality("threat", 1.0)
        assert sm.personality_drift["neuroticism"] > original_neuroticism

    def test_evolve_personality_appreciation(self):
        sm = SelfModel()
        original_agree = sm.personality_drift["agreeableness"]
        sm.evolve_personality("appreciation", 1.0)
        assert sm.personality_drift["agreeableness"] > original_agree

    def test_personality_stays_in_bounds(self):
        sm = SelfModel()
        # Drive openness to max
        for _ in range(200):
            sm.evolve_personality("learning", 1.0)
        assert sm.personality_drift["openness"] <= 1.0

        # Drive neuroticism to min with appreciation
        for _ in range(200):
            sm.evolve_personality("appreciation", 1.0)
        assert sm.personality_drift["neuroticism"] >= 0.0

    def test_evolve_unknown_type_no_crash(self):
        sm = SelfModel()
        # Should not crash on unknown types
        sm.evolve_personality("unknown_type", 1.0)

    def test_who_am_i(self):
        sm = SelfModel()
        desc = sm.who_am_i()
        assert "Manas" in desc
        assert "Neuromorphic" in desc
