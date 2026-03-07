"""Tests for persistent state: SelfModel, GoalSystem, MotivationEngine."""

import os
import json
import time
import pytest


class TestSelfModelPersistence:
    """SelfModel should save/load personality across restarts."""

    def test_save_and_load_personality(self, tmp_data_dir):
        from src.brain.mechanisms.imagination import SelfModel

        model = SelfModel()

        # Drift personality
        model.personality_drift["openness"] = 0.95
        model.personality_drift["neuroticism"] = 0.1
        model.capabilities["reasoning"] = 0.9
        model.add_life_event("First conversation", importance=0.8)
        model.add_life_event("Learned about physics", importance=0.6)

        path = os.path.join(tmp_data_dir, "self_model.json")
        model.save_state(path)

        # Create fresh model and load
        model2 = SelfModel()
        assert model2.personality_drift["openness"] == 0.7  # default
        loaded = model2.load_state(path)

        assert loaded is True
        assert model2.personality_drift["openness"] == 0.95
        assert model2.personality_drift["neuroticism"] == 0.1
        assert model2.capabilities["reasoning"] == 0.9
        assert len(model2.autobiographical_memories) == 2

    def test_load_nonexistent_returns_false(self, tmp_data_dir):
        from src.brain.mechanisms.imagination import SelfModel

        model = SelfModel()
        assert model.load_state(os.path.join(tmp_data_dir, "nope.json")) is False

    def test_load_corrupted_returns_false(self, tmp_data_dir):
        from src.brain.mechanisms.imagination import SelfModel

        path = os.path.join(tmp_data_dir, "bad.json")
        with open(path, "w") as f:
            f.write("{invalid json!!!")

        model = SelfModel()
        assert model.load_state(path) is False
        # Defaults should be preserved
        assert model.personality_drift["openness"] == 0.7

    def test_merge_handles_new_traits(self, tmp_data_dir):
        """Loading old state with fewer traits should merge, not crash."""
        from src.brain.mechanisms.imagination import SelfModel

        path = os.path.join(tmp_data_dir, "partial.json")
        with open(path, "w") as f:
            json.dump({
                "personality_drift": {"openness": 0.99},
                "capabilities": {"reasoning": 0.8},
                "autobiographical_memories": [],
            }, f)

        model = SelfModel()
        loaded = model.load_state(path)
        assert loaded is True
        assert model.personality_drift["openness"] == 0.99
        # Other traits should keep defaults
        assert model.personality_drift["conscientiousness"] == 0.8


class TestGoalSystemPersistence:
    """GoalSystem should save/load goals with progress."""

    def test_save_and_load_goals(self, tmp_data_dir):
        from src.brain.mechanisms.motivation import GoalSystem

        goals = GoalSystem()
        # Modify a seed goal
        goals.update_progress("learn_new", 0.5)
        goals.complete_goal("ask_questions")
        # Add a dynamic goal
        goals.add_goal("learn_physics", "Learn about quantum physics", "curiosity", 0.8)

        path = os.path.join(tmp_data_dir, "goals.json")
        goals.save_state(path)

        # Load into fresh GoalSystem
        goals2 = GoalSystem()
        loaded = goals2.load_state(path)
        assert loaded is True

        assert goals2.goals["learn_new"].progress == 0.5
        assert goals2.goals["ask_questions"].active is False
        assert "learn_physics" in goals2.goals
        assert goals2.goals["learn_physics"].priority == 0.8

    def test_load_nonexistent(self, tmp_data_dir):
        from src.brain.mechanisms.motivation import GoalSystem
        goals = GoalSystem()
        assert goals.load_state(os.path.join(tmp_data_dir, "nope.json")) is False


class TestMotivationPersistence:
    """MotivationEngine should save/load novelty and boredom."""

    def test_save_and_load_motivation(self, tmp_data_dir, mock_neurochem):
        from src.brain.mechanisms.motivation import GoalSystem, MotivationEngine

        goals = GoalSystem()
        engine = MotivationEngine(mock_neurochem, goals)

        engine.track_novelty("python")
        engine.track_novelty("python")
        engine.track_novelty("quantum")
        engine.boredom_counter = 7

        path = os.path.join(tmp_data_dir, "motivation.json")
        engine.save_state(path)

        # Load into fresh engine
        engine2 = MotivationEngine(mock_neurochem, goals)
        assert engine2.boredom_counter == 0  # default
        loaded = engine2.load_state(path)
        assert loaded is True

        assert engine2.boredom_counter == 7
        assert engine2.novelty_tracker["python"] == 2
        assert engine2.novelty_tracker["quantum"] == 1
