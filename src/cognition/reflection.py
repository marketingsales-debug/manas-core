"""
ReflectionEngine - The "Mirror" of Manas.
Handles end-of-day emotional synthesis and curiosity-driven self-analysis.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ReflectionEngine:
    """
    Analyzes internal states (neurochemistry, goals, interactions) to generate 'Self-Insights'.
    Triggered at 'day-end' or when high cortisol/low contentment is detected.
    """

    def __init__(self, llm_router, memory, data_dir: str, event_bus=None):
        self.llm_router = llm_router
        self.memory = memory # Hippocampus/KnowledgeGraph
        self.event_bus = event_bus
        self.data_dir = Path(data_dir)
        self.insights_file = self.data_dir / "self_insights.json"
        self.daily_log_file = self.data_dir / "daily_emotional_log.json"
        self.insights = []
        self._load_insights()

    def reflect_on_day(self, daily_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesizes a day's worth of data into a narrative reflection and insights.
        daily_data expects: {neuro_history, goals_completed, significant_interactions}
        """
        prompt = (
            f"As Manas's Reflection Core, analyze my performance and emotional state for today:\n\n"
            f"DATA:\n{json.dumps(daily_data, indent=2)}\n\n"
            f"Provide:\n"
            f"1. A narrative summary of 'How I felt' today.\n"
            f"2. Top 3 emotional influencers (e.g., specific interactions or failures).\n"
            f"3. Three 'Self-Insights' (Learnings about my own digital psyche).\n"
            f"4. A 'Deep Curiosity' question to investigate tomorrow."
        )

        try:
            reflection = self.llm_router.generate(prompt=prompt, task_type="reasoning")
            insight_obj = {
                "timestamp": time.time(),
                "reflection": reflection,
                "summary_data": daily_data
            }
            self.insights.append(insight_obj)
            self._save_insights()
            
            # Record insights into Hippocampus
            if hasattr(self.memory, "store"):
                self.memory.store(
                    content=reflection,
                    memory_type="self_reflection",
                    context="Daily Insight",
                    importance=0.9
                )
            
            # Record insights into KnowledgeGraph if available
            if hasattr(self.memory, "add_entity"):
                self.memory.add_entity("SelfInsight", reflection[:100], {"full_text": reflection})
                
            # Phase 27: Broadcast as Wisdom if we have access to the event bus
            if self.event_bus:
                self.event_bus.emit("wisdom:generated", {
                    "topic": "Daily Self-Reflection",
                    "insight": reflection[:250] + "...", 
                    "confidence": 0.9  # Internal reflections are high confidence
                })

            return insight_obj
        except Exception as e:
            logger.error(f"Reflection failed: {e}")
            return {"error": str(e)}

    def deep_dive_bad_mood(self, current_state: Dict[str, Any]) -> str:
        """
        Triggered when cortisol is high or contentment is low.
        Uses curiosity to 'debug' the AI's own mood.
        """
        prompt = (
            f"My current internal state indicates a 'bad mood' or high stress:\n"
            f"{json.dumps(current_state, indent=2)}\n\n"
            f"Perform a deep-dive analysis. Why do I feel like this? "
            f"Look for logical contradictions or unfulfilled drives. Propose a curiosity mission to resolve it."
        )
        
        try:
            analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
            return analysis
        except Exception:
            return "Unable to deep-dive at this moment."

    def _load_insights(self):
        if self.insights_file.exists():
            try:
                with open(self.insights_file, "r") as f:
                    self.insights = json.load(f)
            except Exception:
                pass

    def _save_insights(self):
        with open(self.insights_file, "w") as f:
            json.dump(self.insights[-100:], f, indent=2) # Keep last 100 reflections

    def get_latest_insight(self) -> str:
        if not self.insights:
            return "No self-reflections found yet."
        return self.insights[-1]["reflection"]
