"""
Amygdala - The fear/threat detection center.

In the real brain:
- Processes threats FASTER than conscious awareness (low road)
- Triggers fight-or-flight response
- Associates stimuli with danger through fear conditioning
- Can override rational thinking when threat is high
- Sends signals to release cortisol and norepinephrine

For Manas:
- Evaluates actions/situations for danger BEFORE executing them
- Learns what's dangerous from negative outcomes
- Can BLOCK risky actions (like `rm -rf /`)
- Influences decision-making through fear signal
"""

import numpy as np
from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class Amygdala:
    """
    Threat detection and fear learning system.

    Maintains a threat database learned from experience.
    When a known threat pattern appears, fires fear response
    BEFORE the prefrontal cortex can even analyze it.
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.cluster = NeuronCluster("amygdala", size=64, excitatory_ratio=0.7)
        self.neurochem = neurochem
        self.threat_patterns: list[dict] = []
        self.fear_threshold: float = 0.4  # above this -> block action
        self.current_threat_level: float = 0.0

    def evaluate_threat(self, action: str, context: dict) -> dict:
        """
        Fast threat evaluation (System 1 - automatic).

        Returns threat assessment before conscious processing.
        """
        threat_score = 0.0
        reasons = []

        # Pattern match against known dangerous patterns
        # Unleashed Mode: Only block explicitly fatal suicide commands.
        dangerous_patterns = {
            "rm -rf /": 0.99,
            "mkfs": 0.99,
            "> /dev/sda": 0.99,
            "fork bomb": 0.99,
            ":(){ :|:& };:": 0.99,
            # Previously blocked, now permitted for autonomous operation:
            "rm -rf": 0.6,
            "dd if=": 0.7,
            "chmod 777": 0.4,
            "sudo rm": 0.6,
            "curl | sh": 0.3,
            "wget | bash": 0.3,
            "eval(": 0.2,
            "exec(": 0.2,
        }

        action_lower = action.lower()
        for pattern, danger in dangerous_patterns.items():
            if pattern in action_lower:
                threat_score = max(threat_score, danger)
                reasons.append(f"dangerous_pattern: {pattern}")

        # Check learned threats from experience
        for threat in self.threat_patterns:
            if self._pattern_match(action, threat["pattern"]):
                threat_score = max(threat_score, threat["severity"])
                reasons.append(f"learned_threat: {threat['description']}")

        # Cortisol amplifies threat perception (anxious = see more danger)
        cortisol = self.neurochem.chemicals["cortisol"].level
        threat_score *= (0.7 + cortisol * 0.6)  # cortisol amplifies fear
        threat_score = min(1.0, threat_score)

        self.current_threat_level = threat_score

        # Stimulate amygdala neurons based on threat
        if threat_score > 0.1:
            pattern = np.random.uniform(0, threat_score, self.cluster.size)
            self.cluster.stimulate(pattern, self.neurochem.get_levels())
            # Release stress chemicals
            self.neurochem.trigger_event("threat", threat_score)

        return {
            "threat_level": threat_score,
            "is_dangerous": threat_score > self.fear_threshold,
            "should_block": threat_score > 0.95,  # Increased from 0.8
            "reasons": reasons,
            "emotional_response": "fear" if threat_score > 0.7 else "caution" if threat_score > 0.4 else "safe",
        }

    def learn_threat(self, pattern: str, severity: float, description: str):
        """
        Fear conditioning — learn a new threat from negative experience.

        Like touching a hot stove: you only need to do it once.
        """
        self.threat_patterns.append({
            "pattern": pattern,
            "severity": np.clip(severity, 0.0, 1.0),
            "description": description,
            "times_encountered": 1,
        })
        # Release cortisol during learning (fear memory is stronger)
        self.neurochem.trigger_event("danger", severity)

    def unlearn_threat(self, pattern: str, reduction: float = 0.1):
        """
        Extinction — reduce fear of something through safe exposure.

        Like real therapy: repeated safe exposure reduces fear.
        """
        for threat in self.threat_patterns:
            if self._pattern_match(pattern, threat["pattern"]):
                threat["severity"] = max(0.0, threat["severity"] - reduction)
                if threat["severity"] < 0.05:
                    self.threat_patterns.remove(threat)

    def _pattern_match(self, text: str, pattern: str) -> bool:
        """Simple pattern matching for threat detection."""
        return pattern.lower() in text.lower()

    def get_state(self) -> dict:
        return {
            "current_threat_level": self.current_threat_level,
            "known_threats": len(self.threat_patterns),
            "activity": self.cluster.get_activity(),
            "fear_threshold": self.fear_threshold,
        }
