"""
Insular Cortex (Insula) - Interoception, empathy, and embodied feeling.

In the real brain:
- Interoception: awareness of internal body states (heart rate, gut feeling)
- Empathy: understanding others' emotions by simulating them internally
- Disgust: originally for contaminated food, extended to moral disgust
- Risk/uncertainty: "gut feelings" about decisions
- Self-awareness: sense of body ownership and agency
- Pain processing: both physical and social pain
- Anterior insula: subjective feeling states
- Posterior insula: raw body signals

For Manas:
- Monitors internal system state (CPU, memory, disk as "body")
- Generates "gut feelings" about actions based on internal state
- Empathy: simulates emotional impact of actions on others
- Detects "contamination" (corrupted data, security issues)
- Self-awareness: knows its own resource limits and health
"""

import numpy as np
from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class InteroceptiveSystem:
    """
    Monitors internal state — like feeling your own heartbeat.

    For Manas, internal state = system resources + brain state.
    """

    def __init__(self):
        self.body_state: dict[str, float] = {
            "energy": 1.0,       # available compute resources
            "strain": 0.0,       # how hard the system is working
            "temperature": 0.5,  # CPU heat / activity level
            "fullness": 0.5,     # memory/disk usage
            "pain": 0.0,         # errors, failures, overloads
        }
        self.homeostatic_targets: dict[str, float] = {
            "energy": 0.8,
            "strain": 0.2,
            "temperature": 0.4,
            "fullness": 0.5,
            "pain": 0.0,
        }

    def update_from_system(self, system_metrics: dict):
        """Update internal state from actual system metrics."""
        cpu = system_metrics.get("cpu_percent", 50) / 100.0
        memory = system_metrics.get("memory_percent", 50) / 100.0
        disk = system_metrics.get("disk_percent", 50) / 100.0
        error_rate = system_metrics.get("error_rate", 0.0)

        self.body_state["energy"] = 1.0 - cpu * 0.5 - memory * 0.3
        self.body_state["strain"] = cpu * 0.6 + memory * 0.4
        self.body_state["temperature"] = cpu
        self.body_state["fullness"] = (memory + disk) / 2.0
        self.body_state["pain"] = min(1.0, error_rate * 2.0)

    def get_discomfort(self) -> float:
        """
        Overall discomfort level — how far from homeostasis.

        This is the "gut feeling" — you don't know exactly what's wrong,
        but something feels off.
        """
        total_deviation = 0.0
        for key, target in self.homeostatic_targets.items():
            current = self.body_state.get(key, target)
            total_deviation += abs(current - target)
        return min(1.0, total_deviation / len(self.homeostatic_targets))

    def get_gut_feeling(self, action_context: dict) -> dict:
        """
        Generate a "gut feeling" about a proposed action.

        Based on internal state: if you're already strained,
        risky actions feel worse.
        """
        discomfort = self.get_discomfort()
        strain = self.body_state["strain"]
        energy = self.body_state["energy"]

        # More strained -> more cautious
        risk_aversion = strain * 0.5 + discomfort * 0.3

        # Less energy -> avoid demanding tasks
        capacity_concern = max(0, 0.5 - energy) * 0.5

        feeling_valence = energy * 0.3 - strain * 0.3 - discomfort * 0.2

        return {
            "valence": np.clip(feeling_valence, -1.0, 1.0),
            "risk_aversion": risk_aversion,
            "capacity_concern": capacity_concern,
            "confidence": 1.0 - discomfort,
            "discomfort": discomfort,
        }


class EmpathySystem:
    """
    Simulates emotional impact of actions on others.

    The insula enables empathy by mirroring others' emotional states internally.
    For Manas: considers how actions affect the user and system.
    """

    def __init__(self):
        self.empathy_level: float = 0.7  # how much we weight others' experience
        self.user_model: dict[str, float] = {
            "satisfaction": 0.5,
            "frustration": 0.0,
            "trust": 0.5,
            "engagement": 0.5,
        }

    def simulate_impact(self, action: str, context: dict) -> dict:
        """
        Simulate how an action might affect the user.

        Mirror the user's likely emotional response internally.
        """
        user_impact = 0.0
        reasons = []

        # Success/failure impact
        if context.get("likely_success", True):
            user_impact += 0.3
            reasons.append("user_happy_with_success")
        else:
            user_impact -= 0.4
            reasons.append("user_frustrated_by_failure")

        # Destructive actions cause user distress
        destructive_keywords = ["delete", "remove", "drop", "destroy", "reset"]
        if any(kw in action.lower() for kw in destructive_keywords):
            user_impact -= 0.3
            reasons.append("destructive_action_risk")

        # Helpful actions make user happy
        helpful_keywords = ["help", "fix", "create", "build", "setup"]
        if any(kw in action.lower() for kw in helpful_keywords):
            user_impact += 0.2
            reasons.append("helpful_action")

        # Modulate by empathy level
        user_impact *= self.empathy_level

        return {
            "predicted_user_impact": np.clip(user_impact, -1.0, 1.0),
            "reasons": reasons,
            "user_model": dict(self.user_model),
        }

    def update_user_model(self, feedback_valence: float):
        """Update our model of the user based on their feedback."""
        if feedback_valence > 0:
            self.user_model["satisfaction"] = min(1.0, self.user_model["satisfaction"] + 0.1)
            self.user_model["frustration"] = max(0.0, self.user_model["frustration"] - 0.1)
            self.user_model["trust"] = min(1.0, self.user_model["trust"] + 0.05)
        else:
            self.user_model["satisfaction"] = max(0.0, self.user_model["satisfaction"] - 0.1)
            self.user_model["frustration"] = min(1.0, self.user_model["frustration"] + 0.15)
            self.user_model["trust"] = max(0.0, self.user_model["trust"] - 0.05)


class DisgustSystem:
    """
    Disgust detection — contamination avoidance.

    Originally for avoiding rotten food. Extended to:
    - Data contamination (corrupted files, injection attacks)
    - Moral disgust (unethical actions)
    - Code smell (bad patterns, antipatterns)
    """

    def __init__(self):
        self.contamination_patterns: list[dict] = [
            {"pattern": "injection", "type": "security", "severity": 0.8},
            {"pattern": "corrupted", "type": "data", "severity": 0.7},
            {"pattern": "malware", "type": "security", "severity": 0.9},
            {"pattern": "backdoor", "type": "security", "severity": 0.9},
            {"pattern": "hardcoded password", "type": "code_smell", "severity": 0.7},
            {"pattern": "eval(", "type": "code_smell", "severity": 0.5},
            {"pattern": "goto", "type": "code_smell", "severity": 0.3},
        ]

    def evaluate(self, content: str) -> dict:
        """Evaluate content for contamination/disgust."""
        disgust_level = 0.0
        triggers = []

        content_lower = content.lower()
        for pattern in self.contamination_patterns:
            if pattern["pattern"] in content_lower:
                disgust_level = max(disgust_level, pattern["severity"])
                triggers.append(pattern)

        return {
            "disgust_level": disgust_level,
            "is_disgusting": disgust_level > 0.5,
            "triggers": triggers,
            "response": "reject" if disgust_level > 0.7 else "caution" if disgust_level > 0.3 else "clean",
        }


class Insula:
    """
    The complete insular cortex — interoception, empathy, disgust, gut feelings.

    Integrates internal body state with emotional processing.
    Creates the subjective "feeling" of being in a particular state.
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.neurochem = neurochem
        self.cluster = NeuronCluster("insula", size=64, excitatory_ratio=0.75)

        self.interoception = InteroceptiveSystem()
        self.empathy = EmpathySystem()
        self.disgust = DisgustSystem()

        self.subjective_feeling: str = "neutral"
        self.feeling_intensity: float = 0.0

    def process(self, action: str = "", context: dict = None, system_metrics: dict = None) -> dict:
        """
        Full insular processing:
        1. Update internal body state
        2. Generate gut feeling
        3. Check for disgust
        4. Simulate empathy
        5. Derive subjective feeling
        """
        context = context or {}

        # 1. Update body state
        if system_metrics:
            self.interoception.update_from_system(system_metrics)

        # 2. Gut feeling
        gut = self.interoception.get_gut_feeling(context)

        # 3. Disgust check
        disgust = self.disgust.evaluate(action) if action else {"disgust_level": 0.0, "is_disgusting": False}

        # 4. Empathy
        empathy = self.empathy.simulate_impact(action, context) if action else {"predicted_user_impact": 0.0}

        # 5. Derive subjective feeling
        discomfort = self.interoception.get_discomfort()
        disgust_level = disgust["disgust_level"]
        user_impact = empathy["predicted_user_impact"]

        # Subjective feeling emerges from all inputs
        if disgust_level > 0.6:
            self.subjective_feeling = "disgust"
            self.feeling_intensity = disgust_level
            self.neurochem.trigger_event("threat", disgust_level * 0.5)
        elif discomfort > 0.6:
            self.subjective_feeling = "unease"
            self.feeling_intensity = discomfort
            self.neurochem.trigger_event("threat", discomfort * 0.3)
        elif user_impact < -0.3:
            self.subjective_feeling = "concern"
            self.feeling_intensity = abs(user_impact)
        elif gut["valence"] > 0.3:
            self.subjective_feeling = "well-being"
            self.feeling_intensity = gut["valence"]
        else:
            self.subjective_feeling = "neutral"
            self.feeling_intensity = 0.2

        return {
            "gut_feeling": gut,
            "disgust": disgust,
            "empathy": empathy,
            "subjective_feeling": self.subjective_feeling,
            "feeling_intensity": self.feeling_intensity,
            "body_state": dict(self.interoception.body_state),
            "discomfort": discomfort,
        }

    def get_state(self) -> dict:
        return {
            "subjective_feeling": self.subjective_feeling,
            "feeling_intensity": self.feeling_intensity,
            "body_state": dict(self.interoception.body_state),
            "discomfort": self.interoception.get_discomfort(),
            "user_model": dict(self.empathy.user_model),
            "activity": self.cluster.get_activity(),
        }
