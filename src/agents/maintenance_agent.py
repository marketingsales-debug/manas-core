"""
MaintenanceAgent - The self-healing immune system of Manas.
"""

import logging
import subprocess
import os
import sys
import time
from typing import List, Dict, Any
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class MaintenanceAgent(BaseAgent):
    """
    The MaintenanceAgent acts as Manas's autonomous immune system.
    It:
    1. Runs system health checks (pytest).
    2. Analyzes logs for frequent errors.
    3. Coordinates with the Coder agent to fix identified bugs.
    4. Monitors environment health (missing dependencies).
    """

    def __init__(self, name: str, llm_router, memory, working_dir: str = "."):
        super().__init__(name, llm_router, memory, working_dir)
        self.health_history: List[Dict[str, Any]] = []
        self.resolved_issues: List[str] = []

    def run(self, task: str, **kwargs) -> AgentResult:
        """
        Main execution loop for maintenance tasks.
        Supported tasks: "check_health", "fix_bugs", "analyze_logs".
        """
        self.log(f"Starting maintenance task: {task}")
        
        if task == "check_health":
            return self._check_health()
        elif task == "fix_bugs":
            return self._coordinate_bug_fix()
        elif task == "analyze_logs":
            return self._analyze_logs()
        else:
            return AgentResult(False, f"Unknown maintenance task: {task}")

    def _check_health(self) -> AgentResult:
        """Runs the test suite and returns a health report."""
        self.log("Running system health check (pytest)...")
        try:
            # Try to find pytest in the venv
            pytest_path = os.path.join(self.working_dir, ".venv", "bin", "pytest")
            if not os.path.exists(pytest_path):
                # Fallback to system pytest or python -m pytest
                pytest_path = sys.executable.replace("python", "pytest")
                if not os.path.exists(pytest_path):
                    pytest_cmd = [sys.executable, "-m", "pytest"]
                else:
                    pytest_cmd = [pytest_path]
            else:
                pytest_cmd = [pytest_path]

            result = subprocess.run(
                pytest_cmd + ["tests/"],
                capture_output=True,
                text=True,
                cwd=self.working_dir
            )
            
            success = result.returncode == 0
            output = result.stdout + result.stderr
            
            # Use data dir from memory or direct path
            data_dir = os.path.join(self.working_dir, "data")
            goals_path = os.path.join(data_dir, "goals.json")
            
            report = {
                "timestamp": os.path.getmtime(goals_path) if os.path.exists(goals_path) else time.time(),
                "status": "Healthy" if success else "Degraded",
                "failed_tests": self._parse_failed_tests(output) if not success else []
            }
            
            self.health_history.append(report)
            self.log(f"Health check complete. Status: {report['status']}")
            
            return AgentResult(success, report, output)
            
        except Exception as e:
            self.log(f"Health check failed to execute: {e}")
            return AgentResult(False, str(e))

    def _analyze_logs(self) -> AgentResult:
        """Reads the progress log to find recurring patterns of failure."""
        log_path = os.path.join(self.working_dir, "data", "progress_log.txt")
        if not os.path.exists(log_path):
            # Try checking the home dir version
            log_path = os.path.expanduser("~/manas/data/progress_log.txt")
            
        if not os.path.exists(log_path):
            return AgentResult(False, f"Progress log not found at {log_path}.")

        try:
            with open(log_path, 'r') as f:
                # Read last 100 lines
                lines = f.readlines()[-100:]
            
            log_content = "".join(lines)
            prompt = (
                f"Analyze these recent Manas system logs for recurring errors or crash patterns:\n\n"
                f"{log_content}\n\n"
                f"List the top 2 issues that require a developer's attention. If none, say 'SYSTEM STABLE'."
            )
            
            analysis = self.llm_router.generate(prompt, task_type="reasoning")
            self.log(f"Log analysis complete: {analysis[:50]}...")
            
            return AgentResult(True, analysis)
        except Exception as e:
            return AgentResult(False, str(e))

    def _coordinate_bug_fix(self) -> AgentResult:
        """Identifies a bug and asks the Coder agent to fix it."""
        # 1. Check health to find failures
        health = self._check_health()
        if health.success:
            return AgentResult(True, "System is already healthy. No fixes needed.")

        failed_tests = health.output.get("failed_tests", [])
        if not failed_tests:
            return AgentResult(False, "Test suite failed but no specific failed tests were identified.")

        # 2. Pick the first failed test and ask Coder to fix
        target_test = failed_tests[0]
        self.log(f"Coordinating fix for: {target_test}")
        
        # We need a callback to 'mind' or 'orchestrator' to trigger Coder
        # For now, we return a structured suggestion that the Orchestrator can act upon.
        fix_request = {
            "type": "bug_fix",
            "target": target_test,
            "instruction": f"Fix the issue causing {target_test} to fail. Run 'pytest {target_test}' to verify."
        }
        
        return AgentResult(True, fix_request)

    def _parse_failed_tests(self, output: str) -> List[str]:
        """Simple parser to extract failed test paths from pytest output."""
        failed = []
        for line in output.splitlines():
            if "FAILURES" in line:
                continue
            if line.startswith("FAILED "):
                failed.append(line.replace("FAILED ", "").split(" - ")[0])
        return failed
