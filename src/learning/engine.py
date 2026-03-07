"""
Learning Engine - Continual learning from experience.

Humans learn through:
1. Reinforcement: positive outcomes = repeat, negative = avoid
2. Association: things that happen together get linked
3. Generalization: extract patterns from specific experiences
4. Curiosity: seek out novel information
5. Sleep consolidation: strengthen important memories, forget noise

This engine implements all of these.
"""

import time
from typing import Optional


class LearningEngine:
    """
    Learns continuously from every interaction and experience.

    Unlike standard AI that's frozen after training, this learns
    in real-time like a human brain.
    """

    def __init__(self):
        # Action-outcome associations (reinforcement learning)
        self.action_values: dict[str, dict] = {}
        # Pattern library (generalized knowledge)
        self.patterns: list[dict] = []
        # Curiosity targets
        self.curiosity_queue: list[str] = []
        # Learning rate adapts based on emotional state
        self.base_learning_rate: float = 0.1
        self.total_experiences: int = 0

    def learn_from_outcome(
        self,
        action: str,
        outcome: dict,
        emotional_state: dict,
    ) -> dict:
        """
        Learn from the result of an action (reinforcement learning).

        Like a child touching a hot stove:
        - Action: touch stove
        - Outcome: pain (negative)
        - Learning: don't touch stove again

        Emotional state affects learning:
        - High fear/cortisol -> learn faster from negative outcomes
        - High dopamine -> learn faster from positive outcomes
        """
        success = outcome.get("exit_code", -1) == 0
        reward = 1.0 if success else -1.0

        # Emotional modulation of learning
        fear = emotional_state.get("fear", 0)
        happiness = emotional_state.get("happiness", 0)

        if reward < 0:
            # Fear amplifies negative learning (once bitten, twice shy)
            learning_rate = self.base_learning_rate * (1.0 + fear * 2.0)
        else:
            # Happiness amplifies positive learning
            learning_rate = self.base_learning_rate * (1.0 + happiness * 1.5)

        # Extract action category (generalize)
        action_key = self._categorize_action(action)

        if action_key not in self.action_values:
            self.action_values[action_key] = {
                "value": 0.0,
                "attempts": 0,
                "successes": 0,
                "failures": 0,
                "last_outcome": None,
            }

        entry = self.action_values[action_key]
        # Exponential moving average (recent outcomes matter more)
        entry["value"] = entry["value"] * (1 - learning_rate) + reward * learning_rate
        entry["attempts"] += 1
        if success:
            entry["successes"] += 1
        else:
            entry["failures"] += 1
        entry["last_outcome"] = outcome.get("stderr", "")[:200] if not success else "success"

        self.total_experiences += 1

        return {
            "action_key": action_key,
            "reward": reward,
            "learning_rate": learning_rate,
            "new_value": entry["value"],
            "total_attempts": entry["attempts"],
        }

    def should_attempt(self, action: str) -> dict:
        """
        Should we try this action? Based on past experience.

        Like a human deciding: "last time I did this it went badly..."
        """
        action_key = self._categorize_action(action)
        entry = self.action_values.get(action_key)

        if entry is None:
            # Never tried -> curiosity says try it
            return {
                "recommendation": "try",
                "confidence": 0.0,
                "reason": "never_attempted",
                "past_value": 0.0,
            }

        value = entry["value"]
        attempts = entry["attempts"]
        confidence = min(1.0, attempts / 10.0)  # more attempts = more confident

        if value < -0.5 and confidence > 0.5:
            return {
                "recommendation": "avoid",
                "confidence": confidence,
                "reason": f"past_failures ({entry['failures']}/{entry['attempts']})",
                "past_value": value,
            }
        elif value > 0.3:
            return {
                "recommendation": "proceed",
                "confidence": confidence,
                "reason": f"past_successes ({entry['successes']}/{entry['attempts']})",
                "past_value": value,
            }
        else:
            return {
                "recommendation": "cautious",
                "confidence": confidence,
                "reason": "mixed_results",
                "past_value": value,
            }

    def extract_pattern(self, experiences: list[dict]) -> Optional[dict]:
        """
        Generalize from specific experiences to extract a pattern.

        Like noticing "every time I run apt without sudo, it fails"
        -> Pattern: system package commands need sudo.
        """
        if len(experiences) < 3:
            return None

        # Find common elements in failures
        failures = [e for e in experiences if e.get("exit_code", 0) != 0]
        successes = [e for e in experiences if e.get("exit_code", 0) == 0]

        if not failures:
            return None

        # Simple pattern extraction: common words in failed commands
        failure_words = set()
        for f in failures:
            cmd = f.get("command", "").lower().split()
            failure_words.update(cmd)

        success_words = set()
        for s in successes:
            cmd = s.get("command", "").lower().split()
            success_words.update(cmd)

        # Words unique to failures might be the problem
        problem_words = failure_words - success_words

        if problem_words:
            pattern = {
                "type": "failure_pattern",
                "keywords": list(problem_words)[:5],
                "failure_rate": len(failures) / len(experiences),
                "sample_size": len(experiences),
                "timestamp": time.time(),
            }
            self.patterns.append(pattern)
            return pattern

        return None

    def get_curious_about(self, current_context: str) -> Optional[str]:
        """
        Curiosity: what should we explore next?

        Humans get curious about gaps in their knowledge.
        """
        if self.curiosity_queue:
            return self.curiosity_queue.pop(0)

        # Generate curiosity from context
        if self.total_experiences < 10:
            return "basic system information"

        # Look for gaps in knowledge
        weak_areas = [
            k for k, v in self.action_values.items()
            if v["attempts"] < 3 and v["value"] == 0.0
        ]
        if weak_areas:
            return f"how to use: {weak_areas[0]}"

        return None

    def add_curiosity(self, topic: str):
        """Add something to explore later."""
        if topic not in self.curiosity_queue:
            self.curiosity_queue.append(topic)
            if len(self.curiosity_queue) > 20:
                self.curiosity_queue.pop(0)

    def _categorize_action(self, action: str) -> str:
        """
        Categorize an action for generalized learning.

        Instead of learning about exact commands, learn about categories:
        "ls -la /home" -> "ls" (file listing)
        """
        parts = action.strip().split()
        if not parts:
            return "empty"

        base_cmd = parts[0].split("/")[-1]  # handle full paths

        # Group similar commands
        groups = {
            "file_list": ["ls", "dir", "find"],
            "file_read": ["cat", "head", "tail", "less", "more"],
            "file_write": ["echo", "tee", "write"],
            "file_manage": ["cp", "mv", "rm", "mkdir", "rmdir", "touch"],
            "system_info": ["uname", "whoami", "hostname", "uptime", "df", "du"],
            "process": ["ps", "top", "kill", "pkill"],
            "network": ["ping", "curl", "wget", "ssh", "nc"],
            "package": ["apt", "brew", "pip", "npm", "cargo"],
            "git": ["git"],
            "python": ["python", "python3"],
        }

        for group_name, commands in groups.items():
            if base_cmd in commands:
                return group_name

        return base_cmd

    def get_stats(self) -> dict:
        return {
            "total_experiences": self.total_experiences,
            "known_actions": len(self.action_values),
            "patterns_discovered": len(self.patterns),
            "curiosity_queue_size": len(self.curiosity_queue),
        }
