"""
Sensory Processor - Converts raw input into neural patterns.

In the real brain:
- Sensory cortex converts raw signals (light, sound, touch) into neural patterns
- These patterns flow to other brain regions for processing

For Manas:
- Converts text input into spike patterns for the spiking network
- Converts command output into patterns
- Converts internet data into patterns
- Encodes importance/urgency/novelty into the signal
"""

import numpy as np
import hashlib


class SensoryProcessor:
    """
    Converts external inputs (text, data) into neural spike patterns.

    This is the interface between the outside world and the spiking brain.
    """

    def __init__(self, output_size: int = 128):
        self.output_size = output_size
        self.known_patterns: dict[str, np.ndarray] = {}

    def encode_text(self, text: str) -> np.ndarray:
        """
        Convert text into a neural activation pattern.

        Uses character-level hashing to create a distributed representation.
        Novel text produces different patterns than familiar text.
        """
        pattern = np.zeros(self.output_size)

        # Character-level encoding (like how visual cortex processes letters)
        for i, char in enumerate(text[:self.output_size]):
            # Each character activates a set of neurons
            char_hash = int(hashlib.md5(f"{char}_{i}".encode()).hexdigest()[:8], 16)
            neuron_indices = [
                char_hash % self.output_size,
                (char_hash * 31) % self.output_size,
                (char_hash * 97) % self.output_size,
            ]
            for idx in neuron_indices:
                pattern[idx] += ord(char) / 255.0

        # Word-level features
        words = text.lower().split()
        for word in words:
            word_hash = int(hashlib.md5(word.encode()).hexdigest()[:8], 16)
            idx = word_hash % self.output_size
            pattern[idx] += 0.3

        # Normalize to 0-1 range
        if pattern.max() > 0:
            pattern = pattern / pattern.max()

        return pattern

    def encode_command_result(self, result: str, exit_code: int) -> np.ndarray:
        """
        Encode a shell command result into a neural pattern.

        Success/failure is encoded as a distinct signal component.
        """
        pattern = self.encode_text(result[:500])

        # Encode success/failure prominently
        if exit_code == 0:
            # Success pattern: activate first quarter
            pattern[:self.output_size // 4] += 0.3
        else:
            # Failure pattern: activate last quarter
            pattern[-(self.output_size // 4):] += 0.5

        # Error keywords amplify danger signal
        error_words = ["error", "fail", "denied", "fatal", "crash", "killed"]
        text_lower = result.lower()
        for word in error_words:
            if word in text_lower:
                # Spread activation in danger-associated neurons
                pattern[self.output_size // 2:] += 0.2

        return np.clip(pattern, 0.0, 1.0)

    def detect_novelty(self, pattern: np.ndarray) -> float:
        """
        How novel is this pattern compared to what we've seen?

        Novel stimuli trigger curiosity (dopamine) and attention (norepinephrine).
        """
        if not self.known_patterns:
            return 1.0  # everything is novel at first

        # Compare to stored patterns
        min_distance = float("inf")
        for stored in self.known_patterns.values():
            dist = np.linalg.norm(pattern - stored)
            min_distance = min(min_distance, dist)

        novelty = min(1.0, min_distance / 5.0)
        return novelty

    def learn_pattern(self, label: str, pattern: np.ndarray):
        """Store a pattern as familiar."""
        self.known_patterns[label] = pattern.copy()
        # Keep only recent patterns (bounded memory)
        if len(self.known_patterns) > 500:
            oldest_key = next(iter(self.known_patterns))
            del self.known_patterns[oldest_key]
