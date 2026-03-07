"""Tests for autonomous goal generation."""

import pytest
from src.brain.mechanisms.motivation import GoalSystem, MotivationEngine


class TestAutoGoalGeneration:
    def setup_method(self):
        self.goals = GoalSystem()
        # Use a mock neurochem
        from unittest.mock import MagicMock
        self.neurochem = MagicMock()
        self.neurochem.get_levels.return_value = {
            "dopamine": 0.5, "serotonin": 0.5, "cortisol": 0.3,
            "oxytocin": 0.5, "norepinephrine": 0.3, "endorphins": 0.4,
        }
        self.engine = MotivationEngine(self.neurochem, self.goals)

    def test_novel_topic_creates_curiosity_goal(self):
        """High novelty topic should create a 'learn about' goal."""
        initial_count = len(self.goals.goals)
        self.engine.auto_generate_goals("quantum physics", novelty=0.9)
        assert len(self.goals.goals) > initial_count
        assert "learn_quantum_physics" in self.goals.goals
        assert self.goals.goals["learn_quantum_physics"].category == "curiosity"

    def test_low_novelty_no_curiosity_goal(self):
        """Low novelty should NOT create curiosity goals."""
        initial_count = len(self.goals.goals)
        self.engine.auto_generate_goals("old topic", novelty=0.3)
        assert "learn_old_topic" not in self.goals.goals

    def test_repeated_topic_creates_growth_goal(self):
        """Topic seen 5+ times should create a 'get better at' goal."""
        topic = "python"
        for _ in range(6):
            self.engine.novelty_tracker[topic] = self.engine.novelty_tracker.get(topic, 0) + 1
        self.engine.auto_generate_goals(topic, novelty=0.2)
        assert "improve_python" in self.goals.goals
        assert self.goals.goals["improve_python"].category == "growth"

    def test_help_seeking_creates_social_goal(self):
        """Help-seeking intent with repeated topic should create social goal."""
        topic = "debugging"
        self.engine.novelty_tracker[topic] = 4
        self.engine.auto_generate_goals(topic, novelty=0.3, intent="help_seeking")
        assert "help_debugging" in self.goals.goals
        assert self.goals.goals["help_debugging"].category == "social"

    def test_duplicate_goals_not_created(self):
        """Same topic twice shouldn't create duplicate goals."""
        self.engine.auto_generate_goals("machine learning", novelty=0.9)
        count_after_first = len(self.goals.goals)
        self.engine.auto_generate_goals("machine learning", novelty=0.9)
        assert len(self.goals.goals) == count_after_first

    def test_max_goals_cap(self):
        """Should stop creating goals when at cap (15 active)."""
        # Fill up to 15 active goals
        for i in range(15):
            self.goals.add_goal(f"filler_{i}", f"Goal {i}", "curiosity", 0.5)
        initial = len(self.goals.goals)
        self.engine.auto_generate_goals("new topic", novelty=0.9)
        assert len(self.goals.goals) == initial  # no new goal added

    def test_short_topic_ignored(self):
        """Very short topics should be ignored."""
        initial = len(self.goals.goals)
        self.engine.auto_generate_goals("ab", novelty=0.9)
        assert len(self.goals.goals) == initial
