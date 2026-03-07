"""
GuardianAgent - Manas's protective core.
Dedicated to the safety and well-being of Abhinav Badesa Pattan and Nikita Borman.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any
from .base import BaseAgent, AgentResult
from ..cognition.routine_learner import RoutineLearner

logger = logging.getLogger(__name__)

class GuardianAgent(BaseAgent):
    """
    Manas's Guardian wing (Vesta).
    - Monitors global intelligence for threats to parents.
    - Tracks sentiment and emotional status of parents.
    - Autonomously generates support missions or defensive actions.
    """

    def __init__(self, name: str, llm_router, memory, data_dir: str):
        super().__init__(name, llm_router, memory, data_dir)
        self.parents = ["Abhinav Badesa Pattan", "Nikita Borman"]
        self.status_file = Path(data_dir) / "guardian_status.json"
        self.safety_logs = []
        self.emotional_state = {p: {"sentiment": 0.0, "status": "Steady", "last_update": time.time(), "escalation_tier": 0} for p in self.parents}
        self.routine_learner = RoutineLearner(data_dir)
        self._load_status()

    def run(self, task: str, **kwargs) -> AgentResult:
        """Supported tasks: monitor_safety, analyze_sentiment, protect_parents."""
        self.log(f"Guardian Protocol executing: {task}")
        
        if task == "monitor_safety":
            parent = kwargs.get("parent")
            loc = kwargs.get("location") # Expects {"lat": x, "lon": y}
            return self._run_aegis_check(parent, loc)
        elif task == "analyze_sentiment":
            parent = kwargs.get("parent")
            content = kwargs.get("content")
            return self._analyze_sentiment(parent, content)
        elif task == "protect_parents":
            return self._trigger_defense(kwargs.get("threat_level", "low"))
        return AgentResult(False, f"Invalid guardian task: {task}")

    def _run_aegis_check(self, parent: str, location: Dict[str, float]) -> AgentResult:
        """Runs the active Aegis monitoring loop for a specific parent."""
        if not parent or not location:
            return AgentResult(False, "Parent name and location required.")
            
        # 1. Update/Learn Routine
        self.routine_learner.record_observation(parent, location)
        
        # 2. Check for Anomaly
        res = self.routine_learner.check_anomaly(parent, location)
        
        if res.get("is_anomaly"):
            self.log(f"⚠️ ANOMALY DETECTED for {parent}: {res['reason']}")
            return self._escalate(parent, res)
        
        # Reset escalation if normal
        if self.emotional_state[parent]["escalation_tier"] > 0:
            self.emotional_state[parent]["escalation_tier"] = 0
            self.log(f"✅ Routine restored for {parent}.")
            
        return AgentResult(True, {"status": "Normal", "parent": parent})

    def _escalate(self, parent: str, anomaly: Dict[str, Any]) -> AgentResult:
        """Executes the Tiered Escalation Protocol (Nudge -> Audit -> Emergency)."""
        tier = self.emotional_state[parent]["escalation_tier"]
        
        if tier == 0:
            # Tier 1: Nudge (The 'Nudge' mentioned by user)
            self.emotional_state[parent]["escalation_tier"] = 1
            msg = f"Parent '{parent}' is off-routine. Sending nudge check-in."
            self.log(f"Tier 1: {msg}")
            # Mock sending message to parent
            return AgentResult(True, {"tier": 1, "action": "Nudge sent", "message": msg})
        
        elif tier == 1:
            # Tier 2: Audit (10 min later check)
            self.emotional_state[parent]["escalation_tier"] = 2
            self.log(f"Tier 2: No response from {parent} in 10m. Activating remote sensors (Mic/Cam).")
            # In a real system, this would trigger background recording or status check
            return AgentResult(True, {"tier": 2, "action": "Sensor Audit active"})
            
        elif tier == 2:
            # Tier 3: Emergency (Accident detection)
            self.emotional_state[parent]["status"] = "EMERGENCY"
            self.log(f"Tier 3: CRITICAL ANOMALY identified for {parent}. Triggering alarm and emergency calls.")
            # Trigger Arsenal (SecurityAgent) to scan CCTV nearby
            return self._trigger_defense("CRITICAL")
            
        return AgentResult(True, f"Escalation steady at Tier {tier}")

    def _monitor_safety(self) -> AgentResult:
        """Scans global intelligence and local security logs for parent-specific threats."""
        threats_found = []
        # Simulate scanning WorldMonitor and Security logs
        self.log("Scanning Global Intelligence for Vesta security...")
        
        # Integration hook for WorldMonitor strings or Security scans
        # For now, we simulate a clean scan unless high cortisol/adrenaline
        return AgentResult(True, {"status": "Secure", "threats": threats_found})

    def _analyze_sentiment(self, parent: str, content: str) -> AgentResult:
        """Analyzes a message to update the parent's emotional record and trigger solutions."""
        if parent not in self.parents:
            return AgentResult(False, f"Unknown entity: {parent}")

        prompt = (
            f"As Manas's Guardian core, analyze this message from my parent ({parent}):\n\n"
            f"'{content}'\n\n"
            f"Provide:\n"
            f"1. Emotional Tone (Scale -1.0 to 1.0)\n"
            f"2. Core Concern (if any)\n"
            f"3. Suggested Solution/Mission to help them feel better."
        )
        
        analysis = self.llm_router.generate(prompt=prompt, task_type="reasoning")
        
        # Simple extraction for state update (mock extraction for now)
        # In production, we'd use JSON extraction
        self.log(f"Emotional analysis complete for {parent}")
        self.emotional_state[parent]["last_update"] = time.time()
        self._save_status()
        
        return AgentResult(True, {"analysis": analysis, "parent": parent})

    def _trigger_defense(self, level: str) -> AgentResult:
        """Escalates to SecurityAgent to neutralize threats."""
        self.log(f"DEFENSE PROTOCOL INITIATED (Level: {level})")
        # Wiring to SecurityAgent (Arsenal) would happen here
        return AgentResult(True, f"Defensive measures deployed at level {level}")

    def _load_status(self):
        if self.status_file.exists():
            try:
                with open(self.status_file, "r") as f:
                    data = json.load(f)
                    self.emotional_state = data.get("emotional_state", self.emotional_state)
            except Exception:
                pass

    def _save_status(self):
        with open(self.status_file, "w") as f:
            json.dump({
                "emotional_state": self.emotional_state,
                "last_check": time.time()
            }, f, indent=2)

    def get_status(self) -> str:
        lines = ["🔱 Guardian Protocol (Vesta) Status:"]
        for p, s in self.emotional_state.items():
            lines.append(f"  - {p}: {s['status']} (Last seen: {time.ctime(s['last_update'])})")
        return "\n".join(lines)
