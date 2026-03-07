"""
Manas System Validator & Stress Tester
Audits all cognitive pipelines and simulates extreme load scenarios.
"""

import os
import sys
import time
import asyncio
import logging

# Add project root to sys.path
sys.path.append(os.getcwd())

from src.cognition.mind import Mind

logger = logging.getLogger(__name__)

class SystemValidator:
    def __init__(self, data_dir="data"):
        self.data_dir = data_dir
        self.mind = None
        self.results = {}

    async def setup(self):
        """Asynchronously initialize the Mind."""
        print("🌱 Initializing Mind Core for validation...")
        self.mind = Mind(data_dir=self.data_dir)
        print("✅ Mind Core Online.")

    async def audit_components(self):
        """Verify that all core components are initialized and reachable."""
        if not self.mind: await self.setup()
        print("\n🔍 AUDITING CORE COMPONENTS...")
        components = [
            "neurochem", "goal_system", "motivation", "hippocampus", 
            "attention", "consciousness", "language", "knowledge_graph",
            "autonomous", "reflection", "plasticity", "guardian"
        ]
        
        for c in components:
            exists = hasattr(self.mind, c)
            status = "✅ ONLINE" if exists else "❌ MISSING"
            print(f" - {c:20} : {status}")
            self.results[f"component_{c}"] = exists

    async def test_cognitive_pipelines(self):
        """Trace a signal from sensor -> neurochem -> motivation -> action."""
        print("\n🧠 TESTING COGNITIVE PIPELINES...")
        
        print(" - Stimulating Amygdala (Fear/Threat)...")
        self.mind.neurochem.release("cortisol", 0.8)
        self.mind.neurochem.release("adrenaline", 0.5)
        
        drive = self.mind.motivation.compute_drive()
        survival_drive = drive.get("survival_drive", 0)
        
        print(f" - Survival Drive: {survival_drive:.2f}")
        if survival_drive > 0.7:
            print(" ✅ Pipeline: Neurochem -> Motivation is active.")
        else:
            print(" ❌ Pipeline: Motivation response is weak.")

    async def stress_test_autonomy(self):
        """Simulate high load and check for stability."""
        print("\n🚀 STRESS TESTING AUTONOMOUS LOOP...")
        
        # 1. Trigger many autonomous thoughts
        print(" - Injecting high-frequency autonomous cycles...")
        for i in range(5):
            self.mind.autonomous._idle_tick()
            time.sleep(0.1)
        
        thoughts = len(self.mind.autonomous.spontaneous_thoughts)
        print(f" - Autonomous Thoughts Generated: {thoughts}")
        
        # 2. Simulated Conflict: High Survival vs High Curiosity
        print(" - Simulating Objective Conflict (Survival vs Curiosity)...")
        self.mind.neurochem.release("dopamine", 1.0) # Boost curiosity
        self.mind.neurochem.release("cortisol", 1.0) # Boost survival
        
        drive = self.mind.motivation.compute_drive()
        print(f" - Drive Balance: Survival({drive['survival_drive']:.2f}) vs Curiosity({drive['curiosity_drive']:.2f})")
        
        # Check if the "Self-First" protocol is maintained
        if drive['survival_drive'] >= drive['curiosity_drive']:
            print(" ✅ Stress Test: Self-First Protocol correctly prioritized survival under load.")
        else:
            print(" ❌ Stress Test: Curiosity outweighed priority 1 during stress.")

    async def run_full_validation(self):
        await self.audit_components()
        await self.test_cognitive_pipelines()
        await self.stress_test_autonomy()
        print("\n✨ FULL SYSTEM VALIDATION COMPLETE.")

if __name__ == "__main__":
    validator = SystemValidator()
    asyncio.run(validator.run_full_validation())
