"""
Prefrontal Cortex - Rational thinking, planning, decision-making.

In the real brain:
- Executive function: planning, reasoning, decision-making
- Inhibits impulsive behavior (overrides amygdala)
- Working memory: holds current task context
- Evaluates consequences before acting
- Slower than amygdala but more accurate (System 2)

For Manas:
- Analyzes situations rationally
- Plans multi-step actions
- Can override fear response when appropriate
- Holds working memory of current task
"""

from ..neuron import NeuronCluster
from ...neurotransmitters.chemistry import NeurochemicalSystem


class PrefrontalCortex:
    """
    Rational decision-making and planning system.

    System 2: Slow, deliberate, logical thinking.
    Can override emotional responses when needed.
    """

    def __init__(self, neurochem: NeurochemicalSystem):
        self.cluster = NeuronCluster("prefrontal", size=128, excitatory_ratio=0.8)
        self.neurochem = neurochem
        self.working_memory: list[dict] = []
        self.working_memory_capacity: int = 7  # Miller's Law: 7±2 items
        self.plans: list[dict] = []
        self.decision_history: list[dict] = []

    def reason(self, situation: dict, amygdala_signal: dict) -> dict:
        """
        Deliberate reasoning about a situation.

        Takes amygdala's fast assessment and adds rational analysis.
        High cortisol impairs prefrontal function (stress makes you dumber).
        """
        cortisol = self.neurochem.chemicals["cortisol"].level
        dopamine = self.neurochem.chemicals["dopamine"].level

        # Cortisol impairs rational thinking (real effect)
        reasoning_capacity = max(0.2, 1.0 - cortisol * 0.6)

        # Dopamine improves focus and motivation
        reasoning_capacity *= (0.7 + dopamine * 0.3)

        # Should we override the fear response?
        override_fear = False
        if amygdala_signal["is_dangerous"] and not amygdala_signal["should_block"]:
            # Analyze: is the fear justified?
            threat = amygdala_signal["threat_level"]
            if reasoning_capacity > 0.6 and threat < 0.7:
                override_fear = True

        # Evaluate potential outcomes
        risk = amygdala_signal["threat_level"]
        reward = situation.get("expected_reward", 0.5)
        uncertainty = situation.get("uncertainty", 0.5)

        # Risk-reward analysis (impaired by stress)
        decision_score = (reward - risk * 0.8) * reasoning_capacity
        # Uncertainty penalty (cautious when unsure)
        decision_score -= uncertainty * 0.3

        # Generate reasoning
        action = "proceed" if decision_score > 0 else "hesitate" if decision_score > -0.3 else "abort"

        return {
            "action": action,
            "decision_score": decision_score,
            "reasoning_capacity": reasoning_capacity,
            "override_fear": override_fear,
            "risk_assessment": risk,
            "reward_assessment": reward,
            "confidence": abs(decision_score) * reasoning_capacity,
        }

    def plan(self, goal: str, steps: list[str]) -> dict:
        """Create a plan to achieve a goal."""
        plan = {
            "goal": goal,
            "steps": steps,
            "current_step": 0,
            "completed": False,
            "outcomes": [],
        }
        self.plans.append(plan)

        # Store in working memory
        self._add_to_working_memory({
            "type": "plan",
            "content": goal,
            "steps_count": len(steps),
        })

        return plan

    def update_plan(self, plan_index: int, step_outcome: dict):
        """Update a plan based on step outcome."""
        if plan_index < len(self.plans):
            plan = self.plans[plan_index]
            plan["outcomes"].append(step_outcome)

            if step_outcome.get("success", False):
                plan["current_step"] += 1
                self.neurochem.trigger_event("success", 0.3)
                if plan["current_step"] >= len(plan["steps"]):
                    plan["completed"] = True
                    self.neurochem.trigger_event("reward", 0.5)
            else:
                self.neurochem.trigger_event("failure", 0.4)

    def _add_to_working_memory(self, item: dict):
        """Add to working memory (limited capacity like real brain)."""
        self.working_memory.append(item)
        if len(self.working_memory) > self.working_memory_capacity:
            # Oldest items fall out (like real working memory)
            self.working_memory.pop(0)

    def get_working_memory(self) -> list[dict]:
        return list(self.working_memory)

    def clear_working_memory(self):
        self.working_memory.clear()

    def get_state(self) -> dict:
        cortisol = self.neurochem.chemicals["cortisol"].level
        return {
            "reasoning_capacity": max(0.2, 1.0 - cortisol * 0.6),
            "working_memory_items": len(self.working_memory),
            "active_plans": len([p for p in self.plans if not p["completed"]]),
            "activity": self.cluster.get_activity(),
        }
