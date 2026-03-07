"""
RoutineLearner - Temporal and spatial pattern synthesis for the Aegis Network.
Learns "normal" behavior to detect safety-critical anomalies.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any
import numpy as np

logger = logging.getLogger(__name__)

class RoutineLearner:
    """
    Analyzes parents' daily routines (location, time, activity).
    Flags 'Outlier Events' for the GuardianAgent to investigate.
    """

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.routine_file = self.data_dir / "parent_routines.json"
        self.history_file = self.data_dir / "routine_history.json"
        self.routines = {} # {parent_name: {day_of_week: {hour_slot: [samples]}}}
        self._load_data()

    def record_observation(self, parent: str, location: Dict[str, float], activity: str = "unknown"):
        """Records a data point (GPS + Time) for routine learning."""
        now = time.localtime()
        day = str(now.tm_wday) # 0-6
        hour = str(now.tm_hour)
        
        if parent not in self.routines:
            self.routines[parent] = {}
        if day not in self.routines[parent]:
            self.routines[parent][day] = {}
        if hour not in self.routines[parent][day]:
            self.routines[parent][day][hour] = []
            
        # Store location as [lat, lon]
        sample = {
            "loc": [location.get("lat", 0), location.get("lon", 0)],
            "activity": activity,
            "timestamp": time.time()
        }
        self.routines[parent][day][hour].append(sample)
        
        # Keep only last 30 days of samples per slot to adapt to lifestyle changes
        if len(self.routines[parent][day][hour]) > 30:
            self.routines[parent][day][hour].pop(0)
            
        self._save_data()

    def check_anomaly(self, parent: str, current_loc: Dict[str, float]) -> Dict[str, Any]:
        """
        Compares current state against learned routine.
        Returns anomaly score and description.
        """
        now = time.localtime()
        day = str(now.tm_wday)
        hour = str(now.tm_hour)
        
        if parent not in self.routines or day not in self.routines[parent] or hour not in self.routines[parent][day]:
            return {"score": 0.0, "reason": "Insufficient data for routine check."}
            
        samples = self.routines[parent][day][hour]
        if not samples:
            return {"score": 0.0, "reason": "No samples for this time slot."}
            
        # Calculate mean location for this slot
        locs = np.array([s["loc"] for s in samples])
        mean_loc = np.mean(locs, axis=0)
        
        # Calculate distance from mean
        current = np.array([current_loc.get("lat", 0), current_loc.get("lon", 0)])
        dist = np.linalg.norm(current - mean_loc)
        
        # Simple thresholding: if distance > 2 std devs (or fixed radius if low variance)
        std_dev = np.std(locs, axis=0)
        max_std = max(np.max(std_dev) if len(locs) > 1 else 0.001, 0.001)
        
        score = dist / (max_std * 3.0) # Normalized score (1.0+ is anomalous)
        
        # User defined threshold for "Late/Off-routine"
        is_anomaly = dist > 0.005 # ~500 meters roughly for testing
        return {
            "score": round(float(score), 2),
            "is_anomaly": is_anomaly,
            "reason": f"Parent is {dist:.4f} units away from typical location for this time." if is_anomaly else "Normal"
        }

    def _load_data(self):
        if self.routine_file.exists():
            try:
                with open(self.routine_file, "r") as f:
                    self.routines = json.load(f)
            except Exception:
                pass

    def _save_data(self):
        with open(self.routine_file, "w") as f:
            json.dump(self.routines, f, indent=2)

    def get_notes(self, parent: str) -> str:
        """Generates a summary of learned routines for the internal monologue."""
        if parent not in self.routines:
            return f"No routine data for {parent}."
        
        summary = [f"Learned routine for {parent}:"]
        # Simplified summary: Top location for each day part
        return "\n".join(summary)
