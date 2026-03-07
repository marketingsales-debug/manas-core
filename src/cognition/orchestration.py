import logging
import json
import time
from typing import TypedDict, List
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    logger.warning("LangGraph not available. OrchestrationLayer will run in degraded mode.")

class MissionState(TypedDict):
    """The state of a long-running cognitive mission."""
    goal: str
    steps: List[str]
    findings: List[str]
    status: str # "active", "completed", "failed"
    current_agent: str

class OrchestrationLayer:
    """
    Cognitive Orchestration using LangGraph.
    Allows Manas to plan and execute multi-step missions.
    """
    def __init__(self, mind):
        self.mind = mind
        self.missions_dir = Path(mind.data_dir) / "missions"
        self.missions_dir.mkdir(parents=True, exist_ok=True)

    def create_mission_graph(self):
        """Builds the LangGraph for mission orchestration."""
        if not LANGGRAPH_AVAILABLE:
            return None
        
        workflow = StateGraph(MissionState)

        # Define nodes
        workflow.add_node("planner", self._plan_step)
        workflow.add_node("executor", self._execute_step)
        workflow.add_node("validator", self._validate_step)

        # Define edges
        workflow.set_entry_point("planner")
        workflow.add_edge("planner", "executor")
        workflow.add_edge("executor", "validator")
        
        # Conditional edge: continue or finish
        workflow.add_conditional_edges(
            "validator",
            self._should_continue,
            {
                "continue": "planner",
                "finish": END
            }
        )

        return workflow.compile()

    def _plan_step(self, state: MissionState) -> MissionState:
        logger.info(f"Orchestration: Planning next step for goal: {state['goal']}")
        prompt = f"Goal: {state['goal']}\nSteps taken: {state['steps']}\nFindings: {state['findings']}\nPlan the single next tactical step to achieve this goal."
        next_step = self.mind.llm_router.generate(prompt=prompt, task_type="reasoning")
        state['steps'].append(next_step)
        state['status'] = "active"
        return state

    def _execute_step(self, state: MissionState) -> MissionState:
        last_step = state['steps'][-1]
        logger.info(f"Orchestration: Executing step: {last_step}")
        # Try to dispatch a tool based on the step description
        result = self.mind.tools.dispatch(last_step, context={"mind": self.mind})
        if result and result.get("success"):
            state['findings'].append(result.get("output", "Success"))
        else:
            state['findings'].append(f"Attempt failed: {last_step}")
        return state

    def _validate_step(self, state: MissionState) -> MissionState:
        logger.info("Orchestration: Validating mission progress...")
        prompt = f"Goal: {state['goal']}\nFindings so far: {state['findings']}\nIs the goal achieved? Reply with 'YES' or 'NO' followed by a brief reason."
        validation = self.mind.llm_router.generate(prompt=prompt, task_type="reasoning")
        if "YES" in validation.upper():
            state['status'] = "completed"
        return state

    def _should_continue(self, state: MissionState) -> str:
        if state['status'] == "completed" or len(state['steps']) > 10:
            return "finish"
        return "continue"

    def run_mission(self, goal: str):
        """Starts a new mission."""
        if not LANGGRAPH_AVAILABLE:
            self.mind.think(f"LangGraph is unavailable. Running mission '{goal}' in Linear Simulation mode.")
            # Linear fallback
            state = {
                "goal": goal,
                "steps": [],
                "findings": [],
                "status": "active",
                "current_agent": "orchestrator"
            }
            for _ in range(3): # Simple 3-step loop
                state = self._plan_step(state)
                state = self._execute_step(state)
                state = self._validate_step(state)
                if state['status'] == "completed":
                    break
            return state

        graph = self.create_mission_graph()
        initial_state = {
            "goal": goal,
            "steps": [],
            "findings": [],
            "status": "active",
            "current_agent": "orchestrator"
        }
        self.mind.think(f"Starting mission: {goal}")
        final_state = graph.invoke(initial_state)
        
        # Save mission results
        filename = f"mission_{int(time.time())}.json"
        with open(self.missions_dir / filename, "w") as f:
            json.dump(final_state, f, indent=2)
            
        return final_state
