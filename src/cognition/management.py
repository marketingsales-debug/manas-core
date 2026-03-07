import logging

logger = logging.getLogger(__name__)

try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    # CrewAI currently has compatibility issues with Python 3.14 (requires tiktoken + Rust)
    # We run in degraded mode without warning the user every time.
    logger.debug("CrewAI not available. ManagementLayer running in degraded mode.")

class ManagementLayer:
    """
    Multi-agent management using CrewAI.
    Allows Manas to coordinate a team of specialized agents.
    """
    def __init__(self, mind):
        self.mind = mind

    def create_team(self, objective: str) -> str:
        """
        Creates a temporary 'Crew' to solve a complex objective.
        """
        if not CREWAI_AVAILABLE:
            self.mind.think(f"CrewAI is currently unavailable. I will attempt to solve '{objective}' using a single-agent focus instead.")
            # Fallback: Forward to researcher directly
            res = self.mind.orchestrator.active_agents["Researcher"].run(objective)
            return f"Degraded Mode Analysis: {res.output}"

        self.mind.think(f"Assembling a specialized crew for: {objective}")

        # 1. Define Agents (mapped to Manas's existing capabilities)
        researcher = Agent(
            role='Senior Researcher',
            goal='Find and summarize the most relevant information for the objective',
            backstory='Expert at digging through documentation and finding cutting-edge tools.',
            verbose=True,
            allow_delegation=False
        )

        analyst = Agent(
            role='Systems Analyst',
            goal='Analyze findings and propose a technical solution',
            backstory='Specializes in software architecture and cognitive AI systems.',
            verbose=True,
            allow_delegation=False
        )

        coder = Agent(
            role='Senior Developer',
            goal='Implement the proposed solution autonomously',
            backstory='Master of Python and autonomous coding frameworks.',
            verbose=True,
            allow_delegation=True
        )

        # 2. Define Tasks
        task1 = Task(description=f"Research everything related to: {objective}", agent=researcher)
        task2 = Task(description="Analyze the research and create a detailed implementation plan.", agent=analyst)
        task3 = Task(description="Execute the implementation plan autonomously.", agent=coder)

        # 3. Form the Crew
        crew = Crew(
            agents=[researcher, analyst, coder],
            tasks=[task1, task2, task3],
            process=Process.sequential,
            verbose=2
        )

        # 4. Kickoff
        result = crew.kickoff()
        return result
