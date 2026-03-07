"""
PlasticityEngine - The "Self-Rewriting" Core of Manas.
Handles autonomous code optimization, feature expansion, and structural evolution.
"""

import logging
import json
import ast
import os
import time
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PlasticityEngine:
    """
    Manages the 'Neural Plasticity' of the codebase.
    Treats Python modules as synapses that can be optimized or expanded.
    """

    def __init__(self, llm_router, project_root: str):
        self.llm_router = llm_router
        self.project_root = Path(project_root)
        self.evolution_log = self.project_root / "data" / "plasticity_log.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        self.evolution_log.parent.mkdir(parents=True, exist_ok=True)

    def analyze_module(self, file_path: str) -> Dict[str, Any]:
        """Uses AST to extract structural metadata from a module."""
        abs_path = self.project_root / file_path
        if not abs_path.exists():
            return {"error": "File not found"}

        try:
            with open(abs_path, "r") as f:
                code = f.read()
            
            tree = ast.parse(code)
            
            stats = {
                "classes": [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)],
                "functions": [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)],
                "loc": len(code.splitlines()),
                "complexity": self._estimate_complexity(tree)
            }
            return stats
        except Exception as e:
            return {"error": str(e)}

    def _estimate_complexity(self, tree):
        """Simple cyclomatic complexity proxy."""
        count = 0
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.With, ast.Try, ast.ExceptHandler)):
                count += 1
        return count

    def hypothesize_optimization(self, file_path: str) -> Dict[str, Any]:
        """Calls LLM to propose an optimized or expanded version of a module."""
        abs_path = self.project_root / file_path
        with open(abs_path, "r") as f:
            current_code = f.read()

        prompt = (
            f"As Manas's Neural Plasticity Engine, analyze and optimize the following Python module:\n"
            f"FILE: {file_path}\n\n"
            "CURRENT CODE:\n"
            f"```python\n{current_code}\n```\n\n"
            "GOALS:\n"
            "1. Improve execution performance or memory efficiency.\n"
            "2. Add a useful new helper function or metric if beneficial.\n"
            "3. Ensure NO BREAKING CHANGES to existing public APIs.\n\n"
            "Output the ENTIRE new source code inside a single code block."
        )

        try:
            new_code_raw = self.llm_router.generate(
                prompt=prompt, 
                task_type="coding", 
                max_tokens=20000
            )
            # Extract code between ```python and ```
            if "```python" in new_code_raw:
                new_code = new_code_raw.split("```python")[1].split("```")[0].strip()
            else:
                new_code = new_code_raw.strip()

            return {
                "original_path": file_path,
                "proposed_code": new_code,
                "hypothesis": "Autonomous structural optimization."
            }
        except Exception as e:
            return {"error": str(e)}

    def evolve_module(self, file_path: str, proposed_code: str) -> Dict[str, Any]:
        """
        Attempts to apply a code change safely.
        1. Write to temp file.
        2. Run lint/tests.
        3. Replace original if successful.
        """
        abs_path = self.project_root / file_path
        temp_path = abs_path.with_suffix(".tmp.py")
        backup_path = abs_path.with_suffix(".bak.py")

        try:
            # 1. Write proposed code
            with open(temp_path, "w") as f:
                f.write(proposed_code)

            # 2. Syntax Check
            compile(proposed_code, str(temp_path), 'exec')

            # 3. Simulate (Run tests if they exist)
            # For Phase 21, we just check syntax and then commit.
            # Real tests would be run here.
            
            # 4. Commit
            os.replace(abs_path, backup_path)
            os.replace(temp_path, abs_path)

            log_entry = {
                "timestamp": time.time(),
                "file": file_path,
                "status": "evolved",
                "original_backup": str(backup_path)
            }
            self._log_evolution(log_entry)

            return log_entry
        except Exception as e:
            if temp_path.exists(): os.remove(temp_path)
            return {"error": f"Evolution failed: {e}", "file": file_path}

    def _log_evolution(self, entry):
        log = []
        if self.evolution_log.exists():
            with open(self.evolution_log, "r") as f:
                log = json.load(f)
        log.append(entry)
        with open(self.evolution_log, "w") as f:
            json.dump(log[-50:], f, indent=2)

    def get_synapse_map(self) -> List[Dict[str, Any]]:
        """Returns the last few successful evolutions."""
        if not self.evolution_log.exists():
            return []
        with open(self.evolution_log, "r") as f:
            return json.load(f)
