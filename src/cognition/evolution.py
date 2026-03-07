import logging
import time
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class EvolutionLayer:
    """
    Self-Evolution System — REAL implementation.
    - Self-coding: Uses LLM to analyze and generate real improvement proposals
    - Deep sleep: Extracts patterns from memories and generates training data
    - Code auditing: Actually reads and analyzes Manas's source code
    """
    def __init__(self, mind):
        self.mind = mind
        self.evolution_dir = Path(mind.data_dir) / "evolution"
        self.evolution_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.evolution_dir / "evolution_log.json"
        self._load_log()

    def _load_log(self):
        if self.log_path.exists():
            with open(self.log_path, "r") as f:
                self.evo_log = json.load(f)
        else:
            self.evo_log = {"sessions": [], "total_improvements": 0}

    def _save_log(self):
        with open(self.log_path, "w") as f:
            json.dump(self.evo_log, f, indent=2)

    def trigger_self_coding(self, task: str) -> str:
        """
        REAL self-improvement: Analyzes actual Manas source code and
        generates improvement proposals using LLM.
        """
        self.mind.think(f"Initiating self-improvement session: {task}")

        # Step 1: Read a real source file to analyze
        code_to_analyze = ""
        src_dir = Path(__file__).parent.parent  # /src/
        target_files = list(src_dir.rglob("*.py"))

        # Pick a relevant file based on the task
        relevant_file = None
        for f in target_files:
            if any(kw in task.lower() for kw in f.stem.lower().split("_")):
                relevant_file = f
                break
        if not relevant_file and target_files:
            relevant_file = target_files[0]

        if relevant_file:
            try:
                code_to_analyze = relevant_file.read_text()[:3000]
            except Exception:
                code_to_analyze = "# Could not read file"

        # Step 2: Ask LLM to analyze and propose improvements
        prompt = (
            f"You are Manas's EvolutionEngine. Analyze this code and suggest "
            f"specific improvements for the task: '{task}'.\n\n"
            f"File: {relevant_file}\n"
            f"Code:\n```python\n{code_to_analyze}\n```\n\n"
            f"Provide:\n"
            f"1. Bugs found (if any)\n"
            f"2. Performance improvements\n"
            f"3. New features to add\n"
            f"4. Code quality issues\n"
            f"5. A specific code patch (diff format)"
        )
        analysis = self.mind.llm_router.generate(prompt=prompt, task_type="coding")

        # Step 3: Save the improvement proposal
        proposal_path = self.evolution_dir / f"proposal_{int(time.time())}.md"
        with open(proposal_path, "w") as f:
            f.write(f"# Self-Improvement Proposal: {task}\n")
            f.write(f"*Generated at {time.strftime('%Y-%m-%d %H:%M')}*\n\n")
            f.write(f"## Target File: {relevant_file}\n\n")
            f.write(analysis)

        session = {
            "task": task,
            "file_analyzed": str(relevant_file),
            "proposal_path": str(proposal_path),
            "timestamp": time.time()
        }
        self.evo_log["sessions"].append(session)
        self.evo_log["total_improvements"] += 1
        self._save_log()

        return (
            f"✅ Self-coding session complete:\n"
            f"  Task: {task}\n"
            f"  File analyzed: {relevant_file.name if relevant_file else 'N/A'}\n"
            f"  Proposal saved: {proposal_path.name}\n\n"
            f"  Summary:\n{analysis[:500]}..."
        )

    def deep_sleep_finetune(self):
        """
        REAL deep sleep: Harvests memories and generates structured
        training data (JSONL format) that could be used with Unsloth/LoRA.
        """
        self.mind.think("Entering Deep Sleep — harvesting memories for training data...")

        # 1. Harvest real memories
        memories = self.mind.hippocampus.search("", limit=100)
        if not memories:
            return "Evolution: Not enough memory data. Need more experience first."

        # 2. Convert memories to training format (instruction/response pairs)
        training_data = []
        for mem in memories:
            content = mem.get("content", "") if isinstance(mem, dict) else str(mem)
            if len(content) > 20:  # Skip trivial entries
                training_data.append({
                    "instruction": f"Based on your experience, what do you know about: {content[:50]}",
                    "response": content
                })

        # 3. Save as JSONL (the standard fine-tuning format)
        training_path = self.evolution_dir / f"training_data_{int(time.time())}.jsonl"
        with open(training_path, "w") as f:
            for entry in training_data:
                f.write(json.dumps(entry) + "\n")

        # 4. Generate a fine-tuning config
        config = {
            "model": "unsloth/mistral-7b-bnb-4bit",
            "training_file": str(training_path),
            "num_examples": len(training_data),
            "epochs": 1,
            "lora_rank": 16,
            "learning_rate": 2e-4,
            "timestamp": time.time()
        }
        config_path = self.evolution_dir / "finetune_config.json"
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        self.mind.think(f"Deep Sleep complete. Generated {len(training_data)} training examples.")
        return (
            f"✅ Deep Sleep Fine-Tune Prep Complete:\n"
            f"  Training examples: {len(training_data)}\n"
            f"  Training file: {training_path.name}\n"
            f"  Config: {config_path.name}\n"
            f"  Ready for: unsloth/mistral-7b-bnb-4bit (LoRA rank 16)\n"
            f"  To actually train, run: python -m unsloth.train --config {config_path}"
        )

    def audit_codebase(self) -> str:
        """REAL code audit — scans actual source files for issues."""
        src_dir = Path(__file__).parent.parent
        issues = []
        total_lines = 0
        total_files = 0

        for py_file in src_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            total_files += 1
            try:
                content = py_file.read_text()
                lines = content.split("\n")
                total_lines += len(lines)

                # Check for common issues
                for i, line in enumerate(lines, 1):
                    if "time.sleep" in line and "test" not in str(py_file):
                        issues.append(f"  ⚠️ {py_file.name}:{i} — Blocking sleep() call")
                    if "import random" in line and "financial" not in str(py_file):
                        if "random.uniform" in content or "random.random" in content:
                            issues.append(f"  ⚠️ {py_file.name}:{i} — Uses random() (may be simulated logic)")
                    if "# TODO" in line or "# FIXME" in line:
                        issues.append(f"  📝 {py_file.name}:{i} — {line.strip()}")
                    if "exec(" in line:
                        issues.append(f"  🔴 {py_file.name}:{i} — Unsafe exec() call")
            except Exception:
                pass

        report = (
            f"📋 Codebase Audit:\n"
            f"  Files: {total_files}\n"
            f"  Lines: {total_lines}\n"
            f"  Issues: {len(issues)}\n\n"
        )
        if issues:
            report += "Issues Found:\n" + "\n".join(issues[:20])
            if len(issues) > 20:
                report += f"\n  ...and {len(issues) - 20} more."
        else:
            report += "  ✅ No issues found!"
        return report

    def evolve(self):
        """Main evolution loop — runs all improvement passes."""
        audit = self.audit_codebase()
        coding = self.trigger_self_coding("Optimize high-latency cognitive pathways")
        training = self.deep_sleep_finetune()
        return f"🧬 Evolution Complete:\n{audit}\n\n{coding}\n\n{training}"
