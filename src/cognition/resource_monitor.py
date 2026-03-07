"""
ResourceMonitor - Tracks API consumption, costs, and manages frugality.
"""

import json
import logging
import time
import psutil
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """
    Manages the economic consciousness of Manas.
    - Tracks costs per provider.
    - Maintains daily/monthly budgets.
    - Signals frugality (use cheaper models) when budget is low.
    """

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.stats_path = self.data_dir / "resource_stats.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.daily_limit = 50.0  # limit per day
        self.monthly_limit = 500.0 # limit per month
        
        # Phase 31: Energy Awareness
        self.base_tick_rate = 30.0 # Standard background loop interval
        self.total_cognitive_ops = 0
        self.start_time = time.time()
        
        self.usage_history: List[Dict[str, Any]] = []
        self._load_stats()

    def _load_stats(self):
        if self.stats_path.exists():
            try:
                with open(self.stats_path, "r") as f:
                    data = json.load(f)
                    self.usage_history = data.get("history", [])
                    self.daily_limit = data.get("daily_limit", self.daily_limit)
                    self.monthly_limit = data.get("monthly_limit", self.monthly_limit)
            except Exception as e:
                logger.error(f"Failed to load resource stats: {e}")

    def _save_stats(self):
        try:
            with open(self.stats_path, "w") as f:
                json.dump({
                    "history": self.usage_history,
                    "daily_limit": self.daily_limit,
                    "last_updated": time.time()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save resource stats: {e}")

    def log_usage(self, provider: str, model: str, tokens: int, cost: float = 0.0):
        """Log an API transaction."""
        # Simple cost estimation if not provided
        if cost == 0.0 and tokens > 0:
            cost = self._estimate_cost(provider, model, tokens)

        entry = {
            "timestamp": time.time(),
            "provider": provider,
            "model": model,
            "tokens": tokens,
            "cost": cost
        }
        self.usage_history.append(entry)
        
        # Keep only last 1000 entries
        if len(self.usage_history) > 1000:
            self.usage_history = self.usage_history[-1000:]
            
        self.total_cognitive_ops += 1
        self._save_stats()

    def get_energy_efficiency(self) -> float:
        """
        Phase 31: Estimates computational energy efficiency.
        Returns a modifier (1.0 = highly efficient, < 1.0 = inefficient, throttle down).
        """
        uptime = time.time() - self.start_time
        if uptime < 60:
            return 1.0 # Give it a minute to warm up
            
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory().percent
        
        # If CPU/Mem are high but cognitive ops are low, we are inefficient
        ops_per_minute = self.total_cognitive_ops / (uptime / 60)
        
        if cpu_usage > 70 and ops_per_minute < 2:
            return 0.5 # High energy, low output -> Slow down ticks
        elif cpu_usage > 50 and ops_per_minute < 5:
            return 0.8 # Moderate inefficiency
            
        return 1.0 # Efficient

    def get_daily_total(self) -> float:
        """Calculate total cost for the current day."""
        now = time.time()
        start_of_day = now - (now % 86400)
        total = sum(e["cost"] for e in self.usage_history if e["timestamp"] > start_of_day)
        return round(total, 4)

    def get_frugality_score(self) -> float:
        """
        Returns 0.0 to 1.0 (1.0 = extremely frugal/low budget).
        Determines if Manas should switch to cheaper models.
        """
        daily_total = self.get_daily_total()
        if self.daily_limit == 0:
            return 1.0
            
        score = daily_total / self.daily_limit
        return min(1.0, max(0.0, score))

    def _estimate_cost(self, provider: str, model: str, tokens: int) -> float:
        """Approximate cost based on common model pricing."""
        prices = {
            "anthropic": 0.000015, # $15 per 1M tokens (avg for Claude 3.5 Sonnet)
            "openai": 0.00001,      # $10 per 1M (GPT-4o)
            "gemini": 0.0000035,   # $3.5 per 1M (1.5 Flash)
            "groq": 0.0,            # Free tier assumed
            "ollama": 0.0,          # Local
            "mistral": 0.000002     # $2 per 1M (Mistral Large)
        }
        return tokens * prices.get(provider, 0.000001)

    def get_state(self) -> Dict[str, Any]:
        daily = self.get_daily_total()
        return {
            "daily_total_usd": daily,
            "daily_limit_usd": self.daily_limit,
            "frugality": self.get_frugality_score(),
            "energy_efficiency": self.get_energy_efficiency(),
            "status": "Healthy" if daily < self.daily_limit * 0.8 else "Budget Warning"
        }
