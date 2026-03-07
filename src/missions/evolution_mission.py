import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.cognition.mind import Mind

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_evolution_mission():
    """
    Executes the Phase 15 Autonomous Evolution Mission.
    1. OSINT Pull (BBC/HN)
    2. Graph Ingestion
    3. Scouter Search for related tools
    4. Skill Absorption
    5. Reasoning Report
    """
    print("\n🚀 Starting Phase 15: Autonomous Evolution Mission\n")
    
    # Initialize Manas
    data_dir = "/Users/avipattan/manas/data/metadata"
    mind = Mind(data_dir=data_dir)
    
    # Ensure root node
    mind.knowledge_graph.add_entity("manas_brain", "Manas Central Intelligence", "ai_core")

    # 1. OSINT Pull & Graph Ingestion
    print("📡 Step 1: Pulling World Intelligence...")
    res = mind.intelligence.run("pull tech")
    print(res.output[:500] + "...")
    
    # Analyze and Ingest (already happens inside _analyze_world_state called by run)
    print("\n🔍 Step 2: Analyzing World State & Ingesting Relations...")
    analysis_res = mind.intelligence.run("analyze")
    print(analysis_res.output[:1000] + "...")

    # 2. Extract a topic to scout for
    topic_prompt = (
        "Based on these recent headlines, what is the most important NEW technology or security tool "
        "Manas should search for on GitHub to improve its own capabilities?\n\n"
        "Return ONLY the topic name (1-2 words)."
    )
    topic = mind.language.llm_router.generate(topic_prompt, task_type="reasoning").strip().lower()
    print(f"\n🐙 Step 3: Autonomous Scouting for '{topic}'...")
    
    scout_res = mind.scouter.scout_github_topic(topic)
    print(scout_res)

    # 3. Identify a specific repo to learn
    if mind.scouter.catalog['tools']:
        target_tool = mind.scouter.catalog['tools'][-1] # Take the latest one found
        repo_url = target_tool.get('url')
        repo_name = target_tool.get('name')
        
        if repo_url:
            print(f"\n🧠 Step 4: Absorbing Skill from '{repo_name}'...")
            skill_res = mind.skill_agent.learn_from_github(repo_url)
            print(skill_res)
            
            # Link it manually to the threat/topic if possible
            topic_id = topic.replace(" ", "_")
            mind.knowledge_graph.add_relation(repo_name.lower().replace("/", "_"), topic_id, "addresses_need")

    # 4. Final Strategic Synthesis
    print("\n🌳 Step 5: Generating Unified Reasoning Report...")
    problem = f"Explain how my recent evolution (learning tools related to {topic}) helps me better respond to the current world state."
    reasoning_report = mind.reasoning.think_deeply(problem)
    
    print("\n--- FINAL EVOLUTION REPORT ---")
    print(reasoning_report)
    
    # Store the mission success in the graph
    mind.knowledge_graph.add_entity("mission_phase_15", "Phase 15 Evolution Mission", "event", properties={"status": "success"})
    mind.knowledge_graph.add_relation("mission_phase_15", "manas_brain", "strengthened")

if __name__ == "__main__":
    asyncio.run(run_evolution_mission())
