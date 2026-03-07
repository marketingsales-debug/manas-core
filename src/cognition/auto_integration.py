"""
AutoIntegrationEngine — The Self-Evolving Core.

This is Manas's ultimate autonomy feature. It:
1. Periodically scouts GitHub trending repos & open-source communities
2. Evaluates each discovery: "Is this useful for MY capabilities?"
3. Reads the documentation and source code
4. Generates a Python integration (tool/agent wrapper)
5. Hot-loads and registers it into the live system
6. Logs the integration and updates its capability catalog

This means Manas grows smarter every day WITHOUT human intervention.
"""

import logging
import json
import time
import threading
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)


class AutoIntegrationEngine:
    """
    Manas's autonomous self-improvement pipeline.
    Continuously discovers and absorbs useful open-source capabilities.
    """

    # Sources to scout for new capabilities
    SCOUT_SOURCES = [
        "https://github.com/trending?since=daily",
        "https://github.com/topics/ai-agents",
        "https://github.com/topics/llm-tools",
        "https://github.com/topics/autonomous-agents",
        "https://altern.ai/?utm_source=awesomeaitools",
    ]

    # Categories of capabilities Manas values
    CAPABILITY_PRIORITIES = [
        "security", "automation", "data analysis", "web scraping",
        "natural language processing", "computer vision", "trading",
        "communication", "code generation", "knowledge management",
        "monitoring", "self-improvement", "API integration"
    ]

    def __init__(self, mind):
        self.mind = mind
        self.data_dir = Path(mind.data_dir)
        self.integration_log_path = self.data_dir / "auto_integrations.json"
        self.evaluation_cache_path = self.data_dir / "evaluated_projects.json"
        self._load_state()
        self._running = False
        self._thread = None

    def _load_state(self):
        if self.integration_log_path.exists():
            with open(self.integration_log_path, "r") as f:
                self.integration_log = json.load(f)
        else:
            self.integration_log = {
                "integrations": [],
                "total_absorbed": 0,
                "total_evaluated": 0,
                "total_rejected": 0,
                "last_scan": None
            }

        if self.evaluation_cache_path.exists():
            with open(self.evaluation_cache_path, "r") as f:
                self.eval_cache = json.load(f)
        else:
            self.eval_cache = {}  # name -> {decision, reason, timestamp}

    def _save_state(self):
        with open(self.integration_log_path, "w") as f:
            json.dump(self.integration_log, f, indent=2)
        with open(self.evaluation_cache_path, "w") as f:
            json.dump(self.eval_cache, f, indent=2)

    # ─── Stage 1: DISCOVER ───

    def _discover(self, source_url: str = None) -> List[Dict]:
        """
        Uses the ScouterAgent to browse a source and find projects.
        Returns a list of discovered project dicts.
        """
        url = source_url or self.SCOUT_SOURCES[0]
        logger.info(f"AutoIntegration: Scouting {url}...")

        try:
            # Use Scouter's existing capability
            self.mind.scouter.scout(url)
            # Pull from the catalog
            tools = self.mind.scouter.catalog.get("tools", [])
            return tools
        except Exception as e:
            logger.warning(f"AutoIntegration: Discovery failed: {e}")
            # Fallback: use LLM to suggest projects
            prompt = (
                f"Suggest 5 open-source GitHub projects that would be useful for "
                f"an autonomous AI agent with these capabilities: "
                f"{', '.join(self.CAPABILITY_PRIORITIES[:5])}.\n\n"
                f"Return as a JSON list with keys: name, description, url, category."
            )
            response = self.mind.llm_router.generate(prompt=prompt, task_type="reasoning")
            try:
                clean = response.strip()
                if "```" in clean:
                    clean = clean.split("```")[1].split("```")[0].strip()
                    if clean.startswith("json"):
                        clean = clean[4:].strip()
                return json.loads(clean)
            except (json.JSONDecodeError, IndexError):
                return []

    # ─── Stage 2: EVALUATE ───

    def _evaluate(self, project: Dict) -> Dict:
        """
        Uses LLM reasoning to decide if a project is worth integrating.
        Returns: {decision: 'absorb'|'skip', reason: str, score: float}
        """
        name = project.get("name", "unknown")

        # Skip if already evaluated
        if name in self.eval_cache:
            return self.eval_cache[name]

        description = project.get("description", "")
        url = project.get("url", "")

        # Get current capabilities for comparison
        current_skills = []
        if hasattr(self.mind, 'skill_agent'):
            current_skills = [s["name"] for s in self.mind.skill_agent.registry.get("skills", [])]

        prompt = (
            f"You are Manas's self-improvement evaluator. Decide if this project "
            f"should be integrated into Manas's brain.\n\n"
            f"Project: {name}\n"
            f"Description: {description}\n"
            f"URL: {url}\n\n"
            f"Manas's current capabilities: {', '.join(self.CAPABILITY_PRIORITIES)}\n"
            f"Already integrated skills: {', '.join(current_skills) if current_skills else 'None yet'}\n\n"
            f"Evaluate:\n"
            f"1. Usefulness score (0-10): How much would this improve Manas?\n"
            f"2. Novelty: Does Manas already have this capability?\n"
            f"3. Integration difficulty (1-10): How hard to integrate?\n"
            f"4. Decision: ABSORB or SKIP\n"
            f"5. Reason: One sentence why.\n\n"
            f"Return as JSON: {{\"score\": N, \"decision\": \"absorb/skip\", \"reason\": \"...\"}}"
        )

        response = self.mind.llm_router.generate(prompt=prompt, task_type="reasoning")

        try:
            clean = response.strip()
            if "```" in clean:
                clean = clean.split("```")[1].split("```")[0].strip()
                if clean.startswith("json"):
                    clean = clean[4:].strip()
            evaluation = json.loads(clean)
        except (json.JSONDecodeError, IndexError):
            evaluation = {"score": 5, "decision": "skip", "reason": "Could not evaluate properly."}

        evaluation["timestamp"] = time.time()
        self.eval_cache[name] = evaluation
        self.integration_log["total_evaluated"] += 1
        self._save_state()

        return evaluation

    # ─── Stage 3: ABSORB ───

    def _absorb(self, project: Dict) -> str:
        """
        Uses the SkillAgent to learn and integrate the project.
        This is where the magic happens — Manas writes its own code.
        """
        name = project.get("name", "unknown")
        description = project.get("description", "")
        url = project.get("url", "")

        logger.info(f"AutoIntegration: Absorbing '{name}'...")

        # Use SkillAgent to learn
        doc = f"Name: {name}\nDescription: {description}\nURL: {url}"
        result = self.mind.skill_agent.learn_api(name, doc)

        # Log the integration
        entry = {
            "name": name,
            "url": url,
            "absorbed_at": time.time(),
            "result": result[:200]
        }
        self.integration_log["integrations"].append(entry)
        self.integration_log["total_absorbed"] += 1
        self._save_state()

        # Neurochemical reward for self-improvement
        self.mind.neurochem.release("dopamine", 0.4)
        self.mind.think(f"I just taught myself '{name}'. My capabilities have expanded.")

        return result

    # ─── Full Pipeline ───

    def run_scan_cycle(self, source_url: str = None) -> str:
        """
        Runs one full cycle: Discover → Evaluate → Absorb.
        This is the core self-improvement loop.
        """
        logger.info("AutoIntegration: Starting scan cycle...")
        self.integration_log["last_scan"] = time.time()

        # Step 1: Discover
        discoveries = self._discover(source_url)
        if not discoveries:
            return "🔍 Scan complete: No new projects discovered."

        absorbed = []
        skipped = []

        for project in discoveries:
            name = project.get("name", "unknown")

            # Step 2: Evaluate
            evaluation = self._evaluate(project)
            decision = evaluation.get("decision", "skip").lower()
            score = evaluation.get("score", 0)
            reason = evaluation.get("reason", "No reason given.")

            if decision == "absorb" and score >= 6:
                # Step 3: Absorb
                result = self._absorb(project)
                absorbed.append(f"  ✅ {name} (score: {score}) — {reason}")
            else:
                skipped.append(f"  ⏭️ {name} (score: {score}) — {reason}")
                self.integration_log["total_rejected"] += 1

        self._save_state()

        report = "🧬 Auto-Integration Scan Complete:\n"
        report += f"  Discovered: {len(discoveries)} projects\n"
        report += f"  Absorbed: {len(absorbed)}\n"
        report += f"  Skipped: {len(skipped)}\n\n"

        if absorbed:
            report += "Absorbed:\n" + "\n".join(absorbed) + "\n\n"
        if skipped:
            report += "Skipped:\n" + "\n".join(skipped[:5])  # Show max 5
            if len(skipped) > 5:
                report += f"\n  ...and {len(skipped) - 5} more."

        return report

    # ─── Autonomous Background Loop ───

    def start_auto_scan(self, interval_hours: float = 24.0):
        """Starts a background thread that scans periodically."""
        if self._running:
            return "⚠️ Auto-scan is already running."

        self._running = True

        def _loop():
            import random
            while self._running:
                try:
                    source = random.choice(self.SCOUT_SOURCES)
                    result = self.run_scan_cycle(source)
                    logger.info(f"AutoIntegration background scan: {result[:200]}")
                except Exception as e:
                    logger.warning(f"AutoIntegration background error: {e}")

                # Sleep for the interval
                time.sleep(interval_hours * 3600)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        return f"🔄 Auto-scan started. Scanning every {interval_hours}h."

    def stop_auto_scan(self):
        """Stops the background scanning."""
        self._running = False
        return "⏹️ Auto-scan stopped."

    # ─── Status ───

    def get_status(self) -> str:
        last_scan = self.integration_log.get("last_scan")
        last_scan_str = (
            time.strftime("%Y-%m-%d %H:%M", time.localtime(last_scan))
            if last_scan else "Never"
        )

        return (
            f"🧬 Auto-Integration Engine:\n"
            f"  Auto-scan: {'🟢 Running' if self._running else '🔴 Stopped'}\n"
            f"  Last scan: {last_scan_str}\n"
            f"  Total evaluated: {self.integration_log['total_evaluated']}\n"
            f"  Total absorbed: {self.integration_log['total_absorbed']}\n"
            f"  Total rejected: {self.integration_log['total_rejected']}\n"
            f"  Scout sources: {len(self.SCOUT_SOURCES)}\n"
            f"  Priority capabilities: {', '.join(self.CAPABILITY_PRIORITIES[:5])}..."
        )
