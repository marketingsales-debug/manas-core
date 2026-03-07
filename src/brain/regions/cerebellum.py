"""
Cerebellum - Motor coordination, timing, and procedural learning.

In the real brain:
- Contains MORE neurons than the rest of the brain combined (~69 billion)
- Coordinates smooth, precise movements
- Learns precise timing (rhythm, sequences)
- Error-driven learning via climbing fibers
- Forward models: predicts sensory consequences of actions
- Procedural memory: stores learned motor sequences
- Also involved in cognitive sequencing (planning steps)

For Manas:
- Coordinates multi-step action sequences
- Learns timing patterns (when to do what)
- Forward model: predicts what will happen if an action is taken
- Error correction: adjusts plans when predictions are wrong
- Procedural memory for command sequences
"""

import numpy as np
from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class PurkinjeCell:
    """
    Simplified Purkinje cell — the main computational unit of the cerebellum.

    Real Purkinje cells:
    - Receive ~200,000 synaptic inputs (most connected neuron in brain)
    - Two input types: parallel fibers (context) + climbing fiber (error)
    - Output is always inhibitory
    - Learn by adjusting parallel fiber weights based on climbing fiber error
    """

    def __init__(self, cell_id: str, input_size: int = 64):
        self.cell_id = cell_id
        self.weights = np.random.uniform(0.3, 0.7, input_size)
        self.learning_rate: float = 0.01
        self.output: float = 0.0

    def compute(self, parallel_input: np.ndarray) -> float:
        """Compute output from parallel fiber input."""
        activation = np.dot(self.weights[:len(parallel_input)], parallel_input)
        self.output = 1.0 / (1.0 + np.exp(-activation + 3.0))  # sigmoid
        return self.output

    def learn_from_error(self, error_signal: float, parallel_input: np.ndarray):
        """
        Climbing fiber learning — adjust weights based on error.

        This is supervised learning driven by the inferior olive.
        Error signal = (predicted outcome - actual outcome)
        """
        # LTD (Long-Term Depression): weaken parallel fiber synapses
        # that were active when error occurred
        weight_change = -self.learning_rate * error_signal * parallel_input[:len(self.weights)]
        self.weights = np.clip(self.weights + weight_change, 0.01, 0.99)


class ForwardModel:
    """
    Internal forward model — predicts consequences of actions.

    The cerebellum builds internal models of how the world works:
    - "If I run this command, what will happen?"
    - "If I type this, what response will I get?"

    Predictions are compared to reality. Mismatches drive learning.
    """

    def __init__(self):
        self.models: dict[str, dict] = {}
        self.prediction_accuracy: float = 0.5

    def predict(self, action: str, context: dict) -> dict:
        """Predict the outcome of an action given context."""
        action_key = self._action_key(action)

        if action_key not in self.models:
            return {
                "predicted_success": 0.5,
                "predicted_duration": 1.0,
                "confidence": 0.0,
                "novel": True,
            }

        model = self.models[action_key]
        return {
            "predicted_success": model["success_rate"],
            "predicted_duration": model["avg_duration"],
            "confidence": min(1.0, model["samples"] / 10.0),
            "novel": False,
        }

    def update(self, action: str, actual_outcome: dict):
        """Update forward model with actual outcome."""
        action_key = self._action_key(action)

        if action_key not in self.models:
            self.models[action_key] = {
                "success_rate": 0.5,
                "avg_duration": 1.0,
                "samples": 0,
                "last_error": 0.0,
            }

        model = self.models[action_key]
        success = 1.0 if actual_outcome.get("success", False) else 0.0
        duration = actual_outcome.get("duration", 1.0)

        # Exponential moving average
        alpha = 0.2
        model["success_rate"] = model["success_rate"] * (1 - alpha) + success * alpha
        model["avg_duration"] = model["avg_duration"] * (1 - alpha) + duration * alpha
        model["samples"] += 1

        # Prediction error
        prediction = model["success_rate"]
        model["last_error"] = abs(success - prediction)

        # Update overall accuracy
        if model["samples"] > 5:
            self.prediction_accuracy = (
                self.prediction_accuracy * 0.95 + (1.0 - model["last_error"]) * 0.05
            )

    def _action_key(self, action: str) -> str:
        parts = action.strip().split()
        return parts[0] if parts else "unknown"


class SequenceMemory:
    """
    Procedural memory for action sequences.

    The cerebellum excels at learning sequences:
    - Motor sequences (typing, walking)
    - Cognitive sequences (problem-solving steps)
    - Temporal patterns (rhythm, timing)

    For Manas: remembers successful command sequences.
    """

    def __init__(self):
        self.sequences: dict[str, dict] = {}
        self.current_sequence: list[str] = []
        self.sequence_buffer_max: int = 20

    def record_step(self, action: str, success: bool):
        """Record a step in the current sequence."""
        self.current_sequence.append(action)
        if len(self.current_sequence) > self.sequence_buffer_max:
            self.current_sequence = self.current_sequence[-self.sequence_buffer_max:]

    def commit_sequence(self, name: str, reward: float):
        """Save current sequence if it was successful."""
        if len(self.current_sequence) < 2:
            return

        if name not in self.sequences:
            self.sequences[name] = {
                "steps": list(self.current_sequence),
                "times_used": 0,
                "avg_reward": reward,
            }
        else:
            seq = self.sequences[name]
            seq["times_used"] += 1
            seq["avg_reward"] = seq["avg_reward"] * 0.8 + reward * 0.2

        self.current_sequence.clear()

    def get_sequence(self, name: str) -> list[str]:
        """Retrieve a learned sequence."""
        seq = self.sequences.get(name)
        return list(seq["steps"]) if seq else []

    def suggest_next_step(self, current_steps: list[str]) -> str:
        """Given current steps, predict the next step from learned sequences."""
        if not current_steps:
            return ""

        for name, seq in self.sequences.items():
            steps = seq["steps"]
            # Check if current steps match the beginning of a known sequence
            if len(current_steps) < len(steps):
                match = True
                for i, step in enumerate(current_steps):
                    if i >= len(steps) or steps[i] != step:
                        match = False
                        break
                if match and len(current_steps) < len(steps):
                    return steps[len(current_steps)]

        return ""


class Cerebellum:
    """
    The complete cerebellum — coordination, timing, prediction, sequences.

    Key computations:
    1. Forward model: predict action outcomes
    2. Error correction: compare prediction vs reality
    3. Sequence learning: memorize successful action sequences
    4. Timing: coordinate multi-step procedures
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.neurochem = neurochem
        self.cluster = NeuronCluster("cerebellum", size=128, excitatory_ratio=0.85)

        # Purkinje cells for different functional modules
        self.purkinje_cells: list[PurkinjeCell] = [
            PurkinjeCell(f"pc_{i}") for i in range(16)
        ]

        self.forward_model = ForwardModel()
        self.sequence_memory = SequenceMemory()

        # Timing system
        self.internal_clock: float = 0.0
        self.tempo: float = 1.0  # processing speed multiplier

    def predict_outcome(self, action: str, context: dict = None) -> dict:
        """Predict what will happen if this action is taken."""
        return self.forward_model.predict(action, context or {})

    def process_outcome(self, action: str, outcome: dict) -> dict:
        """
        Process actual outcome — learn from prediction errors.

        This drives cerebellar learning:
        1. Compare prediction to actual
        2. Compute error
        3. Update forward model
        4. Adjust Purkinje cell weights
        5. Record in sequence memory
        """
        # Get prediction error
        prediction = self.forward_model.predict(action, {})
        predicted_success = prediction["predicted_success"]
        actual_success = 1.0 if outcome.get("success", False) else 0.0
        error = actual_success - predicted_success

        # Update forward model
        self.forward_model.update(action, outcome)

        # Train Purkinje cells with error signal
        input_pattern = np.random.uniform(0, 0.5, 64)  # context encoding
        for pc in self.purkinje_cells:
            pc.learn_from_error(error, input_pattern)

        # Record in sequence memory
        self.sequence_memory.record_step(action, outcome.get("success", False))

        return {
            "prediction_error": error,
            "model_updated": True,
            "model_accuracy": self.forward_model.prediction_accuracy,
        }

    def suggest_next_action(self, current_actions: list[str]) -> str:
        """Based on sequence memory, suggest what to do next."""
        return self.sequence_memory.suggest_next_step(current_actions)

    def save_procedure(self, name: str, reward: float):
        """Save the current action sequence as a learned procedure."""
        self.sequence_memory.commit_sequence(name, reward)

    def get_state(self) -> dict:
        return {
            "prediction_accuracy": self.forward_model.prediction_accuracy,
            "forward_models_learned": len(self.forward_model.models),
            "sequences_learned": len(self.sequence_memory.sequences),
            "purkinje_cells": len(self.purkinje_cells),
            "activity": self.cluster.get_activity(),
        }
