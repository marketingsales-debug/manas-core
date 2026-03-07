"""
Base abstractions for the Multi-Agent architecture.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class AgentResult:
    """Standardized output from any agent execution."""
    def __init__(self, success: bool, output: Any, logs: str = "", cost: float = 0.0):
        self.success = success
        self.output = output
        self.logs = logs
        self.cost = cost
        
    def __str__(self):
        return f"[{'SUCCESS' if self.success else 'FAILED'}] {self.output}"


class BaseAgent(ABC):
    """
    Abstract Base Class for all specialized cognitive agents in Manas.
    """
    def __init__(self, name: str, llm_router=None, memory=None, working_dir: str = "."):
        self.name = name
        self.llm_router = llm_router
        self.memory = memory
        self.working_dir = working_dir
        self.status = "idle"
        self.logs = []
        
    def log(self, message: str):
        """Append to internal log and logger."""
        self.logs.append(message)
        logger.info(f"[{self.name}] {message}")
        
    def get_status(self) -> Dict[str, Any]:
        """Return the current status of the agent."""
        return {
            "name": self.name,
            "status": self.status,
            "log_tail": self.logs[-5:] if self.logs else []
        }
        
    @abstractmethod
    def run(self, task: str, **kwargs) -> AgentResult:
        """Execute the agent's primary loop for the given task."""
        pass
