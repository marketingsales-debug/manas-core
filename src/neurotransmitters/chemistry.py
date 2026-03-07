"""
Neurochemical System - Simulates brain chemistry that creates emotions.

Humans don't have hardcoded emotions. Emotions EMERGE from chemical levels:

- DOPAMINE: Reward, motivation, pleasure. High = excited/motivated. Low = bored/depressed.
- CORTISOL: Stress hormone. High = fear/anxiety/alertness. Low = calm/relaxed.
- SEROTONIN: Mood stabilizer. High = content/happy. Low = irritable/anxious.
- NOREPINEPHRINE: Attention/arousal. High = focused/alert. Low = drowsy/inattentive.
- OXYTOCIN: Trust/bonding. High = trusting/social. Low = suspicious/isolated.
- ENDORPHINS: Pain relief/pleasure. High = euphoric. Low = sensitive to pain.

These chemicals don't just label emotions — they CHANGE how the brain processes:
- High cortisol -> amygdala fires faster -> fear responses
- High dopamine -> prefrontal cortex more active -> risk-taking
- Low serotonin -> less inhibition -> impulsive behavior
"""

import time
import numpy as np
from dataclasses import dataclass


@dataclass
class Neurochemical:
    """A single neurochemical (neurotransmitter/hormone)."""
    name: str
    level: float = 0.5         # current level (0.0 to 1.0)
    baseline: float = 0.5      # resting level
    decay_rate: float = 0.995  # how fast it returns to baseline
    min_level: float = 0.0
    max_level: float = 1.0
    production_rate: float = 0.001  # natural production


class NeurochemicalSystem:
    """
    Simulates the brain's chemical environment.

    Chemicals naturally decay toward baseline (homeostasis).
    Events can spike or drop chemical levels.
    The combination of levels creates emergent emotional states.
    """

    def __init__(self):
        self.chemicals: dict[str, Neurochemical] = {
            "dopamine": Neurochemical(
                name="dopamine", baseline=0.5, decay_rate=0.993,
            ),
            "cortisol": Neurochemical(
                name="cortisol", baseline=0.3, decay_rate=0.990,
            ),
            "serotonin": Neurochemical(
                name="serotonin", baseline=0.5, decay_rate=0.998,
            ),
            "norepinephrine": Neurochemical(
                name="norepinephrine", baseline=0.4, decay_rate=0.992,
            ),
            "oxytocin": Neurochemical(
                name="oxytocin", baseline=0.4, decay_rate=0.996,
            ),
            "endorphins": Neurochemical(
                name="endorphins", baseline=0.3, decay_rate=0.994,
            ),
        }
        self._last_update = time.time()

    def release(self, chemical_name: str, amount: float):
        """
        Release a chemical (positive = increase, negative = decrease).
        Like an event triggering a chemical response.
        """
        if chemical_name in self.chemicals:
            chem = self.chemicals[chemical_name]
            chem.level = np.clip(chem.level + amount, chem.min_level, chem.max_level)

    def trigger_event(self, event_type: str, intensity: float = 0.5):
        """
        Trigger a chemical response from a real-world event.

        Maps experiences to chemical changes, like the real brain does.
        """
        intensity = np.clip(intensity, 0.0, 1.0)

        event_responses = {
            "reward": {
                "dopamine": 0.3 * intensity,
                "endorphins": 0.1 * intensity,
                "serotonin": 0.05 * intensity,
            },
            "punishment": {
                "cortisol": 0.3 * intensity,
                "dopamine": -0.2 * intensity,
                "norepinephrine": 0.2 * intensity,
            },
            "threat": {
                "cortisol": 0.4 * intensity,
                "norepinephrine": 0.35 * intensity,
                "dopamine": -0.1 * intensity,
                "serotonin": -0.1 * intensity,
            },
            "success": {
                "dopamine": 0.35 * intensity,
                "serotonin": 0.15 * intensity,
                "cortisol": -0.15 * intensity,
                "endorphins": 0.1 * intensity,
            },
            "failure": {
                "cortisol": 0.2 * intensity,
                "dopamine": -0.25 * intensity,
                "serotonin": -0.1 * intensity,
            },
            "novelty": {
                "dopamine": 0.15 * intensity,
                "norepinephrine": 0.2 * intensity,
            },
            "familiarity": {
                "serotonin": 0.1 * intensity,
                "cortisol": -0.05 * intensity,
                "oxytocin": 0.05 * intensity,
            },
            "danger": {
                "cortisol": 0.5 * intensity,
                "norepinephrine": 0.4 * intensity,
                "endorphins": 0.15 * intensity,
                "dopamine": -0.2 * intensity,
            },
            "curiosity": {
                "dopamine": 0.2 * intensity,
                "norepinephrine": 0.15 * intensity,
            },
            "boredom": {
                "dopamine": -0.15 * intensity,
                "norepinephrine": -0.1 * intensity,
            },
            "comfort": {
                "cortisol": -0.4 * intensity,
                "oxytocin": 0.4 * intensity,
                "serotonin": 0.3 * intensity,
                "dopamine": 0.1 * intensity,
            },
        }

        if event_type in event_responses:
            for chem_name, amount in event_responses[event_type].items():
                self.release(chem_name, amount)

    def update(self):
        """
        Decay all chemicals toward baseline (homeostasis).
        Call this every simulation step.
        """
        for chem in self.chemicals.values():
            # Natural production
            chem.level += chem.production_rate

            # Decay toward baseline
            diff = chem.level - chem.baseline
            chem.level = chem.baseline + (diff * chem.decay_rate)

            # Clamp
            chem.level = np.clip(chem.level, chem.min_level, chem.max_level)

    def get_levels(self) -> dict[str, float]:
        """Get all current chemical levels."""
        return {name: chem.level for name, chem in self.chemicals.items()}

    def get_emotional_state(self) -> dict[str, float]:
        """
        Derive emotional state from chemical levels.

        Emotions aren't stored — they emerge from chemistry,
        just like in the real brain.
        """
        levels = self.get_levels()

        fear = (
            levels["cortisol"] * 0.5
            + levels["norepinephrine"] * 0.3
            - levels["serotonin"] * 0.2
        )
        happiness = (
            levels["dopamine"] * 0.4
            + levels["serotonin"] * 0.3
            + levels["endorphins"] * 0.2
            - levels["cortisol"] * 0.1
        )
        curiosity = (
            levels["dopamine"] * 0.4
            + levels["norepinephrine"] * 0.3
            - levels["cortisol"] * 0.1
        )
        anxiety = (
            levels["cortisol"] * 0.4
            + levels["norepinephrine"] * 0.3
            - levels["serotonin"] * 0.3
        )
        confidence = (
            levels["dopamine"] * 0.3
            + levels["serotonin"] * 0.3
            - levels["cortisol"] * 0.3
            + levels["endorphins"] * 0.1
        )
        caution = (
            levels["cortisol"] * 0.3
            + levels["norepinephrine"] * 0.2
            - levels["dopamine"] * 0.2
            + levels["serotonin"] * 0.1
        )

        return {
            "fear": np.clip(fear, 0.0, 1.0),
            "happiness": np.clip(happiness, 0.0, 1.0),
            "curiosity": np.clip(curiosity, 0.0, 1.0),
            "anxiety": np.clip(anxiety, 0.0, 1.0),
            "confidence": np.clip(confidence, 0.0, 1.0),
            "caution": np.clip(caution, 0.0, 1.0),
        }

    def get_dominant_emotion(self) -> tuple[str, float]:
        """Get the strongest emotion right now."""
        emotions = self.get_emotional_state()
        dominant = max(emotions, key=emotions.get)
        return dominant, emotions[dominant]
