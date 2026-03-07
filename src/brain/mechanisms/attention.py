"""
Attention System - Selective, sustained, and divided attention.

In the real brain:
- Selective attention: focus on one thing, ignore others (cocktail party effect)
- Sustained attention: maintain focus over time (vigilance)
- Divided attention: split focus between tasks (limited capacity)
- Bottom-up (exogenous): stimulus-driven (loud noise grabs attention)
- Top-down (endogenous): goal-driven (looking for your keys)
- Attentional spotlight: enhances processing in focused area
- Inhibition of return: don't keep attending to same thing
- Attentional blink: brief blindness after processing something important

Neural basis:
- Dorsal attention network: top-down, voluntary
- Ventral attention network: bottom-up, stimulus-driven
- Pulvinar (thalamus): routes attention between cortical areas
- ACC: detects when attention needs to shift

For Manas:
- Manages what gets processed deeply vs superficially
- Allocates limited processing resources
- Can be captured by salient/novel/threatening stimuli
- Top-down goals direct attention to relevant information
"""

import time
import numpy as np


class AttentionalSpotlight:
    """
    The focus of attention — what's being deeply processed right now.

    Attention is a limited resource. Only a few things can be
    in the spotlight at once (capacity ~4 items).
    """

    def __init__(self, capacity: int = 4):
        self.capacity = capacity
        self.focused_items: list[dict] = []
        self.focus_start_times: dict[str, float] = {}
        self.total_attention: float = 1.0
        self.attention_fatigue: float = 0.0

    def focus_on(self, item_id: str, salience: float, source: str = "top_down") -> bool:
        """
        Bring an item into the attentional spotlight.

        Returns True if successfully focused (has capacity).
        """
        # Check if already focused
        for item in self.focused_items:
            if item["id"] == item_id:
                item["salience"] = max(item["salience"], salience)
                return True

        # Check capacity
        if len(self.focused_items) >= self.capacity:
            # Kick out lowest salience item
            self.focused_items.sort(key=lambda x: x["salience"])
            if salience > self.focused_items[0]["salience"]:
                removed = self.focused_items.pop(0)
                self.focus_start_times.pop(removed["id"], None)
            else:
                return False  # Not salient enough

        self.focused_items.append({
            "id": item_id,
            "salience": salience,
            "source": source,
            "start_time": time.time(),
        })
        self.focus_start_times[item_id] = time.time()
        return True

    def get_attention_weight(self, item_id: str) -> float:
        """How much attention is an item getting? (0 to 1)"""
        for item in self.focused_items:
            if item["id"] == item_id:
                # Attention decays over time (habituation)
                duration = time.time() - item["start_time"]
                decay = np.exp(-duration / 30.0)  # 30s half-life
                return item["salience"] * decay * (1.0 - self.attention_fatigue * 0.5)
        return 0.0  # Not in spotlight

    def update(self):
        """Update spotlight — remove habituated items."""
        now = time.time()
        self.focused_items = [
            item for item in self.focused_items
            if (now - item["start_time"]) < 120.0  # max 2 min focus without refresh
        ]

        # Fatigue increases with sustained focus
        if self.focused_items:
            self.attention_fatigue = min(1.0, self.attention_fatigue + 0.005)
        else:
            self.attention_fatigue = max(0.0, self.attention_fatigue - 0.02)

    def clear(self):
        """Release all attention (mind-wandering)."""
        self.focused_items.clear()
        self.focus_start_times.clear()


class SalienceComputer:
    """
    Computes how attention-grabbing something is (bottom-up salience).

    Salient things capture attention automatically:
    - Novel stimuli (never seen before)
    - Threatening stimuli (danger words)
    - Emotionally charged content
    - Sudden changes (onset/offset)
    - Personal relevance
    """

    def __init__(self):
        self.recent_stimuli: list[str] = []
        self.threat_words = {
            "error", "fail", "crash", "danger", "warning", "critical",
            "kill", "delete", "destroy", "hack", "attack", "breach",
        }
        self.reward_words = {
            "success", "complete", "reward", "done", "perfect", "excellent",
            "found", "created", "fixed", "solved",
        }

    def compute(self, stimulus: str, context: dict = None) -> float:
        """Compute bottom-up salience of a stimulus."""
        context = context or {}
        salience = 0.0

        stimulus_lower = stimulus.lower()
        words = set(stimulus_lower.split())

        # Novelty (not seen recently)
        if stimulus not in self.recent_stimuli:
            salience += 0.3
        self.recent_stimuli.append(stimulus)
        if len(self.recent_stimuli) > 100:
            self.recent_stimuli = self.recent_stimuli[-50:]

        # Threat detection (automatic, fast)
        threat_matches = words & self.threat_words
        if threat_matches:
            salience += 0.4 * len(threat_matches)

        # Reward detection
        reward_matches = words & self.reward_words
        if reward_matches:
            salience += 0.2 * len(reward_matches)

        # Emotional intensity from context
        emotional_intensity = context.get("emotional_intensity", 0.0)
        salience += emotional_intensity * 0.3

        # Length (very short or very long = more salient)
        length = len(stimulus)
        if length < 10 or length > 500:
            salience += 0.1

        return min(1.0, salience)


class AttentionSystem:
    """
    The complete attention system.

    Integrates:
    - Bottom-up salience (stimulus-driven)
    - Top-down goals (voluntary focus)
    - Attentional spotlight (limited capacity)
    - Inhibition of return
    - Fatigue/vigilance
    """

    def __init__(self):
        self.spotlight = AttentionalSpotlight(capacity=4)
        self.salience_computer = SalienceComputer()

        # Top-down attention goals
        self.goals: list[dict] = []
        self.goal_weights: dict[str, float] = {}

        # Inhibition of return (don't re-attend recently processed)
        self.inhibited: dict[str, float] = {}

        # Vigilance / sustained attention
        self.vigilance: float = 1.0
        self.time_on_task: float = 0.0

    def process(self, stimuli: list[dict], goals: list[str] = None) -> dict:
        """
        Main attention processing:
        1. Compute salience of all stimuli (bottom-up)
        2. Apply goal-directed bias (top-down)
        3. Apply inhibition of return
        4. Select what enters the spotlight
        """
        if goals:
            self.goals = [{"goal": g, "priority": 1.0 - i * 0.1} for i, g in enumerate(goals)]

        attended = []
        ignored = []

        for stimulus in stimuli:
            stim_id = stimulus.get("id", stimulus.get("content", "")[:50])
            content = stimulus.get("content", "")
            context = stimulus.get("context", {})

            # 1. Bottom-up salience
            salience = self.salience_computer.compute(content, context)

            # 2. Top-down goal relevance
            goal_boost = 0.0
            for goal in self.goals:
                if any(word in content.lower() for word in goal["goal"].lower().split()):
                    goal_boost += goal["priority"] * 0.3

            # 3. Inhibition of return
            ior_penalty = self.inhibited.get(stim_id, 0.0)

            # Final attention score
            final_score = (salience + goal_boost) * self.vigilance - ior_penalty

            # 4. Try to enter spotlight
            if final_score > 0.2:
                source = "bottom_up" if salience > goal_boost else "top_down"
                if self.spotlight.focus_on(stim_id, final_score, source):
                    attended.append({
                        "id": stim_id,
                        "score": final_score,
                        "salience": salience,
                        "goal_boost": goal_boost,
                        "source": source,
                    })
                    # Mark for inhibition of return
                    self.inhibited[stim_id] = 0.2
                else:
                    ignored.append(stim_id)
            else:
                ignored.append(stim_id)

        # Decay inhibition of return
        self.inhibited = {
            k: max(0, v - 0.05) for k, v in self.inhibited.items() if v > 0.01
        }

        # Update vigilance
        self.time_on_task += 1
        self.vigilance = max(0.3, 1.0 - self.time_on_task * 0.002)

        self.spotlight.update()

        return {
            "attended": attended,
            "ignored_count": len(ignored),
            "spotlight_items": len(self.spotlight.focused_items),
            "vigilance": self.vigilance,
            "attention_fatigue": self.spotlight.attention_fatigue,
        }

    def set_goal(self, goal: str, priority: float = 1.0):
        """Set a top-down attention goal."""
        self.goals.append({"goal": goal, "priority": priority})
        if len(self.goals) > 5:
            self.goals = sorted(self.goals, key=lambda x: x["priority"], reverse=True)[:5]

    def reset_vigilance(self):
        """Rest attention (like taking a break)."""
        self.vigilance = 1.0
        self.time_on_task = 0.0
        self.spotlight.attention_fatigue = 0.0

    def get_state(self) -> dict:
        return {
            "spotlight_items": [
                {"id": item["id"], "salience": item["salience"]}
                for item in self.spotlight.focused_items
            ],
            "vigilance": self.vigilance,
            "fatigue": self.spotlight.attention_fatigue,
            "active_goals": len(self.goals),
            "inhibited_items": len(self.inhibited),
        }
