import logging
import json
from typing import Dict
from .base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """
    High-level agent that breaks complex goals into sub-tasks and delegates
    them to specialized sub-agents. Acts as the manager.
    """
    def __init__(self, name: str = "Orchestrator", llm_router=None, memory=None):
        super().__init__(name, llm_router, memory)
        self.active_agents: Dict[str, BaseAgent] = {}
        
    def register_agents(self, agents_dict: Dict[str, BaseAgent]):
        """Register the sub-agents (coder, researcher, watcher, etc.)"""
        self.active_agents = agents_dict

    def run(self, task: str, **kwargs) -> AgentResult:
        self.status = "planning"
        self.log(f"Received high-level goal: {task}")
        
        if not self.llm_router:
            return AgentResult(False, "No LLM Router connected for reasoning.")
            
        agents_info = "\n".join(f"- {name}" for name in self.active_agents.keys())
        if not agents_info:
            return AgentResult(False, "No sub-agents registered to delegate to.")

        # 1. Break down the task
        prompt = f"""
You are the Orchestrator Agent. Break down the high-level goal into step-by-step sub-tasks.
You MUST output ONLY valid JSON.

Sub-agents available:
{agents_info}

Goal:
{task}

Format:
{{
  "steps": [
    {{"agent": "Researcher", "instruction": "Search for X and summarize"}},
    {{"agent": "Coder", "instruction": "Write a script based on X"}}
  ]
}}
"""
        plan_text = self.llm_router.generate(prompt, task_type="reasoning", temperature=0.1)
        
        try:
            # Simple JSON extraction
            if "{" in plan_text and "}" in plan_text:
                json_str = plan_text[plan_text.find("{"):plan_text.rfind("}")+1]
                plan = json.loads(json_str)
            else:
                plan = {"steps": []}
        except Exception as e:
            self.log(f"Failed to parse plan: {e}")
            return AgentResult(False, f"Plan parsing failed: {e}\nRaw output: {plan_text}")
            
        steps = plan.get("steps", [])
        if not steps:
            return AgentResult(False, "No actionable steps generated.")
            
        self.status = "executing"
        self.log(f"Generated {len(steps)} sequential steps.")
        
        # 2. Execute steps sequentially, passing context along
        context = []
        for i, step in enumerate(steps):
            agent_name = step.get("agent")
            instruction = step.get("instruction")
            
            # Case-insensitive match for agent name
            target_agent = None
            for name, ag in self.active_agents.items():
                if name.lower() == agent_name.lower():
                    target_agent = ag
                    break
                    
            if not target_agent:
                self.log(f"Step {i+1}: Cannot execute, sub-agent '{agent_name}' not found.")
                continue
                
            self.log(f"Step {i+1}: Delegating to {target_agent.name} -> {instruction}")
            
            # Pass context of previous steps to current agent
            context_str = "\n".join(context[-3:])  # Keep last 3 steps of context
            full_instruction = f"Context:\n{context_str}\n\nYour task:\n{instruction}" if context else instruction
            
            result = target_agent.run(full_instruction)
            
            summary = f"Step {i+1} ({target_agent.name}) Result: {'Success' if result.success else 'Failed'} - {str(result.output)[:200]}..."
            self.log(summary)
            context.append(summary)
            
            if not result.success:
                self.log(f"Aborting plan at step {i+1} due to failure.")
                return AgentResult(False, f"Failed at step {i+1}", logs="\n".join(self.logs))
                
        self.status = "idle"
        self.log("All steps completed successfully.")
        return AgentResult(True, context, logs="\n".join(self.logs))
