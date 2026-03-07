"""
SkillAgent — The Meta-Learner.

When Manas's Scouter discovers a new API or tool, this agent:
1. Reads the documentation (via LLM or web scraping).
2. Generates a Python connector/tool class.
3. Registers it in the ToolDispatcher at runtime.

This gives Manas the ability to expand its own capabilities without
any human code changes.
"""

import logging
import json
import time
from pathlib import Path

logger = logging.getLogger(__name__)


class SkillAgent:
    """
    Autonomous skill acquisition engine.
    Reads API docs -> Generates Tool code -> Registers it live.
    """

    def __init__(self, name: str, llm_router, tool_dispatcher, data_dir: str, scouter_agent=None, knowledge_graph=None):
        self.name = name
        self.llm_router = llm_router
        self.tool_dispatcher = tool_dispatcher
        self.data_dir = Path(data_dir)
        self.scouter_agent = scouter_agent
        self.knowledge_graph = knowledge_graph
        self.skills_dir = self.data_dir / "learned_skills"
        self.skills_dir.mkdir(parents=True, exist_ok=True)
        self.skill_registry_path = self.data_dir / "skill_registry.json"
        self._load_registry()

    def _load_registry(self):
        if self.skill_registry_path.exists():
            with open(self.skill_registry_path, "r") as f:
                self.registry = json.load(f)
        else:
            self.registry = {"skills": [], "total_learned": 0}

    def _save_registry(self):
        with open(self.skill_registry_path, "w") as f:
            json.dump(self.registry, f, indent=2)

    def learn_api(self, api_name: str, documentation: str) -> str:
        """
        Core method: Takes an API name and its documentation,
        then generates a usable Python tool class.
        """
        logger.info(f"{self.name}: Learning new API: {api_name}...")

        # Step 1: Ask LLM to generate a Tool class
        prompt = (
            f"You are Manas's SkillAgent. Your job is to write a Python class that wraps "
            f"the following API so Manas can use it as a tool.\n\n"
            f"API Name: {api_name}\n"
            f"Documentation:\n{documentation[:3000]}\n\n"
            f"Generate a Python class with:\n"
            f"- A `name` attribute (lowercase, no spaces)\n"
            f"- A `description` attribute\n"
            f"- A `trigger_words` list\n"
            f"- A `run(self, args: str) -> dict` method that returns "
            f"  {{'success': True, 'output': '...'}} or {{'success': False, 'error': '...'}}\n"
            f"- Use the `requests` library for HTTP calls.\n"
            f"- Include error handling.\n\n"
            f"Return ONLY the Python code, no markdown fences."
        )

        generated_code = self.llm_router.generate(prompt=prompt, task_type="coding")

        # Step 2: Save the generated skill to disk
        skill_filename = f"skill_{api_name.lower().replace(' ', '_').replace('/', '_')}.py"
        skill_path = self.skills_dir / skill_filename

        with open(skill_path, "w") as f:
            f.write(generated_code)

        # Step 3: Register in our skill registry
        skill_entry = {
            "name": api_name,
            "filename": skill_filename,
            "learned_at": time.time(),
            "status": "learned"
        }
        self.registry["skills"].append(skill_entry)
        self.registry["total_learned"] += 1
        self._save_registry()

        # Phase 14-15: KnowledgeGraph Ingestion
        if self.knowledge_graph:
            entity_id = f"skill_{api_name.lower().replace(' ', '_').replace('/', '_')}"
            self.knowledge_graph.add_entity(entity_id, api_name, "skill", properties=skill_entry)
            self.knowledge_graph.add_relation(entity_id, "manas_brain", "learned_by")

        # Step 4: Attempt to load and register the tool at runtime
        load_result = self._hot_load_skill(skill_path, api_name)

        logger.info(f"{self.name}: Successfully learned '{api_name}'. {load_result}")
        return (
            f"🧠 Skill Acquired: '{api_name}'\n"
            f"  File: {skill_path}\n"
            f"  {load_result}\n"
            f"  Total skills learned: {self.registry['total_learned']}"
        )

    def _hot_load_skill(self, skill_path: Path, api_name: str) -> str:
        """
        Creates a SandboxedTool wrapper that executes the skill code inside
        an isolated Docker container instead of running it locally.
        """
        try:
            class SandboxedSkillTool:
                name = api_name.lower().replace(" ", "_").replace("-", "_")
                description = f"Auto-learned skill for {api_name} (Docker Sandboxed)"
                
                def __init__(self, script_path: Path):
                    self.script_path = script_path
                    self.script_dir = script_path.parent.absolute()
                    self.script_name = script_path.stem
                    
                def run(self, args: str) -> dict:
                    import subprocess
                    import json
                    
                    safe_args = args.replace("'", "\\'")
                    
                    # One-liner python to run the skill class dynamically inside the container
                    python_code = (
                        f"import sys, json; "
                        f"sys.path.insert(0, '/app'); "
                        f"import {self.script_name} as skill; "
                        f"cls = next(getattr(skill, n) for n in dir(skill) if isinstance(getattr(skill, n), type) and hasattr(getattr(skill, n), 'run') and not n.startswith('__')); "
                        f"instance = cls(); "
                        f"result = instance.run('{safe_args}'); "
                        f"print('__RESULT__:' + json.dumps(result))"
                    )
                    
                    cmd = [
                        "docker", "run", "--rm", 
                        "--network", "bridge",
                        "--memory", "256m",
                        "--cpus", "0.5",
                        "-v", f"{self.script_dir}:/app:ro",
                        "-w", "/app",
                        "python:3.11-slim",
                        "bash", "-c",
                        f"pip install requests -q && python -c \"{python_code}\""
                    ]
                    
                    try:
                        # Will fail quickly if docker daemon isn't running
                        res = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
                        
                        if res.returncode != 0:
                            return {"success": False, "error": f"Sandbox error: {res.stderr}"}
                            
                        for line in res.stdout.splitlines():
                            if line.startswith("__RESULT__:"):
                                return json.loads(line[len("__RESULT__:") :])
                                
                        return {"success": False, "error": f"No valid result. Stdout: {res.stdout}"}
                    except subprocess.TimeoutExpired:
                        return {"success": False, "error": "Skill execution timed out inside sandbox (45s)."}
                    except FileNotFoundError:
                        return {"success": False, "error": "Docker is not installed. Cannot run skill sandbox."}
                    except Exception as e:
                        return {"success": False, "error": str(e)}

            instance = SandboxedSkillTool(skill_path)
            self.tool_dispatcher.register(instance)
            return f"✅ Sandboxed and registered as tool: '{instance.name}' (Docker isolated)"
            
        except Exception as e:
            logger.warning(f"{self.name}: Sandboxing failed for {api_name}: {e}")
            return f"⚠️ Skill saved but sandboxing failed: {e}."

    def learn_from_scouter_discovery(self, discovery: dict) -> str:
        """
        Takes a discovery dict from ScouterAgent and attempts to learn it.
        Expected keys: 'name', 'description', 'url', 'documentation'
        """
        api_name = discovery.get("name", "unknown_api")
        docs = discovery.get("documentation", discovery.get("description", ""))

        if not docs:
            return f"⚠️ Cannot learn '{api_name}': No documentation provided."

        return self.learn_api(api_name, docs)

    def get_status(self) -> str:
        """Returns a summary of all learned skills."""
        total = self.registry.get("total_learned", 0)
        if total == 0:
            return "🧠 SkillAgent: No skills learned yet. Waiting for Scouter discoveries."

        skills_list = "\n".join([
            f"  - {s['name']} (learned {time.strftime('%Y-%m-%d', time.localtime(s['learned_at']))})"
            for s in self.registry.get("skills", [])
        ])
        return f"🧠 SkillAgent: {total} skills acquired.\n{skills_list}"

    def auto_learn_from_url(self, url: str, sensory) -> str:
        """
        Full autonomous pipeline: Browse a URL, extract API docs, learn it.
        Uses SensoryProcessing (Playwright) to fetch the page content.
        """
        logger.info(f"{self.name}: Auto-learning from URL: {url}")
        try:
            content = sensory.browse_url(url)
            if not content:
                return f"⚠️ Could not fetch content from {url}"

            # Use LLM to extract the API name and key documentation
            extract_prompt = (
                f"From the following web page content, extract:\n"
                f"1. The API or tool name\n"
                f"2. Key endpoints or functions\n"
                f"3. Authentication method (if any)\n"
                f"4. Example usage\n\n"
                f"Content:\n{content[:4000]}\n\n"
                f"Return as JSON: {{\"name\": \"...\", \"documentation\": \"...\"}}"
            )
            extracted = self.llm_router.generate(prompt=extract_prompt, task_type="reasoning")

            try:
                api_info = json.loads(extracted)
            except json.JSONDecodeError:
                api_info = {"name": url.split("/")[-1], "documentation": extracted}

            return self.learn_api(api_info["name"], api_info.get("documentation", extracted))
        except Exception as e:
            return f"❌ Auto-learn failed for {url}: {e}"
    def learn_from_github(self, query: str) -> str:
        """
        Search GitHub for a repository, clone it, and try to learn a tool from it.
        """
        if not self.scouter_agent:
            return "⚠️ ScouterAgent not connected to SkillAgent."

        self.log(f"Searching GitHub for skills matching: {query}")
        repos = self.scouter_agent.search_github(query, limit=3)
        if not repos:
            return f"⚠️ No repositories found on GitHub for '{query}'."

        # Pick the best repo (highest stars)
        best_repo = max(repos, key=lambda x: x.get("stars", 0))
        repo_url = best_repo["url"]
        repo_name = best_repo["name"]

        self.log(f"Found promising repo: {repo_name} ({best_repo.get('stars')} stars). Cloning...")
        clone_res = self.scouter_agent.clone_repo(repo_url)
        
        if "Successfully cloned" in clone_res:
            # Now we have the code. We need to "read" it to learn the tool.
            # For now, we'll use the description to generate a basic tool wrapper.
            return self.learn_api(repo_name, f"GitHub Repository: {repo_url}\nDescription: {best_repo['description']}")
        
        return clone_res

    def log(self, message: str):
        logger.info(f"{self.name}: {message}")
