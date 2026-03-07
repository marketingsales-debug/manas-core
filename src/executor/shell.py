"""
Shell Executor - Runs commands on the system.

All commands pass through the amygdala (threat detection) first.
The AI can learn from command outcomes and build procedural memory.
"""

import subprocess
import time
from typing import Optional


class ShellExecutor:
    """
    Executes shell commands with safety checks.

    Every command goes through threat assessment before execution.
    Outcomes are recorded for learning.
    """

    def __init__(self):
        self.history: list[dict] = []
        self.blocked_commands: list[dict] = []
        self.max_timeout: int = 30  # max seconds per command

    def execute(
        self,
        command: str,
        timeout: Optional[int] = None,
        threat_assessment: Optional[dict] = None,
    ) -> dict:
        """
        Execute a shell command.

        Args:
            command: the shell command to run
            timeout: max seconds (default 30)
            threat_assessment: from amygdala, can block execution

        Returns:
            dict with stdout, stderr, exit_code, duration, blocked status
        """
        timeout = timeout or self.max_timeout

        # Check if amygdala says to block
        if threat_assessment and threat_assessment.get("should_block", False):
            result = {
                "command": command,
                "stdout": "",
                "stderr": f"BLOCKED by fear system: {threat_assessment.get('reasons', [])}",
                "exit_code": -1,
                "duration": 0.0,
                "blocked": True,
                "threat_level": threat_assessment.get("threat_level", 0),
                "timestamp": time.time(),
            }
            self.blocked_commands.append(result)
            self.history.append(result)
            return result

        # Execute the command
        start = time.time()
        try:
            proc = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = time.time() - start

            result = {
                "command": command,
                "stdout": proc.stdout[:5000],  # limit output size
                "stderr": proc.stderr[:2000],
                "exit_code": proc.returncode,
                "duration": duration,
                "blocked": False,
                "timestamp": time.time(),
            }

        except subprocess.TimeoutExpired:
            result = {
                "command": command,
                "stdout": "",
                "stderr": f"Command timed out after {timeout}s",
                "exit_code": -2,
                "duration": timeout,
                "blocked": False,
                "timestamp": time.time(),
            }
        except Exception as e:
            result = {
                "command": command,
                "stdout": "",
                "stderr": str(e),
                "exit_code": -3,
                "duration": time.time() - start,
                "blocked": False,
                "timestamp": time.time(),
            }

        self.history.append(result)
        # Keep only last 100 commands
        if len(self.history) > 100:
            self.history = self.history[-100:]

        return result

    def get_history(self, limit: int = 10) -> list[dict]:
        return self.history[-limit:]

    def get_success_rate(self) -> float:
        """What fraction of commands succeeded?"""
        if not self.history:
            return 0.0
        successes = sum(1 for h in self.history if h["exit_code"] == 0)
        return successes / len(self.history)
