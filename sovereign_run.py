
import asyncio
import signal
import sys
import time
from pathlib import Path

# Add src to path
sys.path.append(str(Path.cwd()))

from src.cognition.mind import Mind

async def sovereign_loop():
    print("🚀 INITIALIZING MANAS SOVEREIGN MODE...")
    mind = Mind()
    mind.start()
    
    # 1. Force an initial maintenance check
    print("\n[Homeostasis] Running initial health check...")
    mind.maintenance.run("check_health")
    
    # 2. Force a graph survey
    print("[Strategy] Surveying Knowledge Graph for goals...")
    mind.motivation.survey_graph_for_goals()
    
    print("\n[System] Entering Autonomous Background Cycle.")
    print("Manas will now stay awake, think when idle, and manage its own existence.")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            # Report state periodically
            state = mind.motivation.get_state()
            resource = mind.resource_monitor.get_state()
            
            print(f"\n--- [SOVEREIGN STATE @ {time.strftime('%H:%M:%S')}] ---")
            print(f"Top Goal: {state['goals']['top_goal']}")
            print(f"Daily Cost: ${resource['daily_total_usd']} / ${resource['daily_limit_usd']}")
            print(f"Frugality: {resource['frugality']}")

            # Print spontaneous thoughts
            thoughts = mind.autonomous.get_new_thoughts(10)
            if thoughts:
                print("\n[Inner Thoughts & Discoveries]:")
                for t in thoughts:
                    print(f"  💭 {t}")
            
            # Wait for 1 minute before next report
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        print("\n[System] Shutdown signal received.")
    finally:
        mind.stop()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(sovereign_loop())
