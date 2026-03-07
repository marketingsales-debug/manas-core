import logging
import json
from pathlib import Path
from src.agents.scouter_agent import ScouterAgent
from src.agents.skill_agent import SkillAgent
from src.executor.llm_router import LLMRouter

# Mock sensory processor for scouter
class MockSensory:
    def encode_text(self, text): return [0.1] * 128
    def detect_novelty(self, pattern): return 0.5
    def init_browser(self, **kwargs): pass
    def browse_to(self, url): pass
    def get_page_text(self): return "Mock page content"
    def close_browser(self): pass

# Mock ToolDispatcher
class MockDispatcher:
    def register(self, tool): print(f"Registered tool: {tool.name}")

def test_github_integration():
    print("--- Initializing LLM Router ---")
    router = LLMRouter()
    
    # Check if Mistral is active as it's our best fallback for reasoning
    if router.mistral_client is None:
         print("WARNING: Mistral client is None. Tests may fail if reasoning is required.")

    print("\n--- Initializing Agents ---")
    scouter = ScouterAgent("Scouter", router, MockSensory(), "/tmp/manas_test_data")
    skill_agent = SkillAgent("MetaLearner", router, MockDispatcher(), "/tmp/manas_test_data", scouter_agent=scouter)

    print("\n--- Testing GitHub Search ---")
    query = "python simple backup script"
    repos = scouter.search_github(query, limit=2)
    print(f"Found {len(repos)} repos for '{query}':")
    for r in repos:
        print(f"  • {r['name']} ({r.get('stars')} stars)")

    if repos:
        print("\n--- Testing Autonomous Cloning & Skill Acquisition ---")
        best_repo = repos[0]
        # We'll use a real repo findable by search if possible, or just mock the clone result for safe testing
        # But let's try a real public repo for truth.
        res = skill_agent.learn_from_github(query)
        print(res)
    else:
        print("Skipping clone test: no repos found (is GH CLI logged in?)")

if __name__ == "__main__":
    logging.basicConfig(level=logging.ERROR)
    test_github_integration()
