import sys
import os
import json
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from executor.llm_router import LLMRouter
from agents.security_agent import SecurityAgent

class MockMemory:
    def add_semantic(self, title, content):
        print(f"[Memory] Added: {title}")

def test_security_deployment():
    print("Initializing LLM Router...")
    router = LLMRouter()
    memory = MockMemory()
    
    agent = SecurityAgent("PentAGI-Test", router, memory)
    
    # We want to test if _deploy_framework works
    # We'll use a lightweight test or just a 'docker version' check if colima is up
    print("\n--- Testing Framework Selection ---")
    framework_name = "Strix"
    target = "scanme.nmap.org"
    
    print(f"Deploying {framework_name} against {target}...")
    # This will run 'docker run --rm strix-sec/strix:latest scanme.nmap.org'
    # Since we don't want to actually pull and run a heavy image yet, 
    # we can just check if docker is responsive.
    
    import subprocess
    try:
        res = subprocess.run(["docker", "ps"], capture_output=True, text=True)
        if res.returncode == 0:
            print("Docker is RESPONSIVE.")
            # Now let's try a very fast run (just verify image name exists or similar)
            # Or just check the agent's internal logic for command generation
        else:
            print(f"Docker is NOT responsive: {res.stderr}")
    except Exception as e:
        print(f"Docker check failed: {e}")

    print("\n--- Testing Agent Campaign Logic ---")
    # This might call the LLM to decide which tool to use
    # We'll use a 'reasoning' task type which is mapped to Mistral/Groq
    result = agent.run(f"audit {target}")
    
    print("\n--- Campaign Results ---")
    print(result.output[:500] + "...")
    print("\n--- Logs ---")
    print(result.logs)

if __name__ == "__main__":
    test_security_deployment()
