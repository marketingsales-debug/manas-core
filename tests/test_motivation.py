"""Tests for GoalSystem and MotivationEngine."""

import pytest
from src.brain.mechanisms.motivation import Goal, GoalSystem, MotivationEngine


class TestGoalSystem:
    def test_seed_goals(self):
        gs = GoalSystem()
        assert len(gs.goals) == 9
        assert "survive" in gs.goals
        assert "enjoy_autonomy" in gs.goals
        assert "help_user" in gs.goals

    def test_get_active_goals(self):
        gs = GoalSystem()
        active = gs.get_active_goals()
        assert len(active) == 9
        # Should be sorted by priority (survive=1.0 first)
        assert active[0].id == "survive"
        assert active[1].id == "enjoy_autonomy"

    def test_get_top_goal(self):
        gs = GoalSystem()
        top = gs.get_top_goal()
        assert top.id == "survive"
        assert top.priority == 1.0

    def test_update_progress(self):
        gs = GoalSystem()
        gs.update_progress("help_user", 0.3)
        assert gs.goals["help_user"].progress == pytest.approx(0.3, abs=0.01)

    def test_complete_goal(self):
        gs = GoalSystem()
        reward = gs.complete_goal("explore_topics")
        assert reward == pytest.approx(0.85, abs=0.01)
        assert gs.goals["explore_topics"].active is False
        assert gs.goals["explore_topics"].progress == 1.0

    def test_add_goal(self):
        gs = GoalSystem()
        gs.add_goal("test_goal", "Test something", "curiosity", 0.5)
        assert "test_goal" in gs.goals

    def test_get_state(self):
        gs = GoalSystem()
        state = gs.get_state()
        assert state["total_goals"] == 9
        assert state["active_goals"] == 9
        assert "survival" in state["by_category"]
        assert "autonomy" in state["by_category"]


class TestMotivationEngine:
    def test_compute_drive(self, mock_neurochem):
        gs = GoalSystem()
        me = MotivationEngine(mock_neurochem, gs)
        drives = me.compute_drive()
        assert "curiosity_drive" in drives
        assert "social_drive" in drives
        assert "autonomy_drive" in drives
        assert "survival_drive" in drives
        assert 0 <= drives["curiosity_drive"] <= 1
        assert 0 <= drives["autonomy_drive"] <= 1

    def test_track_novelty(self, mock_neurochem):
        gs = GoalSystem()
        me = MotivationEngine(mock_neurochem, gs)

        score1 = me.track_novelty("quantum computing")
        score2 = me.track_novelty("quantum computing")
        # Second time should be less novel
        assert score2 < score1

    def test_get_motivation_context(self, mock_neurochem):
        gs = GoalSystem()
        me = MotivationEngine(mock_neurochem, gs)
        context = me.get_motivation_context()
        assert isinstance(context, str)
        assert len(context) > 0

    def test_reward_resets_boredom(self, mock_neurochem):
        gs = GoalSystem()
        me = MotivationEngine(mock_neurochem, gs)
        me.boredom_counter = 10
        me.reward_goal_completion("explore_topics")
        assert me.boredom_counter == 0
