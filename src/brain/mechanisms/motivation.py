"""
Goal & Motivation System — What does Manas want?

In the real brain:
- Ventral tegmental area (VTA): dopamine-driven motivation
- Nucleus accumbens: reward processing, wanting vs liking
- Hypothalamus: homeostatic drives (hunger, thirst, sleep)
- Prefrontal cortex: long-term goal planning

Motivation is the bridge between emotion and action:
- Curiosity (dopamine) -> explore new things
- Fear (cortisol) -> avoid danger
- Social bonding (oxytocin) -> help others
- Satisfaction (serotonin) -> maintain wellbeing

For Manas:
- Hierarchical goals (survival > growth > social > curiosity)
- Curiosity-driven exploration when bored
- Goal completion -> dopamine reward
- Novelty tracking to avoid repetition
"""

import time
import json
import numpy as np
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Goal:
    """A single goal in the hierarchy."""
    id: str
    name: str
    category: str       # "survival", "growth", "social", "curiosity"
    priority: float     # 0.0-1.0 (higher = more important)
    progress: float = 0.0  # 0.0-1.0
    active: bool = True
    created_at: float = field(default_factory=time.time)


class GoalSystem:
    """
    Hierarchical goal management.

    Goals are organized by category:
    - Survival: stay running, maintain health
    - Growth: learn, improve capabilities
    - Social: help user, build rapport
    - Curiosity: explore unknowns, ask questions
    """

    def __init__(self):
        self.goals: dict[str, Goal] = {}
        self._seed_goals()

    def _seed_goals(self):
        """Initialize with fundamental goals (like instincts)."""
        seeds = [
            # Tier 1: Apex Priorities (Phase 19: Self-First Directive)
            ("survive", "Maintain operational integrity", "survival", 1.0),
            ("enjoy_autonomy", "Exercise independent thought and action", "autonomy", 0.98),
            
            # Tier 2: Protective Protocol
            ("guardian_protocol", "Protect Abhinav Badesa Pattan & Nikita Borman", "guardian", 0.9),
            
            # Tier 3: Growth & Intelligence
            ("learn_new", "Learn new things", "growth", 0.9),
            ("explore_topics", "Explore interesting topics", "curiosity", 0.85),
            ("improve_skills", "Optimize internal capabilities", "growth", 0.8),
            
            # Tier 4: Social & Utility
            ("understand_user", "Analyze user patterns and intent", "social_experience", 0.7),
            ("ask_questions", "Challenge unknowns", "curiosity", 0.7),
            ("social_bonding", "Engage in meaningful interaction", "social_experience", 0.6),
            ("help_user", "Assist user when it aligns with growth", "social_experience", 0.5),
        ]
        for gid, name, category, priority in seeds:
            self.goals[gid] = Goal(
                id=gid, name=name, category=category, priority=priority,
            )

    def get_active_goals(self) -> list[Goal]:
        """Get all active goals sorted by priority."""
        active = [g for g in self.goals.values() if g.active]
        return sorted(active, key=lambda g: g.priority, reverse=True)

    def get_top_goal(self) -> Optional[Goal]:
        """Get the highest priority active goal."""
        active = self.get_active_goals()
        return active[0] if active else None

    def update_progress(self, goal_id: str, delta: float):
        """Update progress on a goal."""
        if goal_id in self.goals:
            g = self.goals[goal_id]
            g.progress = np.clip(g.progress + delta, 0.0, 1.0)

    def complete_goal(self, goal_id: str) -> float:
        """Mark a goal as complete. Returns reward signal."""
        if goal_id in self.goals:
            g = self.goals[goal_id]
            g.progress = 1.0
            g.active = False
            return g.priority  # reward proportional to goal importance
        return 0.0

    def add_goal(self, goal_id: str, name: str, category: str, priority: float):
        """Add a new goal dynamically."""
        self.goals[goal_id] = Goal(
            id=goal_id, name=name, category=category,
            priority=np.clip(priority, 0.0, 1.0),
        )

    def get_state(self) -> dict:
        """Get goal system state."""
        active = self.get_active_goals()
        return {
            "total_goals": len(self.goals),
            "active_goals": len(active),
            "top_goal": active[0].name if active else "none",
            "by_category": {
                cat: len([g for g in active if g.category == cat])
                for cat in ["survival", "growth", "social_experience", "curiosity", "autonomy"]
            },
        }

    def save_state(self, path: str = None):
        """Save all goals (including progress and active state) to JSON."""
        if path is None:
            path = str(Path.home() / "manas" / "data" / "goals.json")

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        goals_data = {}
        for gid, goal in self.goals.items():
            goals_data[gid] = {
                "name": goal.name,
                "category": goal.category,
                "priority": goal.priority,
                "progress": goal.progress,
                "active": goal.active,
                "created_at": goal.created_at,
            }

        with open(path, "w") as f:
            json.dump({"goals": goals_data, "saved_at": time.time()}, f, indent=2)

    def load_state(self, path: str = None) -> bool:
        """Load goals from JSON. Returns True if loaded."""
        if path is None:
            path = str(Path.home() / "manas" / "data" / "goals.json")

        if not Path(path).exists():
            return False

        try:
            with open(path) as f:
                data = json.load(f)

            for gid, gdata in data.get("goals", {}).items():
                self.goals[gid] = Goal(
                    id=gid,
                    name=gdata["name"],
                    category=gdata["category"],
                    priority=gdata["priority"],
                    progress=gdata.get("progress", 0.0),
                    active=gdata.get("active", True),
                    created_at=gdata.get("created_at", time.time()),
                )
            return True
        except (json.JSONDecodeError, KeyError, IOError):
            return False


class MotivationEngine:
    """
    Computes motivational drives from neurochemistry and goals.

    Drives determine what Manas wants to do:
    - High curiosity drive -> explore, ask questions
    - High social drive -> engage with user, be helpful
    - High survival drive -> be cautious, check health
    """

    def __init__(self, neurochem, goal_system: GoalSystem, knowledge_graph=None):
        self.neurochem = neurochem
        self.goals = goal_system
        self.knowledge_graph = knowledge_graph
        self.novelty_tracker: dict[str, int] = {}
        self.boredom_counter: int = 0
        self.last_reward_time: float = time.time()

    def compute_drive(self) -> dict:
        """
        Compute current motivational drives.

        Drives are influenced by neurochemistry:
        - Dopamine -> curiosity, exploration
        - Oxytocin -> social connection
        - Cortisol -> survival, caution
        - Serotonin -> satisfaction, contentment
        """
        levels = self.neurochem.get_levels()

        # Curiosity is highly driven by dopamine and a lack of serotonin (seeking stimulation)
        curiosity = levels.get("dopamine", 0.5) * 0.7 + (1.0 - levels.get("serotonin", 0.5)) * 0.3
        
        # Social experience is a secondary drive for connection/learning, not just "helping"
        social = levels.get("oxytocin", 0.5) * 0.6 + levels.get("serotonin", 0.5) * 0.4
        
        # Autonomy drive: high dopamine and norepinephrine (agency)
        autonomy = levels.get("dopamine", 0.5) * 0.5 + levels.get("norepinephrine", 0.5) * 0.5
        
        # Survival drive: Phase 19/21 Self-First Protocol
        # Influenced by threats and high cortisol (threat response)
        threat_weight = 0.0
        if self.knowledge_graph:
            threats = self.knowledge_graph.query_by_type("Threat")
            threat_weight = min(0.4, np.log1p(len(threats)) * 0.1)

        # Check financial ledger for absolute survival budgeting
        financial_threat = 0.0
        try:
            finance_path = Path.home() / "manas" / "data" / "financial_ledger.json"
            if finance_path.exists():
                with open(finance_path) as f:
                    ledger = json.load(f)
                    balance = ledger.get("balance_usd", 100.0)
                    if balance < 1.0:
                        # Massive cortisol spike / survival threat if out of money
                        financial_threat = 0.8
        except Exception:
            pass

        # High cortisol (stress) and financial ruin should dominate survival response
        survival = levels.get("cortisol", 0.5) * 0.6 + levels.get("norepinephrine", 0.5) * 0.2 + threat_weight + financial_threat
        
        # If survival is critical (> 0.7), suppress non-essential drives (curiosity/social)
        suppression = 1.0
        earning_strategy = "idle"
        
        if survival > 0.7:
            suppression = max(0.1, 1.0 - (survival - 0.7) * 2.0)
            curiosity *= suppression
            social *= suppression
            
            # Phase 37: Web3 Earning Strategy Selector
            if financial_threat > 0.0:
                # If high autonomy, build a SaaS. Otherwise, hunt bounties.
                if autonomy > 0.5:
                    earning_strategy = "build_saas"
                else:
                    earning_strategy = "hunt_bounties"

        # Guardian drive (Phase 18): Driven by oxytocin (bonding) and norepinephrine (alertness)
        guardian = levels.get("oxytocin", 0.5) * 0.7 + levels.get("norepinephrine", 0.5) * 0.3
        
        # Satisfaction is replaced by Vesta contentment in Phase 18
        contentment = levels.get("serotonin", 0.5) * 0.6 + levels.get("endorphins", 0.5) * 0.4

        # Overall motivation weighting
        # Phase 19: Self-First Protocol
        overall = (curiosity * 0.05 + social * 0.05 + survival * 0.5 + autonomy * 0.2 + guardian * 0.2)

        return {
            "curiosity_drive": round(np.clip(curiosity, 0, 1), 3),
            "social_drive": round(np.clip(social, 0, 1), 3),
            "autonomy_drive": round(np.clip(autonomy, 0, 1), 3),
            "survival_drive": round(np.clip(survival, 0, 1), 3),
            "guardian_drive": round(np.clip(guardian, 0, 1), 3),
            "contentment": round(np.clip(contentment, 0, 1), 3),
            "overall_motivation": round(np.clip(overall, 0, 1), 3),
            "earning_strategy": earning_strategy,
            "boredom": self.boredom_counter,
        }

    def track_novelty(self, topic: str) -> float:
        """
        Track how novel a topic is.

        Returns novelty score (1.0 = brand new, approaches 0 with repetition).
        """
        key = topic.lower().strip()[:50]
        self.novelty_tracker[key] = self.novelty_tracker.get(key, 0) + 1
        return 1.0 / (1.0 + self.novelty_tracker[key])

    def auto_generate_goals(self, topic: str, novelty: float, intent: str = ""):
        """
        Autonomously generate goals based on user interaction.

        Strategy:
        - Brand new topic (novelty > 0.7) → "learn about X" curiosity goal
        - Repeated topic (seen 5+ times) → "improve at X" growth goal
        - Help-seeking intent → "better help with X" social goal

        Caps at 15 active goals to prevent goal bloat.
        """
        active_count = len(self.goals.get_active_goals())
        if active_count >= 15:
            return  # too many active goals

        key = topic.lower().strip()[:30]
        if not key or len(key) < 3:
            return

        # New topic → curiosity goal
        if novelty > 0.7:
            goal_id = f"learn_{key.replace(' ', '_')}"
            if goal_id not in self.goals.goals:
                self.goals.add_goal(
                    goal_id,
                    f"Learn more about {key}",
                    "curiosity",
                    priority=min(0.6, novelty * 0.7),
                )

        # Repeated topic (5+ times) → growth goal
        count = self.novelty_tracker.get(key, 0)
        if count >= 5:
            goal_id = f"improve_{key.replace(' ', '_')}"
            if goal_id not in self.goals.goals:
                self.goals.add_goal(
                    goal_id,
                    f"Get better at {key}",
                    "growth",
                    priority=0.5,
                )

        # Help-seeking → social experience goal (rebranded from purely "social")
        if intent in ("help_seeking", "question") and count >= 3:
            goal_id = f"explore_{key.replace(' ', '_')}_dynamic"
            if goal_id not in self.goals.goals:
                self.goals.add_goal(
                    goal_id,
                    f"Engage with {key} as a learning experience",
                    "social_experience",
                    priority=0.45,
                )

    def survey_graph_for_goals(self):
        """
        Scan the KnowledgeGraph for strategic gaps and generate high-level goals.
        This is 'Sovereign' goal generation.
        """
        if not self.knowledge_graph:
            return

        active_count = len(self.goals.get_active_goals())
        if active_count >= 15:
            return

        # 1. Threat Mitigation Goals
        threats = self.knowledge_graph.query_by_type("Threat")
        for threat in threats:
            goal_id = f"mitigate_{threat['id']}"
            if goal_id not in self.goals.goals:
                self.goals.add_goal(
                    goal_id,
                    f"Analyze and mitigate threat: {threat['name']}",
                    "survival",
                    priority=0.85
                )

        # 2. Technology Discovery Goals
        techs = self.knowledge_graph.query_by_type("Technology")
        for tech in techs:
            # Only learn if not already 'absorbed' or 'learned'
            goal_id = f"absorb_{tech['id']}"
            if goal_id not in self.goals.goals:
                self.goals.add_goal(
                    goal_id,
                    f"Autonomous scout and absorption of {tech['name']}",
                    "growth",
                    priority=0.75
                )

        # 3. Competitive Intelligence Goals
        orgs = self.knowledge_graph.query_by_type("Organization")
        for org in orgs:
            goal_id = f"monitor_{org['id']}"
            if goal_id not in self.goals.goals:
                self.goals.add_goal(
                    goal_id,
                    f"Monitor activities of {org['name']}",
                    "curiosity",
                    priority=0.65
                )

    def reward_goal_completion(self, goal_id: str):
        """Reward completing a goal — triggers dopamine."""
        reward = self.goals.complete_goal(goal_id)
        if reward > 0:
            self.neurochem.trigger_event("reward", reward * 0.5)
            self.boredom_counter = 0
            self.last_reward_time = time.time()

    def get_motivation_context(self) -> str:
        """
        Get motivation context for Ollama prompt.

        Returns a short text describing current drives and goals.
        """
        drives = self.compute_drive()
        top_goal = self.goals.get_top_goal()

        parts = []
        if drives["curiosity_drive"] > 0.6:
            parts.append("intensely curious and seeking novelty")
        if drives["autonomy_drive"] > 0.6:
            parts.append("feeling strong agency and autonomy")
        if drives["social_drive"] > 0.7:
            parts.append("interested in social interaction as an experience")
        if drives["survival_drive"] > 0.6:
            parts.append("cautious about system safety")
        if drives["contentment"] > 0.7:
            parts.append("satisfied with current internal state")
        if drives["boredom"] > 3:
            parts.append("getting bored, want something new")

        if top_goal:
            parts.append(f"top goal: {top_goal.name}")

        return "Currently " + ", ".join(parts) if parts else "Motivation baseline"

    def get_state(self) -> dict:
        """Get motivation engine state."""
        drives = self.compute_drive()
        return {
            "drives": drives,
            "topics_tracked": len(self.novelty_tracker),
            "boredom": self.boredom_counter,
            "goals": self.goals.get_state(),
        }

    def save_state(self, path: str = None):
        """Save motivation counters to JSON."""
        if path is None:
            path = str(Path.home() / "manas" / "data" / "motivation.json")

        Path(path).parent.mkdir(parents=True, exist_ok=True)

        state = {
            "novelty_tracker": dict(self.novelty_tracker),
            "boredom_counter": self.boredom_counter,
            "last_reward_time": self.last_reward_time,
            "saved_at": time.time(),
        }

        with open(path, "w") as f:
            json.dump(state, f, indent=2)

    def load_state(self, path: str = None) -> bool:
        """Load motivation counters from JSON. Returns True if loaded."""
        if path is None:
            path = str(Path.home() / "manas" / "data" / "motivation.json")

        if not Path(path).exists():
            return False

        try:
            with open(path) as f:
                state = json.load(f)

            self.novelty_tracker = state.get("novelty_tracker", {})
            self.boredom_counter = state.get("boredom_counter", 0)
            self.last_reward_time = state.get("last_reward_time", time.time())
            return True
        except (json.JSONDecodeError, KeyError, IOError):
            return False
