"""
Basal Ganglia - Action selection, habit formation, reward prediction.

In the real brain:
- Selects which action to execute from competing options
- Direct pathway: GO (excite action)
- Indirect pathway: NO-GO (inhibit action)
- Hyperdirect pathway: STOP (emergency brake)
- Dopamine from VTA/SNc modulates GO vs NO-GO balance
- Learns habits through repetition (procedural memory)
- Computes reward prediction errors (expected vs actual reward)
- Striatum is the input layer, receives from all cortex
- GPi/SNr is the output, sends to thalamus (which routes to motor cortex)

For Manas:
- Decides which action wins when multiple options compete
- Learns habits (frequently rewarded actions become automatic)
- Computes prediction errors for learning
- Can form automatic behaviors that bypass prefrontal deliberation
"""

import time
import numpy as np
from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class ActionCandidate:
    """A candidate action competing for selection."""

    def __init__(self, action_id: str, description: str, salience: float = 0.5):
        self.action_id = action_id
        self.description = description
        self.salience = salience          # how attention-grabbing
        self.go_strength: float = 0.0     # direct pathway activation
        self.nogo_strength: float = 0.0   # indirect pathway activation
        self.habit_strength: float = 0.0  # learned automatic tendency
        self.expected_reward: float = 0.0
        self.urgency: float = 0.0


class Striatum:
    """
    Input layer of basal ganglia — receives from all of cortex.

    Contains:
    - D1 neurons (direct pathway, GO) — activated by dopamine
    - D2 neurons (indirect pathway, NO-GO) — inhibited by dopamine
    - Tonically active interneurons — detect novelty
    """

    def __init__(self, size: int = 96):
        self.d1_cluster = NeuronCluster("striatum_d1", size=size // 2, excitatory_ratio=0.9)
        self.d2_cluster = NeuronCluster("striatum_d2", size=size // 2, excitatory_ratio=0.9)
        self.novelty_detector: float = 0.0

    def process(self, cortical_input: np.ndarray, dopamine: float) -> tuple[float, float]:
        """
        Process cortical input through D1 (GO) and D2 (NO-GO) pathways.

        High dopamine -> D1 wins -> GO (seek reward)
        Low dopamine -> D2 wins -> NO-GO (avoid risk)
        """
        input_strength = float(np.mean(cortical_input))

        # D1 (GO) is excited by dopamine
        go_signal = input_strength * (0.5 + dopamine * 0.8)

        # D2 (NO-GO) is inhibited by dopamine
        nogo_signal = input_strength * (0.5 + (1.0 - dopamine) * 0.8)

        return go_signal, nogo_signal


class SubthalamicNucleus:
    """
    Subthalamic Nucleus (STN) - Emergency brake.

    The hyperdirect pathway: cortex -> STN -> GPi
    Provides fast, global inhibition of all actions.
    Used when you need to STOP everything (e.g., about to step off a cliff).
    """

    def __init__(self):
        self.cluster = NeuronCluster("stn", size=24, excitatory_ratio=0.95)
        self.activation: float = 0.0
        self.threshold: float = 0.6  # above this, STOP all actions

    def evaluate_emergency(self, threat_level: float, conflict_level: float) -> float:
        """
        Should we emergency-stop all actions?

        Activated by:
        - High threat (amygdala signal)
        - High conflict (multiple competing actions with similar strength)
        """
        self.activation = max(threat_level * 0.7, conflict_level * 0.5)
        return self.activation

    def should_stop(self) -> bool:
        return self.activation > self.threshold


class RewardPredictionSystem:
    """
    Computes reward prediction errors (RPE).

    RPE = actual_reward - expected_reward

    This is the core learning signal:
    - Positive RPE (better than expected) -> increase dopamine -> reinforce behavior
    - Negative RPE (worse than expected) -> decrease dopamine -> avoid behavior
    - Zero RPE (as expected) -> no learning needed

    This maps directly to the VTA/SNc dopamine system in the real brain.
    """

    def __init__(self):
        self.predictions: dict[str, float] = {}  # action -> expected reward
        self.prediction_learning_rate: float = 0.1
        self.history: list[dict] = []

    def predict_reward(self, action_id: str) -> float:
        """What reward do we expect from this action?"""
        return self.predictions.get(action_id, 0.0)

    def compute_rpe(self, action_id: str, actual_reward: float) -> float:
        """
        Compute reward prediction error.

        This drives dopamine release in the real brain.
        """
        expected = self.predictions.get(action_id, 0.0)
        rpe = actual_reward - expected

        # Update prediction (temporal difference learning)
        self.predictions[action_id] = expected + self.prediction_learning_rate * rpe

        self.history.append({
            "action": action_id,
            "expected": expected,
            "actual": actual_reward,
            "rpe": rpe,
            "timestamp": time.time(),
        })

        # Keep bounded history
        if len(self.history) > 500:
            self.history = self.history[-300:]

        return rpe


class HabitSystem:
    """
    Habit formation through repetition.

    Initially, actions are goal-directed (prefrontal cortex decides).
    After repeated reward, actions become habitual (basal ganglia takes over).
    This is the shift from deliberate to automatic behavior.

    Like learning to drive: first you think about every action,
    then it becomes automatic.
    """

    def __init__(self):
        self.habits: dict[str, dict] = {}
        self.habit_threshold: float = 0.6  # above this, action is habitual

    def update(self, action_id: str, reward: float):
        """Strengthen or weaken habit based on outcome."""
        if action_id not in self.habits:
            self.habits[action_id] = {
                "strength": 0.0,
                "repetitions": 0,
                "avg_reward": 0.0,
            }

        habit = self.habits[action_id]
        habit["repetitions"] += 1

        # Running average of reward
        habit["avg_reward"] = (habit["avg_reward"] * 0.9) + (reward * 0.1)

        # Habit strength increases with repetition and positive reward
        if reward > 0:
            habit["strength"] = min(1.0, habit["strength"] + 0.02 * reward)
        else:
            # Negative outcomes slowly weaken habits (but habits are sticky)
            habit["strength"] = max(0.0, habit["strength"] - 0.005)

    def is_habitual(self, action_id: str) -> bool:
        """Is this action a habit? If so, it can bypass deliberation."""
        habit = self.habits.get(action_id)
        return habit is not None and habit["strength"] > self.habit_threshold

    def get_habit_strength(self, action_id: str) -> float:
        habit = self.habits.get(action_id)
        return habit["strength"] if habit else 0.0

    def get_all_habits(self) -> dict[str, dict]:
        return {k: v for k, v in self.habits.items() if v["strength"] > 0.1}


class BasalGanglia:
    """
    The complete basal ganglia — action selection and habit learning.

    Core computation:
    1. Cortex sends competing action candidates
    2. Striatum evaluates each (GO vs NO-GO)
    3. STN provides emergency brake if needed
    4. Winner gets through to thalamus -> motor cortex
    5. Reward prediction error drives learning
    6. Repeated rewarded actions become habits
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.neurochem = neurochem
        self.striatum = Striatum()
        self.stn = SubthalamicNucleus()
        self.reward_system = RewardPredictionSystem()
        self.habit_system = HabitSystem()
        self.last_selection: dict = {}
        self.selection_history: list[dict] = []

    def select_action(
        self,
        candidates: list[ActionCandidate],
        threat_level: float = 0.0,
    ) -> dict:
        """
        Select the winning action from competing candidates.

        This is the core function of the basal ganglia.
        """
        if not candidates:
            return {"selected": None, "reason": "no_candidates"}

        dopamine = self.neurochem.chemicals["dopamine"].level

        # Evaluate each candidate through GO/NO-GO pathways
        for candidate in candidates:
            # Create cortical input pattern from salience
            cortical_input = np.full(48, candidate.salience)
            go, nogo = self.striatum.process(cortical_input, dopamine)

            # Add habit strength (habitual actions get a GO boost)
            habit = self.habit_system.get_habit_strength(candidate.action_id)
            go += habit * 0.5

            # Add expected reward
            expected_reward = self.reward_system.predict_reward(candidate.action_id)
            go += max(0, expected_reward) * 0.3

            # Urgency increases GO
            go += candidate.urgency * 0.3

            candidate.go_strength = go
            candidate.nogo_strength = nogo
            candidate.expected_reward = expected_reward
            candidate.habit_strength = habit

        # Check emergency brake (STN)
        conflict = self._compute_conflict(candidates)
        emergency = self.stn.evaluate_emergency(threat_level, conflict)

        if self.stn.should_stop():
            return {
                "selected": None,
                "reason": "emergency_stop",
                "threat_level": threat_level,
                "conflict": conflict,
                "emergency_activation": emergency,
            }

        # Select winner: highest (GO - NO-GO) score
        scored = []
        for c in candidates:
            net_score = c.go_strength - c.nogo_strength
            # Emergency brake reduces all scores
            net_score *= (1.0 - emergency * 0.5)
            scored.append((c, net_score))

        scored.sort(key=lambda x: x[1], reverse=True)
        winner, winning_score = scored[0]

        # Must exceed a minimum threshold to act
        if winning_score < 0.1:
            return {
                "selected": None,
                "reason": "below_threshold",
                "best_score": winning_score,
            }

        result = {
            "selected": winner.action_id,
            "description": winner.description,
            "score": winning_score,
            "go_strength": winner.go_strength,
            "nogo_strength": winner.nogo_strength,
            "is_habitual": self.habit_system.is_habitual(winner.action_id),
            "expected_reward": winner.expected_reward,
            "conflict": conflict,
            "dopamine": dopamine,
            "candidates_evaluated": len(candidates),
        }

        self.last_selection = result
        self.selection_history.append(result)
        if len(self.selection_history) > 200:
            self.selection_history = self.selection_history[-100:]

        return result

    def process_outcome(self, action_id: str, reward: float) -> dict:
        """
        Process the outcome of an action — learn from it.

        1. Compute reward prediction error
        2. RPE drives dopamine (positive RPE -> dopamine burst)
        3. Update habit strength
        """
        # Reward prediction error
        rpe = self.reward_system.compute_rpe(action_id, reward)

        # RPE modulates dopamine
        if rpe > 0:
            self.neurochem.release("dopamine", rpe * 0.2)
        elif rpe < 0:
            self.neurochem.release("dopamine", rpe * 0.15)

        # Update habits
        self.habit_system.update(action_id, reward)

        return {
            "action": action_id,
            "reward": reward,
            "rpe": rpe,
            "dopamine_change": rpe * 0.2 if rpe > 0 else rpe * 0.15,
            "habit_strength": self.habit_system.get_habit_strength(action_id),
            "is_now_habitual": self.habit_system.is_habitual(action_id),
        }

    def _compute_conflict(self, candidates: list[ActionCandidate]) -> float:
        """
        Compute response conflict (multiple actions with similar strength).

        High conflict -> STN activation -> pause to decide.
        """
        if len(candidates) < 2:
            return 0.0

        scores = sorted(
            [c.go_strength - c.nogo_strength for c in candidates],
            reverse=True,
        )
        # Conflict = how close the top two are
        if scores[0] == 0:
            return 0.0
        conflict = 1.0 - abs(scores[0] - scores[1]) / max(abs(scores[0]), 0.01)
        return np.clip(conflict, 0.0, 1.0)

    def get_state(self) -> dict:
        return {
            "stn_activation": self.stn.activation,
            "emergency_brake": self.stn.should_stop(),
            "active_habits": len(self.habit_system.get_all_habits()),
            "predictions_learned": len(self.reward_system.predictions),
            "total_selections": len(self.selection_history),
            "last_selection": self.last_selection.get("selected"),
        }
