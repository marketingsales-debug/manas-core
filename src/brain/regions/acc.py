"""
Anterior Cingulate Cortex (ACC) - Conflict monitoring and error detection.

In the real brain:
- Monitors for conflicts between competing responses
- Detects errors and triggers corrective action
- Adjusts cognitive control (tells prefrontal to focus harder)
- Pain processing (both physical and social)
- Motivation: integrates effort costs with rewards
- Autonomic regulation: adjusts arousal based on task demands
- Surprise detection: "this wasn't supposed to happen"

For Manas:
- Detects when multiple systems disagree (amygdala says stop, prefrontal says go)
- Monitors for errors and unexpected outcomes
- Adjusts effort allocation (when to think harder)
- Detects cognitive overload
- Triggers arousal when task demands increase
"""

import time
import numpy as np
from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class ConflictMonitor:
    """
    Detects response conflict — when the brain can't decide.

    High conflict = multiple strong competing signals.
    This triggers increased cognitive control (try harder, pay more attention).
    """

    def __init__(self):
        self.conflict_level: float = 0.0
        self.conflict_history: list[float] = []
        self.baseline_conflict: float = 0.1

    def detect_conflict(self, signals: dict[str, float]) -> float:
        """
        Measure conflict between brain region signals.

        Conflict is high when multiple regions have strong,
        opposing signals (e.g., amygdala says STOP, prefrontal says GO).
        """
        if len(signals) < 2:
            self.conflict_level = 0.0
            return 0.0

        values = list(signals.values())
        # Conflict = variance of signal strengths (all similar = high conflict)
        mean_val = np.mean(values)
        if mean_val < 0.1:
            self.conflict_level = 0.0
            return 0.0

        # Normalize by mean to get relative conflict
        variance = np.var(values)
        # Low variance + high mean = high conflict (everyone active but can't agree)
        conflict = mean_val * (1.0 - min(1.0, variance * 4.0))

        self.conflict_level = np.clip(conflict, 0.0, 1.0)
        self.conflict_history.append(self.conflict_level)
        if len(self.conflict_history) > 100:
            self.conflict_history = self.conflict_history[-50:]

        return self.conflict_level

    def get_sustained_conflict(self, window: int = 10) -> float:
        """Average conflict over recent history. Sustained conflict = stress."""
        if len(self.conflict_history) < window:
            return self.conflict_level
        return np.mean(self.conflict_history[-window:])


class ErrorDetector:
    """
    Detects errors and unexpected outcomes.

    The ACC fires strongly when:
    - An error is made
    - Something unexpected happens
    - A prediction is violated

    This error signal drives learning and behavioral adjustment.
    """

    def __init__(self):
        self.error_rate: float = 0.0
        self.recent_errors: list[dict] = []
        self.surprise_threshold: float = 0.3

    def detect_error(self, expected: dict, actual: dict) -> dict:
        """
        Compare expected vs actual outcome. Detect mismatches.
        """
        mismatches = []
        total_error = 0.0

        for key in expected:
            if key in actual:
                exp_val = expected[key]
                act_val = actual[key]

                if isinstance(exp_val, (int, float)) and isinstance(act_val, (int, float)):
                    error = abs(float(exp_val) - float(act_val))
                    if error > self.surprise_threshold:
                        mismatches.append({
                            "field": key,
                            "expected": exp_val,
                            "actual": act_val,
                            "error": error,
                        })
                        total_error += error
                elif exp_val != act_val:
                    mismatches.append({
                        "field": key,
                        "expected": exp_val,
                        "actual": act_val,
                        "error": 1.0,
                    })
                    total_error += 1.0

        error_magnitude = min(1.0, total_error / max(1, len(expected)))

        error_info = {
            "has_error": len(mismatches) > 0,
            "error_magnitude": error_magnitude,
            "mismatches": mismatches,
            "surprise": error_magnitude > self.surprise_threshold,
            "timestamp": time.time(),
        }

        if error_info["has_error"]:
            self.recent_errors.append(error_info)
            if len(self.recent_errors) > 50:
                self.recent_errors = self.recent_errors[-30:]

        # Update running error rate
        self.error_rate = self.error_rate * 0.9 + error_magnitude * 0.1

        return error_info

    def get_error_trend(self) -> str:
        """Are errors increasing, decreasing, or stable?"""
        if len(self.recent_errors) < 5:
            return "insufficient_data"

        recent = [e["error_magnitude"] for e in self.recent_errors[-10:]]
        older = [e["error_magnitude"] for e in self.recent_errors[-20:-10]]

        if not older:
            return "insufficient_data"

        recent_avg = np.mean(recent)
        older_avg = np.mean(older)

        if recent_avg > older_avg * 1.2:
            return "increasing"
        elif recent_avg < older_avg * 0.8:
            return "decreasing"
        return "stable"


class EffortAllocator:
    """
    Decides how much cognitive effort to expend.

    The ACC weighs effort costs against expected rewards:
    - Easy task, low reward -> minimal effort
    - Hard task, high reward -> maximum effort
    - Hard task, low reward -> might not be worth it (apathy)

    This maps to the concept of "cognitive fatigue" — limited resources.
    """

    def __init__(self):
        self.current_effort: float = 0.5
        self.fatigue: float = 0.0
        self.effort_capacity: float = 1.0

    def compute_effort(
        self,
        task_difficulty: float,
        expected_reward: float,
        conflict_level: float,
    ) -> float:
        """
        How much effort should we put in?

        High conflict -> more effort (need to resolve disagreement)
        High difficulty + high reward -> more effort
        High fatigue -> less capacity for effort
        """
        # Reward-effort trade-off
        effort_demand = task_difficulty * 0.4 + conflict_level * 0.4 + expected_reward * 0.2

        # Fatigue reduces capacity
        available_capacity = self.effort_capacity * (1.0 - self.fatigue * 0.5)

        self.current_effort = min(available_capacity, effort_demand)

        # Effort causes fatigue
        self.fatigue = min(1.0, self.fatigue + self.current_effort * 0.01)

        return self.current_effort

    def rest(self, amount: float = 0.1):
        """Reduce fatigue (like taking a break)."""
        self.fatigue = max(0.0, self.fatigue - amount)

    def get_state(self) -> dict:
        return {
            "current_effort": self.current_effort,
            "fatigue": self.fatigue,
            "capacity": self.effort_capacity,
            "effective_capacity": self.effort_capacity * (1.0 - self.fatigue * 0.5),
        }


class ACC:
    """
    The complete Anterior Cingulate Cortex.

    Integrates conflict monitoring, error detection, and effort allocation
    to provide executive oversight of cognitive processing.
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.neurochem = neurochem
        self.cluster = NeuronCluster("acc", size=64, excitatory_ratio=0.75)

        self.conflict_monitor = ConflictMonitor()
        self.error_detector = ErrorDetector()
        self.effort_allocator = EffortAllocator()

        self.arousal_signal: float = 0.0

    def monitor(
        self,
        brain_signals: dict[str, float],
        expected_outcome: dict = None,
        actual_outcome: dict = None,
        task_difficulty: float = 0.5,
        expected_reward: float = 0.5,
    ) -> dict:
        """
        Full ACC processing cycle:
        1. Monitor conflict between brain regions
        2. Detect errors if outcome available
        3. Compute effort allocation
        4. Adjust arousal/attention signals
        """
        # 1. Conflict monitoring
        conflict = self.conflict_monitor.detect_conflict(brain_signals)

        # 2. Error detection
        error_info = {}
        if expected_outcome and actual_outcome:
            error_info = self.error_detector.detect_error(expected_outcome, actual_outcome)

            # Errors trigger norepinephrine (alertness)
            if error_info.get("surprise", False):
                self.neurochem.release("norepinephrine", error_info["error_magnitude"] * 0.3)
                self.neurochem.release("cortisol", error_info["error_magnitude"] * 0.1)

        # 3. Effort allocation
        effort = self.effort_allocator.compute_effort(
            task_difficulty, expected_reward, conflict,
        )

        # 4. Arousal adjustment
        # High conflict or errors -> increase arousal
        self.arousal_signal = conflict * 0.4 + effort * 0.3
        if error_info.get("has_error", False):
            self.arousal_signal += error_info["error_magnitude"] * 0.3
        self.arousal_signal = min(1.0, self.arousal_signal)

        # Sustained conflict causes stress
        sustained = self.conflict_monitor.get_sustained_conflict()
        if sustained > 0.5:
            self.neurochem.release("cortisol", sustained * 0.05)

        return {
            "conflict_level": conflict,
            "sustained_conflict": sustained,
            "error": error_info,
            "effort": effort,
            "arousal_signal": self.arousal_signal,
            "fatigue": self.effort_allocator.fatigue,
            "error_trend": self.error_detector.get_error_trend(),
            "should_increase_control": conflict > 0.5 or self.arousal_signal > 0.6,
        }

    def rest(self):
        """Rest the ACC (reduce fatigue)."""
        self.effort_allocator.rest(0.2)

    def get_state(self) -> dict:
        return {
            "conflict_level": self.conflict_monitor.conflict_level,
            "error_rate": self.error_detector.error_rate,
            "effort": self.effort_allocator.get_state(),
            "arousal": self.arousal_signal,
            "activity": self.cluster.get_activity(),
        }
