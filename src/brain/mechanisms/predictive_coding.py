"""
Predictive Coding - The brain as a prediction machine.

Core theory of how the brain works (Karl Friston's Free Energy Principle):

1. The brain constantly generates PREDICTIONS about what will happen next
2. Only PREDICTION ERRORS (surprises) propagate up the hierarchy
3. The brain tries to MINIMIZE prediction errors by:
   a. Updating its model (learning/perception)
   b. Acting on the world (active inference)

This means:
- You don't really "see" the world — you hallucinate it and correct errors
- Most processing is top-down predictions, not bottom-up sensation
- Learning = getting better at predicting
- Attention = adjusting precision of prediction errors
- Emotions = prediction errors about body states (interoceptive)
- Surprise is the fundamental learning signal

Hierarchy:
- Low levels: predict raw sensory features (edges, frequencies)
- Mid levels: predict objects, words, patterns
- High levels: predict situations, narratives, goals
"""

import time
import numpy as np
from typing import Optional


class PredictiveLayer:
    """
    A single layer in the predictive coding hierarchy.

    Each layer:
    - Receives input from below (or from senses at lowest level)
    - Generates predictions about that input
    - Passes prediction errors up to the next level
    - Receives predictions from above to refine its own predictions
    """

    def __init__(self, name: str, size: int = 64, precision: float = 1.0):
        self.name = name
        self.size = size
        self.precision = precision  # how much we trust prediction errors from this level

        # Internal generative model
        self.prediction: np.ndarray = np.zeros(size)
        self.prediction_error: np.ndarray = np.zeros(size)
        self.posterior: np.ndarray = np.zeros(size)  # best guess after combining prediction + input

        # Learning
        self.weights = np.random.normal(0, 0.1, (size, size))
        self.learning_rate: float = 0.01
        self.surprise: float = 0.0

    def predict(self, top_down_signal: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Generate prediction about expected input.

        Uses top-down signal from higher level if available.
        """
        if top_down_signal is not None:
            # Transform top-down signal through weights
            td = top_down_signal[:self.size] if len(top_down_signal) > self.size else np.pad(
                top_down_signal, (0, max(0, self.size - len(top_down_signal)))
            )
            self.prediction = np.tanh(self.weights @ td)
        else:
            # Use own posterior as prediction (self-prediction)
            self.prediction = self.posterior * 0.9

        return self.prediction

    def compute_error(self, actual_input: np.ndarray) -> np.ndarray:
        """
        Compute prediction error = actual - predicted.

        This is the ONLY signal that propagates upward.
        If prediction is perfect, nothing propagates (efficient!).
        """
        inp = actual_input[:self.size] if len(actual_input) > self.size else np.pad(
            actual_input, (0, max(0, self.size - len(actual_input)))
        )

        self.prediction_error = inp - self.prediction

        # Weight by precision (attention modulates precision)
        weighted_error = self.prediction_error * self.precision

        # Compute surprise (scalar summary of prediction error)
        self.surprise = float(np.mean(np.abs(weighted_error)))

        # Update posterior (combine prediction with error)
        self.posterior = self.prediction + weighted_error * 0.5

        return weighted_error

    def learn(self, input_signal: np.ndarray, top_down_signal: np.ndarray):
        """
        Update generative model to reduce future prediction errors.

        This is unsupervised learning — just get better at predicting.
        """
        inp = input_signal[:self.size] if len(input_signal) > self.size else np.pad(
            input_signal, (0, max(0, self.size - len(input_signal)))
        )
        td = top_down_signal[:self.size] if len(top_down_signal) > self.size else np.pad(
            top_down_signal, (0, max(0, self.size - len(top_down_signal)))
        )

        # Gradient descent on prediction error
        error = inp - np.tanh(self.weights @ td)
        gradient = np.outer(error, td) * self.learning_rate
        self.weights += gradient

        # Keep weights bounded
        self.weights = np.clip(self.weights, -2.0, 2.0)


class PredictiveCodingHierarchy:
    """
    The full predictive coding hierarchy.

    Multiple layers from low-level (sensory) to high-level (abstract):
    - sensory: raw input patterns
    - perceptual: objects, words, patterns
    - semantic: meaning, categories
    - narrative: situations, goals, plans

    Information flows:
    - Bottom-up: prediction errors only
    - Top-down: predictions (what we expect to see)
    """

    def __init__(self):
        self.layers: dict[str, PredictiveLayer] = {
            "sensory": PredictiveLayer("sensory", size=128, precision=1.0),
            "perceptual": PredictiveLayer("perceptual", size=64, precision=0.8),
            "semantic": PredictiveLayer("semantic", size=32, precision=0.6),
            "narrative": PredictiveLayer("narrative", size=16, precision=0.4),
        }
        self.layer_order = ["sensory", "perceptual", "semantic", "narrative"]
        self.total_surprise: float = 0.0
        self.free_energy: float = 0.0  # variational free energy (should decrease)
        self.processing_history: list[dict] = []

    def process(self, raw_input: np.ndarray) -> dict:
        """
        Full predictive coding cycle:

        1. Top-down sweep: generate predictions at each level
        2. Bottom-up sweep: compute prediction errors
        3. Learning: update models to reduce errors
        4. Compute free energy (overall surprise)
        """
        results = {}
        errors = {}

        # 1. Top-down sweep (predictions flow down)
        for i in range(len(self.layer_order) - 1, -1, -1):
            layer_name = self.layer_order[i]
            layer = self.layers[layer_name]

            if i < len(self.layer_order) - 1:
                higher_name = self.layer_order[i + 1]
                higher = self.layers[higher_name]
                layer.predict(higher.posterior)
            else:
                layer.predict(None)

        # 2. Bottom-up sweep (only errors flow up)
        current_input = raw_input
        for layer_name in self.layer_order:
            layer = self.layers[layer_name]
            error = layer.compute_error(current_input)
            errors[layer_name] = {
                "surprise": layer.surprise,
                "error_magnitude": float(np.mean(np.abs(error))),
            }
            current_input = error  # only errors propagate up

        # 3. Learning (reduce prediction errors)
        for i, layer_name in enumerate(self.layer_order):
            layer = self.layers[layer_name]
            if i < len(self.layer_order) - 1:
                higher = self.layers[self.layer_order[i + 1]]
                layer.learn(
                    raw_input if i == 0 else self.layers[self.layer_order[i - 1]].prediction_error,
                    higher.posterior,
                )

        # 4. Compute free energy (total surprise across hierarchy)
        self.total_surprise = sum(
            layer.surprise for layer in self.layers.values()
        ) / len(self.layers)

        self.free_energy = self.free_energy * 0.95 + self.total_surprise * 0.05

        result = {
            "layer_errors": errors,
            "total_surprise": self.total_surprise,
            "free_energy": self.free_energy,
            "top_level_representation": self.layers["narrative"].posterior.tolist()[:8],
            "is_surprising": self.total_surprise > 0.3,
        }

        self.processing_history.append({
            "surprise": self.total_surprise,
            "free_energy": self.free_energy,
            "timestamp": time.time(),
        })
        if len(self.processing_history) > 200:
            self.processing_history = self.processing_history[-100:]

        return result

    def set_precision(self, layer_name: str, precision: float):
        """
        Adjust precision (= attention) at a specific level.

        High precision -> prediction errors at this level matter more.
        This is how attention works in predictive coding:
        attending to something = increasing precision of its prediction errors.
        """
        if layer_name in self.layers:
            self.layers[layer_name].precision = np.clip(precision, 0.1, 2.0)

    def get_prediction(self, level: str = "perceptual") -> np.ndarray:
        """Get the current prediction at a given level."""
        if level in self.layers:
            return self.layers[level].prediction
        return np.zeros(64)

    def get_state(self) -> dict:
        return {
            "total_surprise": self.total_surprise,
            "free_energy": self.free_energy,
            "layer_surprise": {
                name: layer.surprise for name, layer in self.layers.items()
            },
            "layer_precision": {
                name: layer.precision for name, layer in self.layers.items()
            },
        }
