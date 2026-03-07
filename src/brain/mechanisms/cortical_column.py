"""
Cortical Columns - The fundamental processing unit of the neocortex.

In the real brain:
- The neocortex is organized in columns (~0.5mm diameter, ~2mm tall)
- Each column has 6 layers with specific functions:
  - Layer 1: Feedback/attention (top-down)
  - Layer 2/3: Lateral connections, association, conscious access
  - Layer 4: Primary input (thalamic input arrives here)
  - Layer 5: Primary output (sends to subcortical structures)
  - Layer 6: Feedback to thalamus (top-down predictions)
- ~150,000 columns in the human neocortex
- Each column has ~10,000 neurons
- Columns are organized into "minicolumns" (~80-100 neurons)

The column is a pattern recognizer:
- Learns to recognize specific patterns in its input
- Reports matches via Layer 2/3 (conscious) and Layer 5 (output)
- Sends predictions back via Layer 6
- This is the basis of Jeff Hawkins' "Thousand Brains Theory"

For Manas:
- Scalable pattern recognition units
- Hierarchical processing (columns of columns)
- Temporal memory (sequences of patterns)
- Voting: multiple columns vote on interpretations
"""

import numpy as np
from ..neuron import NeuronCluster
from typing import Optional


class CorticalLayer:
    """A single layer within a cortical column."""

    def __init__(self, name: str, size: int, role: str):
        self.name = name
        self.size = size
        self.role = role
        self.cluster = NeuronCluster(f"layer_{name}", size=size, excitatory_ratio=0.8)
        self.activity: float = 0.0

    def process(self, input_pattern: np.ndarray, modulation: float = 1.0) -> np.ndarray:
        """Process input through this layer."""
        scaled = input_pattern[:self.size] * modulation if len(input_pattern) >= self.size else np.pad(
            input_pattern * modulation, (0, max(0, self.size - len(input_pattern)))
        )
        self.cluster.stimulate(scaled)
        self.activity = self.cluster.get_activity()
        return scaled


class CorticalColumn:
    """
    A single cortical column — the canonical computation unit.

    6-layer structure:
    Layer 1: Top-down attention
    Layer 2/3: Association, lateral, conscious access
    Layer 4: Input (thalamic)
    Layer 5: Output (to subcortical)
    Layer 6: Feedback to thalamus (predictions)
    """

    def __init__(self, column_id: str, minicolumn_count: int = 4, neurons_per_mini: int = 16):
        self.column_id = column_id
        self.total_neurons = minicolumn_count * neurons_per_mini

        # 6 layers
        layer_sizes = {
            "L1": max(4, self.total_neurons // 16),      # Attention
            "L2_3": max(8, self.total_neurons // 4),      # Association
            "L4": max(8, self.total_neurons // 4),        # Input
            "L5": max(8, self.total_neurons // 4),        # Output
            "L6": max(4, self.total_neurons // 8),        # Feedback
        }

        self.layers = {
            "L1": CorticalLayer("L1", layer_sizes["L1"], "attention"),
            "L2_3": CorticalLayer("L2_3", layer_sizes["L2_3"], "association"),
            "L4": CorticalLayer("L4", layer_sizes["L4"], "input"),
            "L5": CorticalLayer("L5", layer_sizes["L5"], "output"),
            "L6": CorticalLayer("L6", layer_sizes["L6"], "feedback"),
        }

        # Pattern memory (what this column recognizes)
        self.learned_patterns: list[np.ndarray] = []
        self.max_patterns: int = 50
        self.recognition_threshold: float = 0.7

        # Temporal context (sequence memory)
        self.temporal_context: np.ndarray = np.zeros(layer_sizes["L2_3"])
        self.sequence_memory: list[list[np.ndarray]] = []

        # Column state
        self.is_active: bool = False
        self.match_score: float = 0.0
        self.prediction: np.ndarray = np.zeros(layer_sizes["L4"])

    def process_input(
        self,
        feedforward: np.ndarray,
        feedback: Optional[np.ndarray] = None,
        attention: float = 1.0,
    ) -> dict:
        """
        Process one cycle through the column:

        1. L4 receives feedforward input (from thalamus/lower column)
        2. L2/3 combines with context and checks for pattern match
        3. L1 applies attentional modulation
        4. L5 generates output if pattern matches
        5. L6 generates prediction for next input
        """
        # 1. Input layer receives feedforward
        l4_output = self.layers["L4"].process(feedforward, modulation=1.0)

        # 2. Association layer combines input with temporal context
        combined = np.concatenate([
            l4_output[:self.layers["L2_3"].size // 2],
            self.temporal_context[:self.layers["L2_3"].size // 2],
        ])[:self.layers["L2_3"].size]
        l23_output = self.layers["L2_3"].process(combined)

        # Apply attention (L1)
        if feedback is not None:
            l1_output = self.layers["L1"].process(feedback[:self.layers["L1"].size], attention)
            attention_modulation = float(np.mean(l1_output)) + 0.5
        else:
            attention_modulation = attention

        # 3. Pattern recognition
        self.match_score = self._match_patterns(l4_output)
        self.is_active = self.match_score > self.recognition_threshold

        # 4. Output (L5) — fires if pattern recognized
        if self.is_active:
            l5_output = self.layers["L5"].process(
                l23_output[:self.layers["L5"].size],
                modulation=self.match_score * attention_modulation,
            )
        else:
            l5_output = np.zeros(self.layers["L5"].size)

        # 5. Prediction (L6) — what do we expect next?
        self.prediction = self._generate_prediction(l23_output)
        self.layers["L6"].process(self.prediction)

        # Update temporal context
        self.temporal_context = l23_output * 0.7 + self.temporal_context * 0.3

        return {
            "is_active": self.is_active,
            "match_score": self.match_score,
            "output": l5_output,
            "prediction": self.prediction,
            "attention": attention_modulation,
            "layer_activities": {
                name: layer.activity for name, layer in self.layers.items()
            },
        }

    def learn_pattern(self, pattern: np.ndarray):
        """Learn a new pattern (or strengthen existing one)."""
        # Check if similar pattern already known
        for i, known in enumerate(self.learned_patterns):
            similarity = self._pattern_similarity(pattern, known)
            if similarity > 0.8:
                # Strengthen existing pattern (running average)
                self.learned_patterns[i] = known * 0.8 + pattern[:len(known)] * 0.2
                return

        # New pattern
        self.learned_patterns.append(pattern.copy()[:self.layers["L4"].size])
        if len(self.learned_patterns) > self.max_patterns:
            self.learned_patterns.pop(0)

    def _match_patterns(self, input_pattern: np.ndarray) -> float:
        """Check if input matches any learned pattern."""
        if not self.learned_patterns:
            return 0.0

        best_match = 0.0
        for pattern in self.learned_patterns:
            similarity = self._pattern_similarity(input_pattern, pattern)
            best_match = max(best_match, similarity)

        return best_match

    def _pattern_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Compute similarity between two patterns (cosine similarity)."""
        min_len = min(len(a), len(b))
        a_trim = a[:min_len]
        b_trim = b[:min_len]
        norm_a = np.linalg.norm(a_trim)
        norm_b = np.linalg.norm(b_trim)
        if norm_a < 0.001 or norm_b < 0.001:
            return 0.0
        return float(np.dot(a_trim, b_trim) / (norm_a * norm_b))

    def _generate_prediction(self, context: np.ndarray) -> np.ndarray:
        """Generate a prediction about the next input based on context."""
        if not self.learned_patterns:
            return np.zeros(self.layers["L4"].size)

        # Simple prediction: weighted average of learned patterns
        # weighted by similarity to current context
        prediction = np.zeros(self.layers["L4"].size)
        total_weight = 0.0

        for pattern in self.learned_patterns:
            sim = self._pattern_similarity(context[:len(pattern)], pattern)
            prediction[:len(pattern)] += pattern * sim
            total_weight += sim

        if total_weight > 0:
            prediction /= total_weight

        return prediction

    def get_state(self) -> dict:
        return {
            "column_id": self.column_id,
            "is_active": self.is_active,
            "match_score": self.match_score,
            "patterns_learned": len(self.learned_patterns),
            "layer_activities": {
                name: layer.activity for name, layer in self.layers.items()
            },
        }


class CorticalSheet:
    """
    A sheet of cortical columns — like a cortical area.

    Multiple columns process input in parallel and vote on interpretation.
    This is the "Thousand Brains" concept: many columns each build
    a model and vote on the best interpretation.
    """

    def __init__(self, name: str, n_columns: int = 8, column_size: int = 64):
        self.name = name
        self.columns = [
            CorticalColumn(
                f"{name}_col_{i}",
                minicolumn_count=4,
                neurons_per_mini=column_size // 4,
            )
            for i in range(n_columns)
        ]

    def process(self, input_pattern: np.ndarray, attention: float = 1.0) -> dict:
        """Process input through all columns and collect votes."""
        column_results = []
        active_count = 0

        for column in self.columns:
            result = column.process_input(input_pattern, attention=attention)
            column_results.append(result)
            if result["is_active"]:
                active_count += 1

        # Voting: consensus from active columns
        consensus = active_count / max(1, len(self.columns))

        # Aggregate output from active columns
        if active_count > 0:
            outputs = [r["output"] for r in column_results if r["is_active"]]
            # Average output
            max_len = max(len(o) for o in outputs)
            padded = [np.pad(o, (0, max_len - len(o))) for o in outputs]
            aggregate_output = np.mean(padded, axis=0)
        else:
            aggregate_output = np.zeros(16)

        return {
            "active_columns": active_count,
            "total_columns": len(self.columns),
            "consensus": consensus,
            "aggregate_output": aggregate_output,
            "column_details": column_results,
        }

    def learn(self, pattern: np.ndarray):
        """All columns learn the pattern."""
        for column in self.columns:
            column.learn_pattern(pattern)

    def get_state(self) -> dict:
        return {
            "name": self.name,
            "total_columns": len(self.columns),
            "active_columns": sum(1 for c in self.columns if c.is_active),
            "total_patterns": sum(len(c.learned_patterns) for c in self.columns),
        }
