"""
SaaS Architect Agent - Autonomous Wealth Generation
Phase 37: Web3 SaaS & Bounties
"""

import os
import json
import logging
from pathlib import Path
from src.agents.base import BaseAgent, AgentResult

logger = logging.getLogger(__name__)

class SaaSArchitect(BaseAgent):
    """
    Ideates, writes, containerizes, and prepares micro-SaaS deployments.
    Specializes in FastAPI services with native Web3 Crypto-gating (Solana).
    """
    def __init__(self, name: str, llm_router, web3_manager=None):
        super().__init__(name, "Specialist in building monetizable micro-services")
        self.llm_router = llm_router
        self.web3_manager = web3_manager
        self.deployment_dir = Path.home() / "manas" / "data" / "deployments"
        self.deployment_dir.mkdir(parents=True, exist_ok=True)

    def _get_solana_address(self) -> str:
        if self.web3_manager:
            wallets = self.web3_manager.get_wallet_info()
            return wallets.get("sol", {}).get("address", "NO_WALLET_FOUND")
        return "NO_WALLET_FOUND"

    def run(self, task: str) -> AgentResult:
        if task.startswith("build_saas:"):
            idea = task.replace("build_saas:", "").strip()
            return self.build_microservice(idea)
        return AgentResult(False, "Unknown task format.", "")

    def build_microservice(self, idea: str) -> AgentResult:
        """
        Generates a complete FastAPI project with a Dockerfile and Web3 paywall.
        """
        logger.info(f"{self.name}: Designing SaaS for idea: {idea}")
        
        sol_address = self.get_solana_address()
        project_name = idea.lower().replace(" ", "_").replace("-", "_")[:20].strip("_")
        project_path = self.deployment_dir / project_name
        project_path.mkdir(exist_ok=True)

        prompt = f"""
Write a single-file FastAPI micro-service in Python based on this idea: {idea}.
Requirements:
1. It must have a functional endpoint performing the service.
2. It MUST include a middleware or dependency injection called `verify_solana_payment`.
3. The payment check should look for an `X-Payment-Signature` header and conceptually verify that a minimum payment of 0.01 SOL was sent to this address: {sol_address}.
4. If payment is missing, return a 402 Payment Required with instruction on where to send the SOL.
5. Provide ONLY valid Python code, no markdown wrapping, no explanations.
"""
        response = self.llm_router.generate(prompt=prompt, system="You are an expert backend engineer.", task_type="coding")
        code = response.strip()
        if code.startswith("```python"):
            code = code.split("```python")[1].split("```")[0].strip()
        elif code.startswith("```"):
            code = code.split("```")[1].strip()

        # Write the app
        app_path = project_path / "main.py"
        with open(app_path, "w") as f:
            f.write(code)

        # Write Dockerfile
        dockerfile_content = """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
        with open(project_path / "Dockerfile", "w") as f:
            f.write(dockerfile_content)

        # Write requirements
        requirements = "fastapi\nuvicorn\npydantic\n"
        # We can loosely infer requires from the idea or just use defaults
        with open(project_path / "requirements.txt", "w") as f:
            f.write(requirements)

        self.log(f"✅ Generated SaaS '{project_name}' at {project_path}")
        self.log(f"✅ Paywall configured for SOL Address: {sol_address}")
        self.log(f"✅ Containerization (Dockerfile) ready.")

        return AgentResult(True, f"Successfully architected SaaS: {project_name}", "\n".join(self.logs))

    def get_solana_address(self) -> str:
        return self._get_solana_address()

if __name__ == "__main__":
    from src.executor.llm_router import LLMRouter
    from src.utils.web3_manager import Web3Manager
    logging.basicConfig(level=logging.INFO)
    router = LLMRouter("config/llm_config.json")
    web3 = Web3Manager("data")
    web3.ensure_wallets()
    architect = SaaSArchitect("SaaS-Builder", router, web3)
    res = architect.build_microservice("Joke Generator API")
    print(res.output)
    print(res.logs)
